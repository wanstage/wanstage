#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys

import requests


def main():
    p = argparse.ArgumentParser(description="Send an image message via LINE (raw HTTP).")
    p.add_argument("url", help="公開アクセス可能な画像URL (https://...)")
    p.add_argument(
        "--to",
        default=os.environ.get("LINE_USER_ID"),
        help="宛先（未指定は $LINE_USER_ID）",
    )
    p.add_argument("--dry-run", action="store_true", help="送らず内容だけ表示")
    args = p.parse_args()

    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        sys.exit("ERROR: LINE_CHANNEL_ACCESS_TOKEN が未設定です (.envrc / direnv を確認)")
    if not args.to:
        sys.exit("ERROR: 宛先が未設定です。--to か LINE_USER_ID を設定してください")

    if args.dry_run:
        print(f"[DRY-RUN] to={args.to} image={args.url}")
        return

    # プロキシ/UAなどの環境影響を無効化（latin-1事故回避）
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "USER_AGENT"):
        os.environ.pop(k, None)

    headers = {
        "Authorization": f"Bearer {token}",  # ASCIIのみ
        "Content-Type": "application/json",
        "User-Agent": "wanstage-linebot/1.0",  # ASCIIのみ
    }
    payload = {
        "to": args.to,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": args.url,
                "previewImageUrl": args.url,
            }
        ],
    }

    try:
        r = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=headers,
            data=json.dumps(payload),
            timeout=15,
        )
        if 200 <= r.status_code < 300:
            print("[send_line_image] ok:", args.url)
        else:
            print(
                f"[send_line_image] FAIL: status={r.status_code} body={r.text}",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:
        print(f"[send_line_image] FAIL: {e.__class__.__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
