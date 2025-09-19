#!/usr/bin/env bash
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
echo "[wan-stopall] pm2 stop all"
pm2 stop all >/dev/null 2>&1 || true
echo "[wan-stopall] killing servers"
pkill -f "uvicorn|gunicorn|ts-node|nodemon|http-server|python -m http" 2>/dev/null || true
sleep 1
echo "[wan-stopall] residual pm2 logs viewers"
pkill -f "pm2 logs" 2>/dev/null || true
echo "[wan-stopall] done."
