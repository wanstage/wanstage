#!/usr/bin/env zsh
set -euo pipefail

# --- 基本ユーティリティ ---
ts(){ date '+%Y-%m-%d %H:%M:%S'; }
log(){ echo "[$(ts)] [pid=$$] $*" | tee -a "$LOG_FILE"; }
err(){ log "ERROR: $*"; }

# --- デフォルト値 ---
: ${SIZE:=${SIZE:-1280x720}}
: ${FPS:=${FPS:-30}}
: ${DURATION_PER_IMAGE:=${DURATION_PER_IMAGE:-3}}
: ${MAX_IMAGES:=${MAX_IMAGES:-120}}
: ${BGM_MODE:=${BGM_MODE:-mix}}

# --- 位置/ログ/状態 ---
ROOT="${HOME}/WANSTAGE"
SRC_DIR="${SRC_DIR:-$ROOT/media/inbox}"
OUT_DIR="${OUT_DIR:-$ROOT/videos/out}"
LOG_FILE="${LOG_FILE:-$ROOT/logs/auto_slideshow_worker.log}"
STATE_DIR="${STATE_DIR:-$ROOT/state}"
LAST_TS_FILE="$STATE_DIR/last_slideshow_ts"
LOCK_FILE="$STATE_DIR/build.lock"

# --- .env 読み込み（あれば） ---
if [[ -f "$ROOT/.env" ]]; then
  set -a; source "$ROOT/.env"; set +a
fi

# --- 依存チェック ---
need(){ command -v "$1" >/dev/null 2>&1 || { err "$1 not found"; exit 1; }; }
need ffmpeg; need exiftool
# fswatch が無ければポーリングにフォールバック
HAS_FSWATCH=0; command -v fswatch >/dev/null 2>&1 && HAS_FSWATCH=1

# --- 通知 ---
notify_slack(){
  local msg="$1"
  [[ -n "${SLACK_WEBHOOK:-}" ]] || return 0
  curl -sS -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"${msg//$'\n'/\\n}\"}" \
    "$SLACK_WEBHOOK" >/dev/null || true
}

post_mastodon(){
  local status="$1"
  [[ -n "${MASTODON_BASE:-}" && -n "${MASTODON_TOKEN:-}" ]] || return 0
  curl -sS -X POST "$MASTODON_BASE/api/v1/statuses" \
    -H "Authorization: Bearer ${MASTODON_TOKEN}" \
    --data-urlencode "status=$status" \
    --data "visibility=unlisted" >/dev/null || true
}

gen_caption(){
  # Gemini が無ければデフォ文
  if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "本日のスライドショーを公開しました。#wanstage"
    return 0
  fi
  # ここでは簡易なローカル生成にフォールバック（安全）
  # ※ 実際の Gemini 呼び出しは別スクリプトに任せてもOK
  echo "今日のハイライトをまとめたスライドショーです。#wanstage"
}

# --- ロック（簡易：ln -s 原子作成） ---
acquire_lock(){
  mkdir -p "$STATE_DIR"
  if ln -s "$$" "$LOCK_FILE" 2>/dev/null; then
    return 0
  else
    log "ビルド中のためスキップ（ロック取得できず）"
    return 1
  fi
}
release_lock(){
  [[ -L "$LOCK_FILE" ]] && rm -f "$LOCK_FILE" || true
}

