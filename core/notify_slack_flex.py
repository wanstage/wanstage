import os

import requests

webhook = os.environ.get("SLACK_WEBHOOK_URL")
msg = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📊 *投稿の反応ログ通知*\n自動通知が完了しました。",
            },
        }
    ]
}
if webhook:
    r = requests.post(webhook, json=msg)
    print("✅ Slack通知送信済")
else:
    print("⚠️ Slack Webhook 未設定")
