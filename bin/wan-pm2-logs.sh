#!/usr/bin/env bash
set -Eeuo pipefail
app="${1:-all}"
if [ "$app" = "all" ]; then
  pm2 logs --lines 50
else
  pm2 logs "$app" --lines 50
fi
