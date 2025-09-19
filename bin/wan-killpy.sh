#!/usr/bin/env bash
set -Eeuo pipefail
pkill -f "python|uvicorn|gunicorn" 2>/dev/null && echo "[wan-killpy] killed" || echo "[wan-killpy] none"
