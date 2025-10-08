import sqlite3, os, pandas as pd, matplotlib.pyplot as plt, streamlit as st

DB = os.path.join(os.path.expanduser("~/WANSTAGE"), "data", "short.db")
st.set_page_config(page_title="WANSTAGE Dashboard", layout="wide")
st.title("WANSTAGE Shortener Dashboard")


@st.cache_data
def load_links(q=""):
    conn = sqlite3.connect(DB)
    if q:
        df = pd.read_sql_query(
            """
          SELECT code,long_url,created_at,IFNULL(tags,'') AS tags,IFNULL(note,'') AS note
          FROM links
          WHERE code LIKE ? OR long_url LIKE ? OR IFNULL(tags,'') LIKE ? OR IFNULL(note,'') LIKE ?
          ORDER BY created_at DESC LIMIT 500
        """,
            conn,
            params=[f"%{q}%"] * 4,
        )
    else:
        df = pd.read_sql_query(
            """
          SELECT code,long_url,created_at,IFNULL(tags,'') AS tags,IFNULL(note,'') AS note
          FROM links ORDER BY created_at DESC LIMIT 500
        """,
            conn,
        )
    conn.close()
    return df


@st.cache_data
def load_clicks(code):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(
        """
      SELECT substr(ts,1,10) AS day, COUNT(*) AS clicks
      FROM clicks WHERE code=? GROUP BY day ORDER BY day
    """,
        conn,
        params=[code],
    )
    conn.close()
    return df


col1, col2 = st.columns([2, 3])
with col1:
    q = st.text_input("検索（code / URL / tags / note）", "")
    links = load_links(q)
    st.dataframe(links, use_container_width=True, height=400)
    codes = links["code"].tolist()
    sel = st.selectbox("コード選択", codes)

with col2:
    if sel:
        df = load_clicks(sel)
        st.subheader(f"Clicks by Day - {sel}")
        if not df.empty:
            fig, ax = plt.subplots()
            ax.plot(df["day"], df["clicks"])
            ax.set_xlabel("Day")
            ax.set_ylabel("Clicks")
            plt.xticks(rotation=45)
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("クリックデータがありません")
