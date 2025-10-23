selected_tab = "Home"
language = "Python"
keyword = "ai"
count = "count"
PACK = "wanstage_github_trending_pack"
import os

os.environ["STREAMLIT_SERVER_PORT"] = "0"

import os
import pathlib
import subprocess
import time

import streamlit as st

BASE = os.path.expanduser("~/WANSTAGE")
LOGS = os.path.join(BASE, "logs")
pathlib.Path(LOGS).mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="WANSTAGE Dev UI", layout="wide")
st.title("WANSTAGE Dev Dashboard")

st.caption(f"BASE: {BASE}")


# 共通ユーティリティ
def run_cmd(cmd: str):
    with st.spinner(f"Running: {cmd}"):
        try:
            cp = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                timeout=60 * 30,
            )
            st.code(cp.stdout or "(no stdout)")
            if cp.stderr:
                with st.expander("stderr"):
                    st.code(cp.stderr)
            st.success(f"exit code: {cp.returncode}")
        except subprocess.TimeoutExpired:
            st.error("⏰ Timeout")
        except Exception as e:
            st.error(f"❌ {e}")


def script_exists(p: str) -> bool:
    return pathlib.Path(p).exists() and os.access(p, os.X_OK)


# 1) 今すぐ全実行（例：wanstage_flex_notify_and_dbgen.sh）
full_run = os.path.join(BASE, "wanstage_flex_notify_and_dbgen.sh")
st.subheader("⚡ 今すぐ全実行")
if script_exists(full_run):
    if st.button("▶ 実行（Flex通知→DB登録 一括）", type="primary"):
        run_cmd(
            f'/bin/zsh -lc "cd {BASE} && . {BASE}/.venv/bin/activate 2>/dev/null || true; {full_run}"'
        )
else:
    st.warning(f"スクリプトが見つかりません: {full_run}")

# 2) ネット監視を手動実行
netwatch = os.path.join(BASE, "bin", "wan_netwatch.sh")
st.subheader("🌐 ネット監視（手動）")
col1, col2 = st.columns(2)
if script_exists(netwatch):
    with col1:
        if st.button("networkQuality & ping を実行"):
            run_cmd(f'/bin/zsh -lc "{netwatch}"')
    with col2:
        csv = os.path.join(LOGS, f"netwatch_{time.strftime('%Y-%m')}.csv")
        if pathlib.Path(csv).exists():
            with open(csv, "r") as f:
                data = f.read().strip().splitlines()
            st.caption("最新ログ（末尾20行）")
            st.code("\n".join(data[-20:]))
        else:
            st.info("まだCSVがありません。実行すると生成されます。")
else:
    st.warning(f"スクリプトが見つかりません: {netwatch}")

# 3) アイドルターミナル自動クローズ（手動トリガ）
idle_killer = os.path.join(BASE, "bin", "wan_auto_close_idle_terms.sh")
st.subheader("🪄 アイドルターミナル整理（手動）")
if script_exists(idle_killer):
    idle_min = st.number_input(
        "IDLE_MIN（分）",
        min_value=1,
        max_value=120,
        value=int(os.getenv("IDLE_MIN", "15")),
    )
    dry_run = st.checkbox("DRY RUN（終了せずログのみ）", value=False)
    if st.button("▶ 実行"):
        cmd = f"IDLE_MIN={idle_min} DRY_RUN={'1' if dry_run else '0'} {idle_killer}"
        run_cmd(f'/bin/zsh -lc "{cmd}"')
    # ログ表示
    log_file = os.path.join(LOGS, "auto_close_idle_terms.log")
    if pathlib.Path(log_file).exists():
        with st.expander("ログ（末尾50行）"):
            with open(log_file, "r") as f:
                lines = f.read().splitlines()
            st.code("\n".join(lines[-50:]))
else:
    st.warning(f"スクリプトが見つかりません: {idle_killer}")

# 4) PM2 制御ショートカット
st.subheader("🧩 PM2 制御")
colL, colR = st.columns(2)
with colL:
    if st.button("PM2 start wan-ui-dev"):
        run_cmd('/bin/zsh -lc "pm2 start $HOME/WANSTAGE/pm2.dev.ecosystem.config.js && pm2 save"')
with colR:
    if st.button("PM2 stop wan-ui-dev"):
        run_cmd('/bin/zsh -lc "pm2 stop wan-ui-dev && pm2 delete wan-ui-dev && pm2 save"')

st.caption("Powered by WANSTAGE Dev Pack")

# --- WANSTAGE_ANALYTICS_V2 拡張読込 ---
from analytics.extend_ui_graph import render_extended_graph

render_extended_graph()

import json
import os

# ======================================================
# 🧭 GitHub Trending タブ (WANSTAGE_ANALYTICS_V4)
# ======================================================
import pandas as pd


def load_github_data():
    trending_path = os.path.join(
        "/Users/okayoshiyuki/WANSTAGE/wanstage_github_trending_pack",
        "logs/github_trending.json",
    )
    code_path = os.path.join(
        "/Users/okayoshiyuki/WANSTAGE/wanstage_github_trending_pack",
        "logs/github_code_stats.json",
    )
    trending, code = None, None
    if os.path.exists(trending_path):
        with open(trending_path, "r") as f:
            trending = json.load(f)
    if os.path.exists(code_path):
        with open(code_path, "r") as f:
            code = json.load(f)
    return trending, code


if selected_tab == "GitHub Trending":
    st.title("🚀 GitHub Trending Monitor")
    st.write("最新のGitHubトレンドとコード統計を自動収集・可視化します。")

    trending, code = load_github_data()
    if trending:
        st.subheader(f"📈 Trending Repositories ({trending[language]})")
        df = pd.DataFrame(trending["data"])
        st.dataframe(df)
    else:
        st.warning(
            "トレンドデータがまだ生成されていません。fetch_github_trending.py を実行してください。"
        )

    if code:
        st.subheader("🧮 Code Search Statistics")
        st.metric(label=f"Keyword: {code[keyword]}", value=f"{code[count]:,}")
    else:
        st.info("コード統計データが未生成です。fetch_github_code_stats.py を実行してください。")

    if st.button("🔄 トレンド再取得"):
        os.system(
            f"cd {PACK} && python3 fetch_github_trending.py && python3 fetch_github_code_stats.py"
        )
        st.success("再取得完了！ページを再読み込みしてください。")
