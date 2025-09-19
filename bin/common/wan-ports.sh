#!/usr/bin/env bash
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ports="${*:-3000 3001 5173 7860 8000 8001 8080 9000}"
for p in $ports; do
  echo "== PORT $p =="
  lsof -nP -iTCP:"$p" -sTCP:LISTEN || echo "  (no listener)"
done
