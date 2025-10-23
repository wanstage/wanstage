#!/usr/bin/env python3
import json
import os

import requests


def send_line_message(text: str):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to_user = os.getenv("LINE_TO_USER")
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")

    if not token or not to_user:
        print("❌ 環境変数が不足しています")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"to": to_user, "messages": [{"type": "text", "text": text}]}

    res = requests.post(url, headers=headers, data=json.dumps(body))
    if res.status_code == 200:
        print("✅ LINE通知送信: 200 OK")
        return True
    elif res.status_code == 403:
        print(f"⚠️ LINE送信失敗（403 Forbidden）: {res.text}")
        if slack_webhook:
            fallback_msg = f"⚠️ LINE送信403 → Slackフォールバック通知: {text}"
            requests.post(slack_webhook, json={"text": fallback_msg})
            print("🔁 Slackにフォールバック送信完了 ✅")
        return False
    else:
        print(f"❌ LINE通知失敗: {res.status_code} - {res.text}")
        return False


if __name__ == "__main__":
    send_line_message("✅ WANSTAGE自動通知テスト：Slackフォールバック対応済み")
