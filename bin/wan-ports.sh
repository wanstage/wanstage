#!/usr/bin/env bash
set -Eeuo pipefail
ports="${*:-3000 5000 8000 8080 9000}"
for p in $ports; do
  echo "== PORT $p =="; lsof -i :$p -n -P || true; echo
done
