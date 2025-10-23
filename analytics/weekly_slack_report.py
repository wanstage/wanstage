#!/usr/bin/env python3
import os
from datetime import datetime, timedelta

import pandas as pd
import requests

BASE = os.path.expanduser("~/WANSTAGE")
CSV_PATH = f"{BASE}/logs/post_log.csv"
WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

if not WEBHOOK:
    print("[WARN] SLACK_WEBHOOK_URL not set.")
    exit(0)

if not os.path.exists(CSV_PATH):
    print("[WARN] No post_log.csv found.")
    exit(0)

df = pd.read_csv(CSV_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
this_week = df[df["date"] >= datetime.now() - timedelta(days=7)]

total = this_week["revenue"].sum() if "revenue" in df.columns else 0
count = len(this_week)

msg = {
    "text": f"📊 *WANSTAGE 週次レポート*\n投稿数: {count}件\n合計収益: ¥{int(total)}\n({datetime.now():%Y/%m/%d})"
}
requests.post(WEBHOOK, json=msg)
print("[OK] Slack週次レポート送信完了")
