#!/usr/bin/env zsh
set -euo pipefail
LOG="${1:-logs/notify.log}"
LINES="${LINES:-200}"
if [ ! -f "$LOG" ]; then
  echo "[WANSTAGE] log not found: $LOG"
  exit 0
fi
tail -n "$LINES" "$LOG"
