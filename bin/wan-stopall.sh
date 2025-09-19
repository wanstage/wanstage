#!/usr/bin/env bash
set -Eeuo pipefail
"$HOME/WANSTAGE/bin/wan-killpy.sh" || true
"$HOME/WANSTAGE/bin/wan-killnode.sh" || true
pkill -f "tail -f .*logs" 2>/dev/null || true
echo "[wan-stopall] done"
