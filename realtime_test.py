import json
import os

import websocket
from dotenv import load_dotenv

# ✅ .env を明示的に読み込む
load_dotenv(os.path.expanduser("~/WANSTAGE/.env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise SystemExit("❌ OPENAI_API_KEY が見つかりません。~/WANSTAGE/.env を確認してください。")

url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
headers = ["Authorization: Bearer " + OPENAI_API_KEY, "OpenAI-Beta: realtime=v1"]


def on_open(ws):
    print("✅ Connected to OpenAI Realtime API")


def on_message(ws, message):
    data = json.loads(message)
    print("📩 Received:", json.dumps(data, indent=2))


ws = websocket.WebSocketApp(url, header=headers, on_open=on_open, on_message=on_message)
ws.run_forever()
