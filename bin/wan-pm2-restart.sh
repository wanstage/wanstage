#!/usr/bin/env bash
set -Eeuo pipefail

# ---- pm2 の実体を安全に解決 ----
PM2="${PM2_PATH:-$(command -v pm2 || true)}"
if [[ -z "${PM2}" ]]; then
  for d in "$HOME/.nvm/versions/node"/*/bin /opt/homebrew/bin /usr/local/bin; do
    [[ -x "$d/pm2" ]] && PM2="$d/pm2" && break || true
  done
fi
if [[ -z "${PM2}" ]]; then
  echo "[wan-pm2] pm2 not found."
  echo "  → npm i -g pm2  を実行、もしくは  export PM2_PATH=/absolute/path/to/pm2"
  exit 1
fi

apps=( "$@" )
[[ ${#apps[@]} -gt 0 ]] || apps=( wan-node-api wan-uvicorn wan-py-worker wan-secrets-cron )

echo "[wan-pm2-restart] apps: ${apps[*]}"
for a in "${apps[@]}"; do
  "$PM2" restart "$a" || true
done

"$PM2" save || true
"$PM2" ls
