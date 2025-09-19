#!/usr/bin/env bash
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
limit="${1:-80}"
echo "[wan-guard] CPU > ${limit}%"
ps -ax -o pid,%cpu,%mem,command \
| awk -v L="$limit" '$2+0 > L && /python|node|uvicorn|gunicorn|pm2|ts-node/ {printf("%6s  %6.1f%%  %5.1f%%  %s\n",$1,$2,$3,$4)}'
