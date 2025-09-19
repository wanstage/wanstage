#!/usr/bin/env bash
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
apps=(wan-node-api wan-uvicorn wan-py-worker wan-secrets-cron)
[[ $# -gt 0 ]] && apps=("$@")
echo "[wan-pm2-restart] apps: ${apps[*]}"
for a in "${apps[@]}"; do
  pm2 restart "$a" --update-env || true
done
pm2 save || true
echo "[wan-pm2-restart] status"
pm2 ls
