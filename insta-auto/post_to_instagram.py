import os
import time

import requests
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv()

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")


def create_media(image_url, caption):
    """投稿用のメディアを作成する"""
    url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN,
    }
    r = requests.post(url, params=params)
    r.raise_for_status()
    return r.json()["id"]


def publish_media(creation_id):
    """作成したメディアを公開する"""
    url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    params = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN,
    }
    r = requests.post(url, params=params)
    r.raise_for_status()
    return r.json()["id"]


if __name__ == "__main__":
    # サンプル：プレースホルダー画像を投稿
    image_url = "https://via.placeholder.com/1080.jpg"
    caption = "✅ 自動投稿テスト #wanstage #自動投稿"

    print("▶️ Instagram 投稿開始")
    cid = create_media(image_url, caption)
    print("creation_id:", cid)

    time.sleep(3)  # 投稿反映の待機
    post_id = publish_media(cid)
    print("published post id:", post_id)
    print("✅ 投稿完了")
