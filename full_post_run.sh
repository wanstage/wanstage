#!/bin/zsh
DEBUG="${DEBUG:-0}"
set -eu
set -o pipefail
BASE="$HOME/WANSTAGE"
LOG="$BASE/logs/full_post_run.log"
mkdir -p "$BASE/logs"
exec >> "$LOG" 2>&1
echo "[START] $(date '+%F %T') full_post_run.sh"

PY="$BASE/.venv/bin/python3"
[ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "[FATAL] python3 not found"; exit 1; }

POST_JSON="$($PY core/generate_post.py)"
CAP_JSON="$(printf '%s' "$POST_JSON" | $PY core/compose_caption.py)"
if [ "$DEBUG" = "1" ]; then TMP_FILE="/tmp/wan_post.json"; else if [ "$DEBUG" = "1" ]; then TMP_FILE="/tmp/wan_post.json"; else TMP_FILE="$(mktemp)"; fi; fi
printf '%s' "$CAP_JSON" > "$TMP_FILE"

$PY core/post_to_social.py "$TMP_FILE" || true
$PY notify/notify_mux.py "WANSTAGE flow done"

if [ "$DEBUG" != "1" ]; then if [ "$DEBUG" != "1" ]; then rm -f "$TMP_FILE"; fi; fi
if [ "$DEBUG" = "1" ]; then echo "[DEBUG] TMP_FILE=$TMP_FILE"; fi
echo "[DONE] $(date '+%F %T') full_post_run.sh"
