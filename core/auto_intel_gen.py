import sys

# --- 互換層: 古い引数 (--mode, --env) 無視対応 ---
compat_args = {"--mode", "--env"}
sys.argv = [a for a in sys.argv if not any(c in a for c in compat_args)]

import argparse
import datetime

#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

BASE = os.path.expanduser("~/WANSTAGE")
LOG_FILE = os.path.join(BASE, "logs", "auto_intel_gen_fixed2.log")


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def slack_notify(msg: str):
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        log("⚠ SLACK_WEBHOOK_URL 未設定（通知スキップ）")
        return
    try:
        import requests

        requests.post(webhook, json={"text": msg}, timeout=5)
        log("📤 Slack通知送信: " + msg)
    except Exception as e:
        log("❌ Slack通知失敗: " + str(e))


def pm2_register(name: str, path: str, cron: str = None):
    cron_opt = f'--cron "{cron}"' if cron else ""
    cmd = (
        f"pm2 delete {name} 2>/dev/null || true && "
        f"pm2 start \"bash -lc 'source {BASE}/.env; bash {path}'\" "
        f"--name {name} {cron_opt} && pm2 save"
    )
    subprocess.run(cmd, shell=True, check=False)
    log(f"⚙️ PM2登録完了: {name} ({path})")


def main():
    parser = argparse.ArgumentParser(description="WANSTAGE auto-intel generation with phases")
    parser.add_argument(
        "--phase",
        default="3",
        choices=["3", "4"],
        help="実行フェーズを指定 (3 または 4)",
    )
    args = parser.parse_args()

    phase = args.phase
    log(f"🚀 AUTO_INTEL_GEN 起動: フェーズ {phase}")

    if phase == "3":
        slack_notify("Phase 3 自動生成を開始しました")
        targets = [
            ("auto_macro_gen", f"{BASE}/core/auto_macro_gen.sh"),
            ("auto_patch_ui", f"{BASE}/core/auto_patch_ui.sh"),
        ]
        for name, path in targets:
            if os.path.exists(path):
                pm2_register(name, path, "*/10 * * * *")
                slack_notify(f"{name} をPM2登録しました ✅")
            else:
                log(f"⚠ スクリプトが見つかりません: {path}")
        slack_notify("Phase 3 自動化処理 完了 🎉")
        log("🏁 AUTO_INTEL_GEN Phase 3 完了")

    elif phase == "4":
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 AUTO_INTEL_GEN Phase 4 started"
        )
        script = os.path.join(BASE, "bin", "wan-autoheal-full.sh")
        if not Path(script).exists():
            print("⚠ 自動修復スクリプトが見つかりません:", script)
        else:
            subprocess.run(["chmod", "+x", script], check=False)
            subprocess.run(["pm2", "start", script, "--name", "wan-autoheal-full"], check=False)
            subprocess.run(["pm2", "save"], check=False)
            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚙️ PM2登録完了: wan-autoheal-full ({script})"
            )
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Slack通知統合済み")
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ ログ監視: ~/WANSTAGE/logs/autoheal.log"
        )
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🏁 AUTO_INTEL_GEN Phase 4 完了"
        )


if __name__ == "__main__":
    main()
