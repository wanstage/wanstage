import os
import requests
from dotenv import load_dotenv

# .env の読み込み
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# 環境変数から取得
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
user_id = os.getenv("LINE_USER_ID")
greeting = os.getenv("GREETING", "こんにちは！")

# LINE Messaging API のエンドポイント
url = "https://api.line.me/v2/bot/message/push"

# ヘッダー
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {channel_access_token}"
}

# メッセージ本文
payload = {
    "to": user_id,
    "messages": [
        {
            "type": "text",
            "text": greeting
        }
    ]
}

# 送信
response = requests.post(url, headers=headers, json=payload)

# 結果を表示
print(f"Status Code: {response.status_code}")
print("Response:", response.json())

