#!/usr/bin/env zsh
set -euo pipefail

# === WANSTAGE VSCode Diagnose ================================================
# 目的: VSCode/Node/Python/Git/拡張/ワークスペース設定/ログ を安全に収集し、
#      GPT に貼るだけの解析プロンプトを生成する
# 対象: macOS / VSCode Stable（Insiders も自動検出）
# 出力: logs/diagnose/vscode_YYYYmmdd_HHMMSS/ 配下に各種ファイルを保存
# ==============================================================================

# ---- 準備 --------------------------------------------------------------------
ts="$(date +%Y%m%d_%H%M%S)"
root="${HOME}/WANSTAGE"
outdir="${root}/logs/diagnose/vscode_${ts}"
mkdir -p "${outdir}"

log() { echo "[$(date '+%F %T')] $*" | tee -a "${outdir}/_diag.log"; }

mask_secrets() {
  # よくあるシークレット環境変数名を伏字化
  sed -E \
    -e 's/(TOKEN|SECRET|PASSWORD|WEBHOOK|KEY|API_KEY|CF_API_TOKEN|SLACK_WEBHOOK_URL|LINE_NOTIFY_TOKEN)=([^[:space:]]+)/\1=***MASKED***/g' \
    -e 's#https://hooks\.slack\.com/[^[:space:]]+#https://hooks.slack.com/***MASKED***#g' \
    -e 's#https://hooks\.zapier\.com/[^[:space:]]+#https://hooks.zapier.com/***MASKED***#g' \
    -e 's#(Bearer|bearer) [A-Za-z0-9._-]+#\1 ***MASKED***#g'
}

# ---- VSCode パス検出 ----------------------------------------------------------
VSCODE_APP=""
for c in "code" "code-insiders"; do
  if command -v "$c" >/dev/null 2>&1; then
    VSCODE_APP="$c"
    break
  fi
done

if [[ -z "${VSCODE_APP}" ]]; then
  log "VSCode CLI (code) が見つかりません。VSCode を起動し、Command Palette → 'Shell Command: Install 'code' command in PATH' を実行してください。"
fi

# ---- 基本情報 ---------------------------------------------------------------
{
  echo "=== System ==="
  sw_vers 2>/dev/null || true
  uname -a

  echo
  echo "=== Shell ==="
  echo "SHELL=${SHELL}"
  zsh --version 2>/dev/null || true
  bash --version 2>/dev/null | head -1 || true

  echo
  echo "=== Homebrew ==="
  brew --version 2>/dev/null || true

  echo
  echo "=== Git ==="
  git --version 2>/dev/null || true
  git config --global --get user.name 2>/dev/null || true
  git config --global --get user.email 2>/dev/null || true
  git config --get-regexp '^url\..*\.insteadof$' 2>/dev/null || true
  git remote -v 2>/dev/null || true
} | tee "${outdir}/system_git.txt" | mask_secrets > "${outdir}/system_git.masked.txt"

# ---- Node / Python / nvm / pyenv --------------------------------------------
{
  echo "=== Node / npm / pnpm / yarn ==="
  node -v 2>/dev/null || true
  npm -v 2>/dev/null || true
  pnpm -v 2>/dev/null || true
  yarn -v 2>/dev/null || true

  echo
  echo "=== nvm / Volta ==="
  command -v nvm >/dev/null 2>&1 && nvm --version || echo "nvm: not found"
  command -v volta >/dev/null 2>&1 && volta --version || echo "volta: not found"

  echo
  echo "=== Python / pip / venv ==="
  python3 --version 2>/dev/null || true
  pip3 --version 2>/dev/null || true
  which python3 2>/dev/null || true
  echo "VIRTUAL_ENV=${VIRTUAL_ENV-}"
  python3 -c "import sys;print('sys.executable',sys.executable)" 2>/dev/null || true

  echo
  echo "=== pyenv / poetry ==="
  command -v pyenv >/dev/null 2>&1 && pyenv --version || echo "pyenv: not found"
  command -v poetry >/dev/null 2>&1 && poetry --version || echo "poetry: not found"
} | tee "${outdir}/runtimes.txt" > /dev/null

# ---- VSCode 拡張・設定 --------------------------------------------------------
if [[ -n "${VSCODE_APP}" ]]; then
  {
    echo "=== ${VSCODE_APP} Version ==="
    "${VSCODE_APP}" --version

    echo
    echo "=== Installed Extensions ==="
    "${VSCODE_APP}" --list-extensions --show-versions
  } | tee "${outdir}/vscode_basic.txt" > /dev/null
fi

# VSCode 設定・ログパス
VSCODE_HOME="${HOME}/Library/Application Support/Code"
VSCODEI_HOME="${HOME}/Library/Application Support/Code - Insiders"

copy_if_exists() {
  local from="$1"; local to="$2"; local max_kb="${3:-5120}"
  if [[ -f "$from" ]]; then
    # 最大サイズ制限（デカすぎるログは先頭・末尾のみ）
    local size_kb=$(( $(wc -c <"$from") / 1024 ))
    if (( size_kb > max_kb )); then
      mkdir -p "$(dirname "$to")"
      head -c $((max_kb*512)) "$from" > "${to}.head"
      echo -e "\n--- TRUNCATED (${size_kb}KB) ---\n" >> "${to}.head"
      tail -c $((max_kb*512)) "$from" > "${to}.tail"
    else
      mkdir -p "$(dirname "$to")"
      cp "$from" "$to"
    fi
  fi
}

# ユーザー設定（settings.json）と拡張設定
for base in "$VSCODE_HOME" "$VSCODEI_HOME"; do
  if [[ -d "$base" ]]; then
    mkdir -p "${outdir}/$(basename "$base")"
    copy_if_exists "$base/User/settings.json" "${outdir}/$(basename "$base")/settings.json"
    copy_if_exists "$base/User/keybindings.json" "${outdir}/$(basename "$base")/keybindings.json"
  fi
