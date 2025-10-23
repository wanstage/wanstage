#!/bin/bash
set -e
BASE="$HOME/WANSTAGE/auto"
# shellcheck disable=SC1090
source "$BASE/.venv/bin/activate"
python3 "$BASE/run_post_flow.py"
