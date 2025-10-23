#!/usr/bin/env python3
import datetime as dt
import os

import pandas as pd

base = os.path.expanduser("~/WANSTAGE")
log_path = os.path.join(base, "logs", "template_score_ranking.csv")

if not os.path.exists(log_path):
    print(f"⚠️ ログが見つかりません: {log_path}")
    exit(1)

df = pd.read_csv(log_path)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
this_week = df[df["date"] >= (dt.datetime.now() - dt.timedelta(days=7))]

summary = this_week.groupby("template")["revenue"].sum().sort_values(ascending=False)
print("=== 📊 今週の収益ランキング ===")
print(summary.head(10))
summary.to_csv(os.path.join(base, "logs", "weekly_summary.csv"))
print("\n✅ 集計結果を保存しました。")