done

# ログディレクトリ（直近セッション）
collect_logs() {
  local base="$1"
  local dest="$2"
  [[ -d "$base/logs" ]] || return 0
  local latest="$(ls -1 "$base/logs" | tail -1 || true)"
  [[ -n "$latest" ]] || return 0
  log "Collect logs: $base/logs/$latest"
  mkdir -p "$dest"
  rsync -a --exclude='**/*.trace' --exclude='**/*.cpuprofile' "$base/logs/$latest/" "$dest/" 2>/dev/null || true
}

[[ -d "$VSCODE_HOME" ]]  && collect_logs "$VSCODE_HOME"  "${outdir}/Code_logs"
[[ -d "$VSCODEI_HOME" ]] && collect_logs "$VSCODEI_HOME" "${outdir}/CodeInsiders_logs"

# ESLint / TypeScript サーバーログ（あれば）
find "${outdir}" -type f -iname "*eslint*.log"     -exec cp {} "${outdir}/eslint_logs_$(basename {}).log" \; 2>/dev/null || true
find "${outdir}" -type f -iname "*tsserver*.log"   -exec cp {} "${outdir}/tsserver_logs_$(basename {}).log" \; 2>/dev/null || true
find "${outdir}" -type f -iname "*python*.log"     -exec cp {} "${outdir}/python_logs_$(basename {}).log" \; 2>/dev/null || true

# ---- ワークスペース（WANSTAGE）情報 ------------------------------------------
{
  echo "=== WANSTAGE Git Status ==="
  cd "${root}" 2>/dev/null || echo "WARN: ${root} not found"
  git status -sb 2>/dev/null || true

  echo
  echo "=== WANSTAGE remotes ==="
  git remote -v 2>/dev/null || true

  echo
  echo "=== .git/config (masked) ==="
  if [[ -f ".git/config" ]]; then
    cat .git/config | mask_secrets
  fi

  echo
  echo "=== package.json（存在すれば）==="
  if [[ -f "package.json" ]]; then
    cat package.json
  else
    echo "package.json: not found"
  fi

  echo
  echo "=== pyproject.toml（存在すれば）==="
  if [[ -f "pyproject.toml" ]]; then
    cat pyproject.toml
  else
    echo "pyproject.toml: not found"
  fi

  echo
  echo "=== .env（伏字）==="
  if [[ -f ".env" ]]; then
    cat .env | mask_secrets
  else
    echo ".env: not found"
  fi
} | tee "${outdir}/workspace.txt" > /dev/null

# ---- 直近のエラーメッセージ（あれば投入想定のファイル群） --------------------
# ユーザーが貼りやすい「最新エラーの要約」を作る
{
  echo "=== Heuristics: 最近の VSCode エラー断片（よくあるファイルを走査） ==="
  grep -RHiE "error|exception|traceback|EADDRINUSE|ECONNREFUSED|permission|denied|publickey|module not found|ssl|proxy|cert|timeout" \
    "${outdir}/Code_logs" "${outdir}/CodeInsiders_logs" 2>/dev/null | head -n 200 || true
} | tee "${outdir}/errors_snippets.txt" > /dev/null

# ---- GPT 解析プロンプト生成 ---------------------------------------------------
cat > "${outdir}/GPT_prompt.txt" <<'PROMPT'
あなたは VSCode/Node/Python/Git/シェル/拡張のトラブルシューティングに長けたエンジニアです。
以下の診断出力を精読し、**原因候補の優先度付きリスト**と、**即試せる修正手順（コピペ可能なコマンド付き）**を提示してください。
特に以下の観点を順にチェックしてください：

1) VSCode 拡張の競合・壊れたキャッシュ（tsserver/eslint/python/ext host）
2) Node / Python のバージョン不整合、仮想環境/pyenv/nvm/volta ミスマッチ
3) Git リモート、SSH 認証（publickey / known_hosts / deploy key 権限）
4) プロキシ/DNS/SSL/証明書/社内ネットワーク制限によるフェッチ不可
5) .env / Secrets の未設定 or 誤設定（伏字になっているが変数名から推測）
6) ワークスペース設定（settings.json）や tasks.json のミス
7) ESLint/TypeScript/Python Language Server のログに出ている実エラー

▼ 添付データ（マスク済み）
- system_git.masked.txt （OS/シェル/Git/リモート/URL書き換え）
- runtimes.txt （Node/Python/nvm/pyenv 等）
- vscode_basic.txt （VSCode バージョン・拡張一覧）
- Code_logs / CodeInsiders_logs（直近セッションの VSCode ログ）
- workspace.txt（WANSTAGE リポジトリ状態、package.json/pyproject.toml/.env マスク）
- errors_snippets.txt（エラー断片の要約）

制約：
- 憶測だけで断定しない（ログ根拠と紐付ける）
- 原因ごとに「再現の有無確認→修正→検証コマンド」の順番で提示
- 失敗時のロールバック手順も書く
PROMPT

# 要約とガイド
{
  echo "=== Summary ==="
  echo "診断出力を ${outdir} に保存しました。"
  echo "GPT に貼るべきファイル: ${outdir}/GPT_prompt.txt"
  echo "補助ファイル（必要に応じて添付）:"
  echo " - system_git.masked.txt / runtimes.txt / vscode_basic.txt"
  echo " - Code_logs/ 配下のログ、workspace.txt、errors_snippets.txt"
} | tee "${outdir}/README.txt" > /dev/null

log "Done. Output dir: ${outdir}"
echo "${outdir}"
