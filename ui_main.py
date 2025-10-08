import streamlit as st, json, pandas as pd, pathlib

st.set_page_config(page_title="WANSTAGE Posts", layout="wide")
p_json = pathlib.Path("data/outputs/posts_next.json")
p_csv = pathlib.Path("data/outputs/posts_next.csv")

st.title("WANSTAGE 投稿プレビュー")
if p_json.exists():
    data = json.loads(p_json.read_text())
    df = pd.DataFrame(data)
    st.caption(f"Loaded {len(df)} posts from {p_json}")
    st.dataframe(df, use_container_width=True, hide_index=True)
    sel = st.selectbox(
        "Preview row",
        range(len(df)),
        format_func=lambda i: f"{df.loc[i,'date']} #{df.loc[i,'slot']}",
    )
    row = df.loc[sel]
    st.subheader(row["title"])
    st.image(row["image"])
    st.write(row["body"])
    st.code(json.dumps(row, ensure_ascii=False, indent=2), language="json")
else:
    st.warning("data/outputs/posts_next.json が見つかりません。先に生成してください。")
