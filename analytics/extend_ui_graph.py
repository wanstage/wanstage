import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

BASE = os.path.expanduser("~/WANSTAGE")
RANK_CSV = f"{BASE}/logs/template_score_ranking.csv"


def render_extended_graph():
    st.markdown("### 💹 テンプレ別収益トレンド (拡張版)")
    if not os.path.exists(RANK_CSV):
        st.warning("template_score_ranking.csv がまだ存在しません。")
        return

    df = pd.read_csv(RANK_CSV)
    if "date" in df.columns and "revenue" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        fig, ax = plt.subplots(figsize=(8, 4))
        for template, group in df.groupby("template"):
            ax.plot(group["date"], group["revenue"], label=template)
        ax.legend()
        ax.set_title("テンプレ別 収益推移")
        st.pyplot(fig)
    else:
        st.warning("CSVに必要な列 (date, revenue) が不足しています。")
