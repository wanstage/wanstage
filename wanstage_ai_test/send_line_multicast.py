import os

import requests
from dotenv import load_dotenv

# .envファイル読み込み
load_dotenv()

access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
message = os.getenv("GREETING", "こんにちは！")

# 複数のユーザーIDをここに設定
user_ids = [
    "F97C6S26FC",
    "6QSX8WEPWR",
    "GWQUXTTNZV",
    "EGUZM5RU2G",
    "S83KTER6MV",
    "FYQCESQ4WN",
    "HC5348TX4N",
    "FGAH6PZ8X3",
    "2JBXWSD5R2",
    "6J4CNUPQHQ",
]

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}",
}

# 各ユーザーにメッセージ送信
for user_id in user_ids:
    payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    response = requests.post(
        "https://api.line.me/v2/bot/message/push", headers=headers, json=payload
    )
    print(f"{user_id} → {response.status_code}: {response.text}")
