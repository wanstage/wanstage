#!/bin/bash
set -e
BASE="$HOME/WANSTAGE/auto"
source "$BASE/.venv/bin/activate"
python3 "$BASE/bin/post_content.py"
