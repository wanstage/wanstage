#!/usr/bin/env bash
set -Eeuo pipefail
rm -rf "$HOME/Library/Caches/com.microsoft.VSCode.ShipIt" 2>/dev/null || true
find /tmp -type f -mtime +3 -maxdepth 1 -print -delete 2>/dev/null || true
echo "[wan-tmp-clean] done"
