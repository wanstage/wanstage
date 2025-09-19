#!/usr/bin/env bash
set -Eeuo pipefail
dir="${1:-$HOME/WANSTAGE}"
echo "[wan-find-big] $dir"
find "$dir" -type f -not -path "*/.git/*" -print0 \
  | xargs -0 du -ah 2>/dev/null | sort -h | tail -n 20
