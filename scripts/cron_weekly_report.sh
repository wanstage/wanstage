#!/bin/zsh
source "$HOME/WANSTAGE/.venv/bin/activate"
python3 ~/WANSTAGE/analytics/sync_to_sheets.py
python3 ~/WANSTAGE/analytics/weekly_slack_report.py
