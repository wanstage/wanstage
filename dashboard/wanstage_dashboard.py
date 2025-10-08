import os, re, glob
from datetime import datetime, date, time as dtime, timedelta
import pandas as pd
import streamlit as st

ROOT = os.path.expanduser("~/WANSTAGE")
LOG = os.path.join(ROOT, "logs", "auto_slideshow_worker.log")
OUT = os.path.join(ROOT, "videos", "out")

st.set_page_config(page_title="WANSTAGE Dashboard", layout="wide")
st.title("🎬 WANSTAGE AutoSlideshow Dashboard")

# ---------- Sidebar: 日時フィルタ ----------
today = date.today()
start_default = datetime.combine(today, dtime(0, 0, 0))
end_default = datetime.now()

st.sidebar.subheader("フィルタ")
start_date = st.sidebar.date_input("開始日", value=today)
end_date = st.sidebar.date_input("終了日", value=today)
start_time = st.sidebar.time_input("開始時刻", value=dtime(0, 0, 0))
end_time = st.sidebar.time_input("終了時刻", value=datetime.now().time())

start_dt = datetime.combine(start_date, start_time)
end_dt = datetime.combine(end_date, end_time)

# ---------- ログ解析 ----------
rows = []
if os.path.exists(LOG):
    with open(LOG, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m_ts = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
            if not m_ts:
                continue
            ts = datetime.strptime(m_ts.group(1), "%Y-%m-%d %H:%M:%S")

            if "✅ スライドショー生成:" in line:
                m_path = re.search(r": (/.+\.mp4)", line)
                path = m_path.group(1) if m_path else ""
                rows.append(
                    {"time": ts, "level": "OK", "message": "生成", "path": path, "service": ""}
                )

            elif "ERROR:" in line:
                msg = line.split("ERROR:", 1)[1].strip()
                rows.append(
                    {"time": ts, "level": "ERROR", "message": msg, "path": "", "service": ""}
                )

            # あるなら拾う（将来のログ拡張用／無ければ出ません）
            elif ("Slack" in line and "成功" in line) or ("Slack" in line and "失敗" in line):
                rows.append(
                    {
                        "time": ts,
                        "level": "INFO",
                        "message": line.strip(),
                        "path": "",
                        "service": "Slack",
                    }
                )
            elif ("Mastodon" in line and "成功" in line) or ("Mastodon" in line and "失敗" in line):
                rows.append(
                    {
                        "time": ts,
                        "level": "INFO",
                        "message": line.strip(),
                        "path": "",
                        "service": "Mastodon",
                    }
                )
else:
    st.warning(f"ログが見つかりません: {LOG}")

df = pd.DataFrame(rows)
if not df.empty:
    df = df.sort_values("time", ascending=False)

# フィルタ適用
if not df.empty:
    mask = (df["time"] >= start_dt) & (df["time"] <= end_dt)
    dff = df[mask].copy()
else:
    dff = df

# ---------- サマリ ----------
colA, colB, colC = st.columns(3)
if not dff.empty:
    ok_cnt = int((dff["level"] == "OK").sum())
    err_cnt = int((dff["level"] == "ERROR").sum())
    total = ok_cnt + err_cnt
    rate = (ok_cnt / total * 100.0) if total > 0 else 0.0
    colA.metric("成功件数", f"{ok_cnt}")
    colB.metric("エラー件数", f"{err_cnt}")
    colC.metric("成功率", f"{rate:.1f}%")
else:
    colA.metric("成功件数", "0")
    colB.metric("エラー件数", "0")
    colC.metric("成功率", "—")

# ---------- 主要テーブル ----------
c1, c2 = st.columns([2, 1])
with c1:
    st.subheader("最新イベント（フィルタ適用後）")
    st.dataframe(dff.head(50), use_container_width=True)

with c2:
    st.subheader("時間帯別（当日 または 選択範囲）")
    if not dff.empty:
        tmp = dff.copy()
        tmp["hour"] = tmp["time"].dt.strftime("%m/%d %H:00")
        hourly = tmp[tmp["level"] == "OK"].groupby("hour").size().rename("count").reset_index()
        st.bar_chart(hourly.set_index("hour"))
    else:
        st.info("まだデータがありません。")

# ---------- 生成ファイル一覧 ----------
st.subheader("生成ファイル一覧（最新20）")
files = sorted(glob.glob(os.path.join(OUT, "*.mp4")), key=os.path.getmtime, reverse=True)[:20]
table = []
for f in files:
    try:
        table.append(
            {
                "file": os.path.basename(f),
                "size(MB)": round(os.path.getsize(f) / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(os.path.getmtime(f)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "path": f,
            }
        )
    except FileNotFoundError:
        pass
st.dataframe(pd.DataFrame(table), use_container_width=True)

st.caption(
    f"LOG: {LOG}  |  OUT: {OUT}  |  範囲: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} → {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
)
