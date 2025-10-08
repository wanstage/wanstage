import streamlit as st
import pathlib

st.set_page_config(page_title="Video Preview", layout="wide")
st.title("動画プレビュー")

outdir = pathlib.Path("videos/out")
outdir.mkdir(parents=True, exist_ok=True)

videos = sorted(outdir.glob("*.mp4"))
if not videos:
    st.info("videos/out に動画がありません。まずは生成してください。")
else:
    for v in videos:
        st.subheader(v.name)
        with open(v, "rb") as f:
            st.video(f.read())
