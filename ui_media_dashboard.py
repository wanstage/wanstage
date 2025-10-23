import glob
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="WANSTAGE Media Dashboard", layout="wide")

log_dir = os.path.expanduser("~/WANSTAGE/logs")
csv_files = sorted(glob.glob(f"{log_dir}/media_scan_*.csv"))

st.title("📊 WANSTAGE Media Scan Dashboard")

if not csv_files:
    st.warning("media_scan_*.csv が見つかりません。先に wan_media_scan.sh を実行してください。")
else:
    latest_csv = csv_files[-1]
    st.write(f"📁 最新ログ: {os.path.basename(latest_csv)}")

    df = pd.read_csv(latest_csv)
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig1, ax1 = plt.subplots()
        ax1.barh(df["file_name"], df["duration"], color="skyblue")
        ax1.set_xlabel("Duration (sec)")
        ax1.set_title("素材の長さ")
        st.pyplot(fig1)
    with col2:
        fig2, ax2 = plt.subplots()
        ax2.barh(df["file_name"], df["size_MB"], color="salmon")
        ax2.set_xlabel("Size (MB)")
        ax2.set_title("ファイルサイズ")
        st.pyplot(fig2)

    st.success("✅ グラフ生成完了")
