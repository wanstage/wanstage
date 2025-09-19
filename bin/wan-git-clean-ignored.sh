#!/usr/bin/env bash
set -Eeuo pipefail
cd "${1:-$HOME/WANSTAGE}"
echo "[dry-run] git clean -n -dX"
git clean -n -dX
read -rp "Run clean ignored? (yes/no): " ans
[ "$ans" = "yes" ] || exit 0
git clean -f -dX
echo "[done] cleaned ignored files"
