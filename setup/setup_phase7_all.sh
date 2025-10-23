#!/bin/bash
set -euo pipefail

BASE="$HOME/WANSTAGE"
BIN="$BASE/bin"
CORE="$BASE/core"
UI="$BASE/ui"
LOGS="$BASE/logs"
SETUP="$BASE/setup"

mkdir -p "$BIN" "$CORE" "$UI" "$LOGS" "$SETUP"

echo "=== 🚀 Phase 7: All-in-One Setup 開始 ==="

# --- ① Refiner改善ループスクリプト確認 ---
if [ ! -f "$CORE/gpt_refiner.py" ]; then
  echo "⚠️ gpt_refiner.py が見つかりません。先にフェーズ4まで完了させてください。"
else
  echo "🧠 gpt_refiner.py 検出済み"
fi

# --- ② revenue_analyzer.py 再生成 ---
cat <<'PYEOF' >"$CORE/revenue_analyzer.py"
import pandas as pd
import numpy as np
from pathlib import Path
import datetime

LOG_PATH = Path.home() / "WANSTAGE" / "logs" / "reaction_log.csv"
OUTPUT_CSV = Path.home() / "WANSTAGE" / "logs" / "revenue_scores.csv"

if not LOG_PATH.exists():
    print(f"⚠️ ログが見つかりません: {LOG_PATH}")
    exit(1)

df = pd.read_csv(LOG_PATH)
df["views"] = df["views"].replace(0, np.nan)
df["engagement_rate"] = (df["likes"] + df["comments"]) / df["views"]
df["revenue_score"] = (df["engagement_rate"] * 100).round(2)
top_posts = df.sort_values("revenue_score", ascending=False).head(10)
top_posts.to_csv(OUTPUT_CSV, index=False)
print(f"✅ 収益スコア算出完了: {OUTPUT_CSV}")
print(top_posts[["post_id", "revenue_score"]].to_string(index=False))
PYEOF

chmod +x "$CORE/revenue_analyzer.py"

# --- ③ Streamlit UI生成 ---
cat <<'EOF' >"$UI/ui_main.py"
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="📊 WANSTAGE Revenue Dashboard", layout="wide")

st.title("📊 WANSTAGE 収益スコア ダッシュボード")

csv_path = Path.home() / "WANSTAGE" / "logs" / "revenue_scores.csv"

if csv_path.exists():
    df = pd.read_csv(csv_path)
    st.dataframe(df)
    st.bar_chart(df.set_index("post_id")["revenue_score"])
else:
    st.warning("収益スコアCSVがまだ生成されていません。")
EOF

# --- ④ ダッシュボード起動スクリプト ---
cat <<'EOF' >"$BIN/wan_dashboard_run.sh"
#!/bin/bash
cd ~/WANSTAGE/ui
streamlit run ui_main.py
EOF

chmod +x "$BIN/wan_dashboard_run.sh"

echo "✅ 全ファイル生成完了"
echo "🟢 Streamlit起動 → bash ~/WANSTAGE/bin/wan_dashboard_run.sh"
echo "📦 Phase 7 All-in-One 完了！"