# --- 画像選定 ---
collect_images(){
  # 更新時刻降順に並べて上限まで
  # GNU/bsd差異回避のため find + stat は使わず ls で揃える
  local list=()
  # 拡張子バリエーション対応
  local -a globs=("$SRC_DIR"/*.jpg "$SRC_DIR"/*.JPG "$SRC_DIR"/*.jpeg "$SRC_DIR"/*.JPEG "$SRC_DIR"/*.png "$SRC_DIR"/*.PNG)
  for g in $globs; do [[ -f "$g" ]] && list+=("$g"); done
  [[ ${#list[@]} -eq 0 ]] && return 1
  # 更新時刻降順
  local -a sorted
  IFS=$'\n' sorted=($(ls -t ${list:q})) ; unset IFS
  # 上限
  local n=${#sorted[@]}
  if (( n > MAX_IMAGES )); then
    sorted=(${sorted[1,MAX_IMAGES]})
  fi
  print -r -- "${sorted[@]}"
}

# --- ビルド本体 ---
build_slideshow(){
  acquire_lock || return 0
  {
    mkdir -p "$OUT_DIR" "$STATE_DIR" || true
    local -a files
    IFS=$'\n' files=($(collect_images)) || {
      err "画像選択に失敗しました（$SRC_DIR）"; return 1; }
    local count=${#files[@]}
    (( count > 0 )) || { err "画像が見つかりません（$SRC_DIR）"; return 1; }

    # 入力リストを ffmpeg の concat イメージ入力へ
    local tmplist; tmplist="$(mktemp)"
    # 1枚あたりDURATION秒でスライド（fpsで補間）
    for f in "${files[@]}"; do
      # 1枚ずつ同じ静止画をDURATION*FPSフレーム出す
      echo "file '$f'" >> "$tmplist"
      echo "duration $DURATION_PER_IMAGE" >> "$tmplist"
    done
    # concat デマルチ用に最終ファイルを重複記載（ffmpeg仕様）
    echo "file '${files[-1]}'" >> "$tmplist"

    local tsout; tsout="$(date +%Y%m%d_%H%M%S)"
    local base="$OUT_DIR/slideshow_${tsout}.mp4"

    # 画像→動画（無音）
    ffmpeg -y -f concat -safe 0 -i "$tmplist" \
      -vf "scale=${SIZE}:force_original_aspect_ratio=decrease,pad=${SIZE}:(ow-iw)/2:(oh-ih)/2,format=yuv420p,fps=${FPS}" \
      -r "$FPS" -movflags +faststart \
      -an -c:v libx264 -pix_fmt yuv420p "$base" >/dev/null 2>&1

    rm -f "$tmplist"

    # BGM ミックス（任意）
    if [[ -n "${BGM_PATH:-}" && -f "$BGM_PATH" ]]; then
      local out_bgm="${base%.mp4}_bgm.mp4"
      case "$BGM_MODE" in
        none)
          cp "$base" "$out_bgm"
          ;;
        mix)
          ffmpeg -y -i "$base" -stream_loop -1 -i "$BGM_PATH" -shortest \
            -filter_complex "[1:a]volume=0.28[a1];[0:a][a1]amix=inputs=2:duration=shortest:dropout_transition=2[aout]" \
            -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k "$out_bgm" >/dev/null 2>&1
          ;;
        duck)
          # base に音声は基本無いが、将来音声ありでも対応
          ffmpeg -y -i "$base" -i "$BGM_PATH" \
            -filter_complex "[1:a]volume=0.4[a_bgm];[a_bgm][0:a]sidechaincompress=threshold=0.015:ratio=8:attack=5:release=300[a_duck];[0:a][a_duck]amix=inputs=2:duration=shortest:dropout_transition=2[a_mix]" \
            -map 0:v -map "[a_mix]" -c:v copy -c:a aac -b:a 192k "$out_bgm" >/dev/null 2>&1
          ;;
        duck_loudnorm)
          ffmpeg -y -i "$base" -stream_loop -1 -i "$BGM_PATH" -shortest \
            -filter_complex "[1:a]volume=0.28[a1];[0:a][a1]amix=inputs=2:duration=shortest:dropout_transition=2, loudnorm=I=-16:TP=-1.5:LRA=11[aout]" \
            -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k "$out_bgm" >/dev/null 2>&1
          ;;
        *)
          cp "$base" "$out_bgm"
          ;;
      esac
      base="$out_bgm"
    fi

    # 成功ログ
    log "✅ スライドショー生成: $base"
    date +%s > "$LAST_TS_FILE"

    # 通知
    local caption; caption="$(gen_caption)"
    notify_slack "AutoSlideshow 完了:\n$base"
    post_mastodon "$caption"

  } always {
    release_lock
  }
}

# --- 変更検知: 初回 or 差分があればビルド ---
ensure_change_then_build(){
  if [[ ! -f "$LAST_TS_FILE" ]]; then
    log "初回ビルドを実行します（last_tsなし）"
    build_slideshow; return 0
  fi
  local last_ts; last_ts=$(<"$LAST_TS_FILE")
  # 最新画像の mtime
  local newest=0
  local -a globs=("$SRC_DIR"/*.jpg "$SRC_DIR"/*.JPG "$SRC_DIR"/*.jpeg "$SRC_DIR"/*.JPEG "$SRC_DIR"/*.png "$SRC_DIR"/*.PNG)
  local found=0
  for g in $globs; do
    for f in $g; do
      [[ -f "$f" ]] || continue
      found=1
      local m; m=$(stat -f '%m' "$f" 2>/dev/null || stat -t '%s' -f '%m' "$f" 2>/dev/null || echo 0)
      (( m > newest )) && newest=$m
    done
  done
  if (( ! found )); then
    err "画像が見つかりません（$SRC_DIR）"; return 0
  fi
  if (( newest <= last_ts )); then
    log "変化なし: スキップ（last_ts=$last_ts / newest=$newest)"
  else
    build_slideshow
  fi
}

# --- 起動ログ ---
log "AutoSlideshow ワーカー起動"
log "SRC_DIR=$SRC_DIR / OUT_DIR=$OUT_DIR / SIZE=$SIZE / DURATION=$DURATION_PER_IMAGE / FPS=$FPS / MAX_IMAGES=$MAX_IMAGES"
log "BGM_PATH=${BGM_PATH:-（未設定）}"
log "Slack通知=$([[ -n ${SLACK_WEBHOOK:-} ]] && echo ON || echo OFF)"
log "Gemini=$([[ -n ${GEMINI_API_KEY:-} ]] && echo ON || echo OFF)"
log "Mastodon=$([[ -n ${MASTODON_BASE:-} && -n ${MASTODON_TOKEN:-} ]] && echo ON\ \(${MASTODON_BASE}\) || echo OFF)"

# 画像があれば即チェック
if ls "$SRC_DIR"/*.(jpg|JPG|jpeg|JPEG|png|PNG) >/dev/null 2>&1; then
  ensure_change_then_build || true
fi

# 監視ループ
if (( HAS_FSWATCH )); then
  log "監視開始 (fswatch): $SRC_DIR"
  fswatch -0 -r -e ".*" -i "\\.jpe?g$" -i "\\.JPE?G$" -i "\\.png$" -i "\\.PNG$" "$SRC_DIR" | \
  while IFS= read -r -d '' _; do
    log "変更検知: ビルドを開始します"
    ensure_change_then_build || true
  done
else
  log "監視開始 (polling every 15s): $SRC_DIR"
  while true; do ensure_change_then_build || true; sleep 15; done
fi
