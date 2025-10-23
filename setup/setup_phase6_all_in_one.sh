#!/bin/bash
set -e
echo "=== 📦 Phase 6: All-in-One Setup 開始 ==="

BASE=~/WANSTAGE
BIN="$BASE/bin"
CORE="$BASE/core"
UI="$BASE/ui"
LOGS="$BASE/logs"

mkdir -p "$BIN" "$CORE" "$UI" "$LOGS"

# ① revenue_analyzer.py
cat <<'PYEOF' > "$CORE/revenue_analyzer.py"
import pandas as pd
import numpy as np
from pathlib import Path

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
PYEOF

chmod +x "$CORE/revenue_analyzer.py"

# ② wan_dashboard_run.sh
cat <<'SH' > "$BIN/wan_dashboard_run.sh"
#!/bin/bash
echo "=== 📊 Streamlit UI 起動中 ==="
streamlit run ~/WANSTAGE/ui/ui_main.py
SH
chmod +x "$BIN/wan_dashboard_run.sh"

# ③ ui_main.py
cat <<'PYEOF' > "$UI/ui_main.py"
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="WANSTAGE 収益スコア", layout="wide")

st.title("📈 投稿別 収益スコア ダッシュボード")

log_file = Path("~/WANSTAGE/logs/revenue_scored.csv").expanduser()
if not log_file.exists():
    st.warning("まだ収益スコアが生成されていません。")
else:
    df = pd.read_csv(log_file)
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.set_index("post_id")["revenue_score"])
PYEOF

echo "✅ setup_phase6_all_in_one.sh 完了"
