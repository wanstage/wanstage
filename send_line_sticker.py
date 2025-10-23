#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys

import requests


def main():
    p = argparse.ArgumentParser(description="Send a sticker via LINE (raw HTTP).")
    p.add_argument("--package", default="11539", help="packageId")
    p.add_argument("--sticker", default="52114136", help="stickerId")
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
        print(f"[DRY-RUN] to={args.to} packageId={args.package} stickerId={args.sticker}")
        return

    # 環境影響の遮断
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "USER_AGENT"):
        os.environ.pop(k, None)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "wanstage-linebot/1.0",
    }
    payload = {
        "to": args.to,
        "messages": [
            {
                "type": "sticker",
                "packageId": str(args.package),
                "stickerId": str(args.sticker),
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
            print(f"[send_line_sticker] ok: packageId={args.package} stickerId={args.sticker}")
        else:
            print(
                f"[send_line_sticker] FAIL: status={r.status_code} body={r.text}",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:
        print(f"[send_line_sticker] FAIL: {e.__class__.__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
