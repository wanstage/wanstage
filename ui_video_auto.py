import streamlit as st

st.set_page_config(page_title="Video Auto", layout="wide")
st.title("🎞️ Video Auto (stub)")

st.info(
    "指定された `ui_video_auto.py` が見つからなかったため、暫定スタブを表示しています。\n"
    "※ ランチャー側で参照しているファイル名を修正するか、"
    "`ui_video.py` / `pages/Video_Auto.py` など実体を作成して下さい。"
)

with st.expander("簡易動作テスト"):
    st.write("ここは仮ページです。最低限の画面表示のみ行います。")
    if st.button("動作チェック（メッセージ表示）"):
        st.success("OK: Streamlit は正常に実行できています。")
