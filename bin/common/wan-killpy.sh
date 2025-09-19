#!/usr/bin/env bash
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cpu="${1:-200}"   # 例: 200% 超で kill（マルチスレ想定）
mem="${2:-2.0}"   # 例: 2.0% 超で kill
echo "[wan-killpy] thresholds: cpu>${cpu}% OR mem>${mem}%"
ps -ax -o pid,%cpu,%mem,command \
| awk -v C="$cpu" -v M="$mem" '
  NR>1 && ($2+0>C || $3+0>M) && /python|node|uvicorn|gunicorn|pm2|ts-node/ {print $1}
' \
| while read -r pid; do
    echo "  killing PID=$pid"
    kill -TERM "$pid" 2>/dev/null || true
    sleep 1
    kill -KILL "$pid" 2>/dev/null || true
  done
echo "[wan-killpy] done."
