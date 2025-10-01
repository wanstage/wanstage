#!/usr/bin/env bash
set -euo pipefail

TAG="${TAG:-v20250926-r2}"   # デフォルトは実在する r2 に
GH_REPO="${GH_REPO:-wanstage/wanstage}"
SUMS="SHA256SUMS_${TAG}.txt"
SECKEY="$HOME/.minisign_keys/minisign_seckey.txt"
PUBKEY_FILE="minisign_pubkey.txt"

log(){ printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }

log "auth status"
gh auth status -h github.com || { echo "gh not authenticated"; exit 1; }

log "check release existence"
if ! gh release view -R "$GH_REPO" "$TAG" >/dev/null 2>&1; then
  echo "Release $TAG not found in $GH_REPO"
  gh release list -R "$GH_REPO" | head
  exit 1
fi

log "download ${SUMS}"
gh release download -R "$GH_REPO" "$TAG" -p "$SUMS"

log "sign ${SUMS}"
if [[ -n "${MINISIGN_PASSPHRASE:-}" ]]; then
  expect <<EXP
set timeout -1
spawn minisign -S -s "$SECKEY" -m "$SUMS"
expect "Enter passphrase: "
send -- "$MINISIGN_PASSPHRASE\r"
expect eof
EXP
else
  minisign -S -s "$SECKEY" -m "$SUMS"
fi

if [[ -f "$PUBKEY_FILE" ]]; then
  log "verify ${SUMS}"
  minisign -Vm "$SUMS" -p "$PUBKEY_FILE"
else
  log "no $PUBKEY_FILE -> verify skipped"
fi

log "done"
