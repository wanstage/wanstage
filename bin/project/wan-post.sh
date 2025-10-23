#!/usr/bin/env bash
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$HOME/WANSTAGE"
echo "[wan-post] run flow"
# [DISABLED by script] "./scripts/run_magic_flow_now.sh" || "./full_auto_post_flow.sh" || true
echo "[wan-post] last_post.json (text)"
jq -r .text logs/last_post.json 2>/dev/null || echo "(no text)"
echo "[wan-post] tail full_auto.log"
tail -n 80 logs/full_auto.log 2>/dev/null || true
