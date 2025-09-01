#!/usr/bin/env bash
set -euo pipefail
cd /Users/okayoshiyuki/WANSTAGE/insta-auto
deactivate 2>/dev/null || true
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
[ -f requirements.txt ] && python -m pip install -r requirements.txt
echo "[OK] insta-auto venv repaired"
