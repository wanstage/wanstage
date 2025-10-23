import json
import logging
import os
import sys

import requests

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

IG_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_BIZID = os.getenv("IG_BUSINESS_ACCOUNT_ID", "")


def _need(v: str, name: str):
    if not v:
        raise RuntimeError(f"missing env: {name}")


def post_image(image_url: str, caption: str) -> dict:
    _need(IG_TOKEN, "IG_ACCESS_TOKEN")
    _need(IG_BIZID, "IG_BUSINESS_ACCOUNT_ID")

    # Step1: メディア（コンテナ）作成
    url_media = f"https://graph.facebook.com/v21.0/{IG_BIZID}/media"
    r1 = requests.post(
        url_media,
        data={"image_url": image_url, "caption": caption, "access_token": IG_TOKEN},
    )
    j1 = r1.json()
    if r1.status_code != 200 or "id" not in j1:
        return {"ok": False, "step": "media", "status": r1.status_code, "resp": j1}
    creation_id = j1["id"]
    log.info("media created: %s", creation_id)

    # Step2: publish
    url_pub = f"https://graph.facebook.com/v21.0/{IG_BIZID}/media_publish"
    r2 = requests.post(url_pub, data={"creation_id": creation_id, "access_token": IG_TOKEN})
    j2 = r2.json()
    ok = r2.status_code == 200 and "id" in j2
    return {"ok": ok, "step": "publish", "status": r2.status_code, "resp": j2}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python3 ig_post.py <IMAGE_URL> <CAPTION>", file=sys.stderr)
        sys.exit(1)
    img, cap = sys.argv[1], " ".join(sys.argv[2:])
    out = post_image(img, cap)
    print(json.dumps(out, ensure_ascii=False, indent=2))
