#!/usr/bin/env zsh
set -euo pipefail

# ------------------------------
# release-local.zsh
# 例:
#   ./release-local.zsh --sign --clean
#   ./release-local.zsh --reldate=20250926 --categories=094057,image,media --sign --clean
#   MPW='your-pass' ./release-local.zsh --sign   # パスフレーズを非対話で渡す
# オプション:
#   --reldate=YYYYMMDD     : 既定は今日
#   --categories=a,b,c     : 既定 "094057,image,media"
#   --sign                 : minisign で署名
#   --clean                : wan-clean.sh を先に実行
#   --skip-notices         : NOTICES 収集をスキップ
#   --seckey=PATH          : 既定 ~/.minisign_keys/minisign_seckey.txt
#   --pubkey=PATH          : 既定 ./minisign_pubkey.txt or ~/.minisign_keys/minisign_pubkey.txt
# ------------------------------

log() { print -r -- "[$(date '+%F %T')] $*"; }

# defaults
RELDATE=$(date +%Y%m%d)
CATEGORIES="094057,image,media"
DO_SIGN=false
DO_CLEAN=false
SKIP_NOTICES=false
SECKEY="${HOME}/.minisign_keys/minisign_seckey.txt"
PUBKEY=""
ROOT="$(pwd)"

# parse args
for arg in "$@"; do
  case "$arg" in
    --reldate=*)     RELDATE="${arg#*=}";;
    --categories=*)  CATEGORIES="${arg#*=}";;
    --sign)          DO_SIGN=true;;
    --clean)         DO_CLEAN=true;;
    --skip-notices)  SKIP_NOTICES=true;;
    --seckey=*)      SECKEY="${arg#*=}";;
    --pubkey=*)      PUBKEY="${arg#*=}";;
    *) print -ru2 -- "WARN: unknown option: $arg";;
  esac
done

# resolve pubkey
if [[ -z "${PUBKEY}" ]]; then
  if [[ -f "${ROOT}/minisign_pubkey.txt" ]]; then
    PUBKEY="${ROOT}/minisign_pubkey.txt"
  elif [[ -f "${HOME}/.minisign_keys/minisign_pubkey.txt" ]]; then
    PUBKEY="${HOME}/.minisign_keys/minisign_pubkey.txt"
  else
    PUBKEY=""  # 署名検証しない場合は空でも可
  fi
fi

# sanity
command -v zip >/dev/null 2>&1 || { print -ru2 -- "zip が必要です"; exit 1; }
command -v tar >/dev/null 2>&1 || { print -ru2 -- "tar が必要です"; exit 1; }
if $DO_SIGN; then
  command -v minisign >/dev/null 2>&1 || { print -ru2 -- "minisign が必要です"; exit 1; }
  [[ -f "$SECKEY" ]] || { print -ru2 -- "秘密鍵が見つかりません: $SECKEY"; exit 1; }
fi

# optional clean
if $DO_CLEAN; then
  if [[ -x "${ROOT}/scripts/wan-clean.sh" ]]; then
    log "CLEAN: scripts/wan-clean.sh 実行"
    "${ROOT}/scripts/wan-clean.sh"
  else
    log "CLEAN: スキップ（scripts/wan-clean.sh 不在）"
  fi
fi

# 既存パッカーがあれば使う
pack_by_category() {
  local cat="$1"
  if [[ -x "${ROOT}/pack-by-category.zsh" ]]; then
    log "PACK: pack-by-category.zsh (${cat})"
    "${ROOT}/pack-by-category.zsh" --category="${cat}" --reldate="${RELDATE}"
  elif [[ -x "${ROOT}/pack-by-category.sh" ]]; then
    log "PACK: pack-by-category.sh (${cat})"
    "${ROOT}/pack-by-category.sh" --category="${cat}" --reldate="${RELDATE}"
  else
    # フォールバック: ディレクトリ雛形のみ
    log "PACK: フォールバック（${cat}) → release_${cat} だけ作成"
    mkdir -p "release_${cat}"
  fi
}

# SBOM/NOTICES
collect_notices() {
  $SKIP_NOTICES && { log "NOTICES: スキップ"; return; }
  if [[ -x "${ROOT}/collect-licenses.zsh" ]]; then
    log "NOTICES: collect-licenses.zsh 実行"
    "${ROOT}/collect-licenses.zsh" || log "NOTICES: 警告: 収集でエラー（続行）"
  else
    log "NOTICES: スキップ（collect-licenses.zsh 不在）"
  fi
}

# 1) 各カテゴリをパック/用意
collect_notices
IFS=, read -rA CAT_ARR <<< "${CATEGORIES}"
for c in "${CAT_ARR[@]}"; do
  pack_by_category "$c"
done

# 2) メタフォルダ組立
ALL_DIR="release_all_${RELDATE}"
log "BUNDLE: ${ALL_DIR} を作成"
rm -rf "${ALL_DIR}"
mkdir -p "${ALL_DIR}"

# 想定されるサブパッケージがあれば同梱
for sub in "${RELDATE}" "${CAT_ARR[@]}"; do
  if [[ -d "release_${sub}" ]]; then
    cp -a "release_${sub}" "${ALL_DIR}/"
  fi
done

# 3) 公開鍵を同梱（あれば）
if [[ -n "${PUBKEY}" && -f "${PUBKEY}" ]]; then
  cp -f "${PUBKEY}" "${ALL_DIR}/minisign_pubkey.txt"
fi

# 4) アーカイブ作成
TAR="release_all_${RELDATE}.tar.gz"
ZIP="release_all_${RELDATE}.zip"

log "ARCHIVE: tar.gz を作成 → ${TAR}"
tar -czf "${TAR}" "${ALL_DIR}"

log "ARCHIVE: zip を作成 → ${ZIP}"
rm -f "${ZIP}"
( cd "${ALL_DIR%/*}" >/dev/null 2>&1 || true; )
zip -r "${ZIP}" "${ALL_DIR}" >/dev/null

# 5) SHA256
SHA="SHA256SUMS_release_all_${RELDATE}.txt"
log "HASH: ${SHA} を生成"
shasum -a 256 "${TAR}" "${ZIP}" > "${SHA}"

# 6) 署名（必要時）
if $DO_SIGN; then
  log "SIGN: minisign で署名中"
  if [[ -n "${MPW:-}" ]]; then
    # -S で passphrase を stdin から受け取る
    printf '%s\n' "$MPW" | minisign -S -s "${SECKEY}" -Sm "${TAR}"
    printf '%s\n' "$MPW" | minisign -S -s "${SECKEY}" -Sm "${ZIP}"
    printf '%s\n' "$MPW" | minisign -S -s "${SECKEY}" -Sm "${SHA}"
  else
    minisign -s "${SECKEY}" -Sm "${TAR}"
    minisign -s "${SECKEY}" -Sm "${ZIP}"
    minisign -s "${SECKEY}" -Sm "${SHA}"
  fi
fi

# 7) 最終表示
log "DONE:"
ls -lh "${TAR}" "${ZIP}" 2>/dev/null || true
[[ -f "${SHA}" ]] && ls -lh "${SHA}" || true
[[ -f "${TAR}.minisig" ]] && ls -lh "${TAR}.minisig" || true
[[ -f "${ZIP}.minisig" ]] && ls -lh "${ZIP}.minisig" || true
[[ -f "${SHA}.minisig" ]] && ls -lh "${SHA}.minisig" || true
