#!/usr/bin/env bash
set -Eeuo pipefail
pkill -f "node|nodemon|ts-node|pm2 logs" 2>/dev/null && echo "[wan-killnode] killed" || echo "[wan-killnode] none"
