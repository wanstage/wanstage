#!/usr/bin/env python3
import os
import sys

import requests

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")
CAPTION = os.getenv("CAPTION", "")


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


for k, v in {
    "IG_USER_ID": IG_USER_ID,
    "IG_ACCESS_TOKEN": ACCESS_TOKEN,
    "IMAGE_URL": IMAGE_URL,
}.items():
    if not v:
        die(f"[IG Graph] Missing env: {k}")


def post(url, **data):
    r = requests.post(url, data=data, timeout=30)
    try:
        j = r.json()
    except Exception:
        j = {"raw": r.text}
    if not r.ok:
        die(f"[IG Graph] HTTP {r.status_code}: {j}")
    return j


# 1) コンテナを作成
create = post(
    f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media",
    image_url=IMAGE_URL,
    caption=CAPTION,
    access_token=ACCESS_TOKEN,
)
container_id = create.get("id")
if not container_id:
    die(f"[IG Graph] no container id: {create}")

print("[IG Graph] container:", container_id)

# 2) 公開（publish）
pub = post(
    f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish",
    creation_id=container_id,
    access_token=ACCESS_TOKEN,
)
post_id = pub.get("id")
if not post_id:
    die(f"[IG Graph] publish failed: {pub}")

print("[IG Graph] published:", post_id)
