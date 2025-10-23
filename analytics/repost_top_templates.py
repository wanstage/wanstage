import datetime
import os
import subprocess

import pandas as pd

BASE = os.path.expanduser("~/WANSTAGE")
RANK_CSV = f"{BASE}/logs/template_score_ranking.csv"
POST_SCRIPT = f"{BASE}/full_auto_post_flow.sh"


def main():
    if not os.path.exists(RANK_CSV):
        print("[WARN] ランキングCSVが存在しません。初回データ生成を待機します。")
        return

    df = pd.read_csv(RANK_CSV)
    top3 = df.sort_values("revenue", ascending=False).head(3)

    print("=== 🚀 上位テンプレ再投稿 ===")
    for _, row in top3.iterrows():
        template = row.get("template") or "unknown"
        print(f"▶ {template} を再投稿中...")
        subprocess.run(["bash", POST_SCRIPT], check=False)
        print("　完了。")

    print("✅ 自動再投稿完了:", datetime.datetime.now())


if __name__ == "__main__":
    main()
