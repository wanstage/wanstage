#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/WANSTAGE"; LOGS="$BASE/logs"; mkdir -p "$LOGS"
[ -d "$BASE/venv" ] && source "$BASE/venv/bin/activate" || true
python3 "$BASE/monetize/send_kpi_to_sheet.py" >> "$LOGS/kpi.log" 2>&1 || true
