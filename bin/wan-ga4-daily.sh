#!/usr/bin/env bash
unset BASH_ENV
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cd "$HOME/WANSTAGE"

# venv 準備
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# 依存（必要最低限）を保証
pip install -q --upgrade pip
pip install -q google-analytics-data notion-client slack_sdk python-dotenv requests gspread google-auth

# 必要な環境変数（.env があれば自動読込）
if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

# 実行
mkdir -p logs
python3 analytics/ga4_pull.py
python3 analytics/notion_upsert_ga4.py
python3 analytics/notify_slack_daily.py || true

echo "[GA4→Notion] finished at $(date '+%F %T')" >> logs/cron_ga4.log
