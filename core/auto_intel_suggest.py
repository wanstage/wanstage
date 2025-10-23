#!/usr/bin/env python3
# --- WANSTAGE AUTO INTEL SUGGEST (Phase 1/2 Boot) ---
import datetime
import os
import sqlite3

print(f"✅ [AUTO_INTEL] 起動確認: {datetime.datetime.now().isoformat()}")

BASE = os.path.expanduser("~/WANSTAGE")
LOG_FILE = os.path.join(BASE, "logs", "auto_intel_suggest.log")
DB_PATH = os.path.join(BASE, "post_log.sqlite3")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def log(msg: str):
    """ログ出力と標準出力"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def check_recent_activity():
    """投稿やAI実行履歴を軽く監視して提案を出す"""
    try:
        if not os.path.exists(DB_PATH):
            log("⚠ post_log.sqlite3 が見つかりません。スキップ。")
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        tables = cur.fetchone()[0]
        if tables == 0:
            log("⚠ DBにテーブルが存在しません。")
            return
        log("🧠 DB接続OK - 軽度解析開始")
        cur.execute("SELECT COUNT(*) FROM post_log")
        cnt = cur.fetchone()[0]
        log(f"📊 投稿件数: {cnt}")
        if cnt > 30:
            log("💡 提案: auto_macro_gen.sh の生成候補があります。")
        conn.close()
    except Exception as e:
        log(f"❌ DB解析エラー: {e}")


def main():
    log("🚀 AUTO_INTEL_SUGGEST 起動")
    check_recent_activity()
    log("✅ 終了")


if __name__ == "__main__":
    main()
