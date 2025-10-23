from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="WANSTAGE 収益スコア", layout="wide")

st.title("📈 投稿別 収益スコア ダッシュボード")

log_file = Path("~/WANSTAGE/logs/revenue_scored.csv").expanduser()
if not log_file.exists():
    st.warning("まだ収益スコアが生成されていません。")
else:
    df = pd.read_csv(log_file)
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.set_index("post_id")["revenue_score"])
