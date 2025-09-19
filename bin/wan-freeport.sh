#!/usr/bin/env bash
set -Eeuo pipefail
p="${1:-}"
[ -n "$p" ] || { echo "usage: wan-freeport <port>"; exit 1; }
pids=$(lsof -t -i :$p -sTCP:LISTEN 2>/dev/null || true)
[ -z "$pids" ] && { echo "[wan-freeport] no listener on $p"; exit 0; }
echo "$pids" | xargs -I{} kill -9 {} || true
echo "[wan-freeport] killed: $pids"
