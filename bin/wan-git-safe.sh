#!/usr/bin/env bash
set -Eeuo pipefail
cd "${1:-$HOME/WANSTAGE}"
echo "== git status =="; git status -s
echo
echo "== .gitignore check: preview clean -dX =="; git clean -n -dX || true
echo
echo "== secret scan (gitleaks) =="
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --config .gitleaks.toml --redact --no-banner || true
else
  echo "gitleaks not installed"
fi
