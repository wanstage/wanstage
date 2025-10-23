#!/usr/bin/env python3
import json
import os

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("🚀 GitHub Trending Monitor")


def load_github_data():
    trending_path = os.path.join(os.path.dirname(__file__), "logs/github_trending.json")
    code_path = os.path.join(os.path.dirname(__file__), "logs/github_code_stats.json")
    trending = None
    code = None
    if os.path.exists(trending_path):
        with open(trending_path, "r") as f:
            trending = json.load(f)
    if os.path.exists(code_path):
        with open(code_path, "r") as f:
            code = json.load(f)
    return trending, code


trending, code = load_github_data()

if trending:
    st.subheader(f"📈 Trending Repos ({trending.get('language', '')})")
    df = pd.DataFrame(trending["data"])
    st.dataframe(df)
else:
    st.warning("トレンドデータがまだ生成されていません。")

if code:
    st.subheader("🧮 Code Search Statistics")
    st.metric(label=f"Keyword: {code.get('keyword', '')}", value=f"{code.get('count', 0):,}")
else:
    st.info("コード統計データが未生成です。")
