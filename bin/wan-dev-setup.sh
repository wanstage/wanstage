#!/usr/bin/env bash
set -Eeuo pipefail

cd "$HOME/WANSTAGE"

# venv 作成・有効化
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

# pip系アップデート（3.13対応でwheel必須）
python -m pip install -U pip setuptools wheel

# 運用ミニマム（投稿フロー・通知）
python -m pip install \
  requests gspread google-auth google-auth-oauthlib slack_sdk python-dotenv

# 可視化・ダッシュボード系
python -m pip install \
  pandas numpy matplotlib plotly streamlit watchdog notion-client

# GA4 / Notion 連携
python -m pip install google-analytics-data

# スクレイピング/自動ブラウザ
python -m pip install beautifulsoup4 lxml selenium playwright
python -m playwright install --with-deps || true

# 金融系
python -m pip install yfinance forex-python

# APIサーバ
python -m pip install "fastapi[standard]" uvicorn pydantic

# ユーティリティ
python -m pip install tqdm rich

echo "[OK] WANSTAGE dev setup completed."
echo "→ 有効化:  source ~/WANSTAGE/.venv/bin/activate"
