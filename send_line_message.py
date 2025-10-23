#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import uuid

import requests


def ensure_ascii_headers(h):
    # すべてのヘッダ値が ASCII か検査（非ASCIIを見つけたら即エラー）
    for k, v in h.items():
        try:
            (v if isinstance(v, str) else str(v)).encode("latin-1")
        except UnicodeEncodeError as e:
            raise SystemExit(f"HEADER-NOT-ASCII: {k}={v!r}  --> {e}")
    return h


def main():
    p = argparse.ArgumentParser(description="Send a LINE push message (raw HTTP).")
    p.add_argument(
        "--to",
        default=os.environ.get("LINE_USER_ID"),
        help="User ID (defaults to $LINE_USER_ID)",
    )
    p.add_argument("--text", required=True, help="Text message")
    p.add_argument("--dry-run", action="store_true", help="Send nothing, just print")
    args = p.parse_args()

    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        sys.exit("ERROR: LINE_CHANNEL_ACCESS_TOKEN が未設定です (.envrc を確認)")

    if not args.to:
        sys.exit("ERROR: 宛先が不明です。--to か LINE_USER_ID を設定してください")

    if args.dry_run:
        print(f"[DRY-RUN] to={args.to} text={args.text}")
        return

    headers = {
        "Authorization": f"Bearer {token}",  # ASCII
        "Content-Type": "application/json",  # ASCII
        "User-Agent": "wanstage-linebot/1.0",  # ASCII固定
        "X-Line-Retry-Key": str(uuid.uuid4()),  # ASCII
    }
    ensure_ascii_headers(headers)

    payload = {"to": args.to, "messages": [{"type": "text", "text": args.text}]}

    # 念のため proxies/環境UAを無効化（latin-1事故の温床）
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "USER_AGENT"):
        os.environ.pop(k, None)

    try:
        r = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=headers,
            json=payload,
            timeout=15,
        )
        if 200 <= r.status_code < 300:
            print("[send_line_message] ok:", args.to)
        else:
            print(
                f"[send_line_message] FAIL: status={r.status_code} body={r.text}",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:
        print(f"[send_line_message] FAIL: {e.__class__.__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
