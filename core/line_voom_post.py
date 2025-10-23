#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WANSTAGE_LINE_VOOM_POST
自動生成された投稿（画像＋本文）を LINE VOOM に投稿するモジュール
"""

import json
import os

import requests

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_TO_USER")
VOOM_ENDPOINT = "https://api.line.me/v2/bot/message/push"  # 暫定利用


def post_voom_message(text: str, image_path: str = None):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("❌ LINE設定が未登録です。環境変数を確認してください。")
        return False

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    if image_path and os.path.exists(image_path):
        message = [
            {
                "type": "image",
                "originalContentUrl": image_path,
                "previewImageUrl": image_path,
            },
            {"type": "text", "text": text},
        ]
    else:
        message = [{"type": "text", "text": text}]

    payload = {"to": LINE_USER_ID, "messages": message}
    res = requests.post(VOOM_ENDPOINT, headers=headers, data=json.dumps(payload))

    if res.status_code == 200:
        print("✅ LINE VOOM投稿成功")
        return True
    elif res.status_code == 429:
        print("⚠️ VOOM投稿制限に達しました。Slack通知へフォールバックします。")
        slack_notify(f"⚠️ VOOM上限 → Slack通知切替: {text[:50]}")
        return False
    else:
        print(f"❌ VOOM投稿失敗: {res.status_code} - {res.text}")
        return False


def slack_notify(msg: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if webhook:
        requests.post(webhook, json={"text": msg})


if __name__ == "__main__":
    sample_text = "📢 WANSTAGE自動投稿テスト：名古屋の街と犬の送迎日記"
    sample_image = f"{os.environ['HOME']}/WANSTAGE/media/sample.png"
    post_voom_message(sample_text, sample_image)
