from pathlib import Path

import numpy as np
import pandas as pd

LOG_FILE = Path("~/WANSTAGE/logs/reaction_log.csv").expanduser()
OUTPUT_CSV = Path("~/WANSTAGE/logs/revenue_scored.csv").expanduser()

if not LOG_FILE.exists():
    print(f"⚠️ ログファイルが見つかりません: {LOG_FILE}")
    exit(1)

df = pd.read_csv(LOG_FILE)
df["views"] = df["views"].replace(0, np.nan)
df["engagement_rate"] = (df["likes"] + df["comments"]) / df["views"]
df["revenue_score"] = (df["engagement_rate"] * 100).round(2)
top_posts = df.sort_values("revenue_score", ascending=False).head(10)

top_posts.to_csv(OUTPUT_CSV, index=False)
print(f"✅ 収益スコア算出完了: {OUTPUT_CSV}")
print(top_posts[["post_id", "revenue_score"]].to_string(index=False))
