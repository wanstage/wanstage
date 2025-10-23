#!/usr/bin/env python3
import os


def main():
    user = os.getenv("IG_USERNAME", "").strip()
    pwd = os.getenv("IG_PASSWORD", "").strip()
    if not user or not pwd:
        print("[WARN] IG creds missing → skip auto post")
        return 0
    try:
        from instagrapi import Client
    except Exception as e:
        print(f"[WARN] instagrapi import failed: {e}")
        return 0
    cap = open(
        os.path.join(os.environ["HOME"], "WANSTAGE", "logs", "last_caption.txt"),
        encoding="utf-8",
    ).read()
    img = os.getenv("IG_IMAGE", "").strip() or None
    if not img or not os.path.exists(img):
        print("[WARN] image not found or unset → skip")
        return 0
    try:
        cl = Client()
        cl.login(user, pwd)
        res = cl.photo_upload(img, cap)
        shortcode = getattr(res, "shortcode", None)
        print("[OK] IG posted:", shortcode)
    except Exception as e:
        print(f"[WARN] IG post failed: {e}")
    return 0


if __name__ == "__main__":
    main()
