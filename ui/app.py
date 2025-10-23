import os

import pandas as pd  # noqa: F401
import streamlit as st

st.set_page_config(page_title="WANSTAGE Dashboard", layout="wide")
st.title("WANSTAGE 収益ダッシュボード")

st.subheader("Instagram 自動投稿設定")
username = os.getenv("IG_USERNAME", "")
password = os.getenv("IG_PASSWORD", "")
image_path = os.getenv("IG_IMAGE", "")

with st.form("ig_form"):
    u = st.text_input("IG_USERNAME", value=username)
    p = st.text_input("IG_PASSWORD", value=password, type="password")
    img = st.text_input("IG_IMAGE", value=image_path)
    submitted = st.form_submit_button("保存")
    if submitted:
        home = os.environ.get("HOME", ".")
        envp = os.path.join(home, "WANSTAGE", ".env")
        os.makedirs(os.path.dirname(envp), exist_ok=True)
        lines = [
            f"IG_USERNAME={u}",
            f"IG_PASSWORD={p}",
            f"IG_IMAGE={img}",
        ]
        with open(envp, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        st.success(".env に追記しました。反映には `wanenv` を実行してください。")
