#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/WANSTAGE"; LOG="$ROOT/logs"; mkdir -p "$LOG"
echo "[stub] full_auto_post_flow executed $(date '+%F %T')" >> "$LOG/full_auto.log"
echo '{"id":"stub","ts":"'"$(date -u +%FT%TZ)"'","caption":"stub"}' > "$LOG/last_post.json"
