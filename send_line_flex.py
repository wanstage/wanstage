#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import datetime
import pathlib
import requests

ROOT = pathlib.Path(__file__).resolve().parent
ENV = ROOT / ".env"
TEMPLATE = ROOT / "templates/flex_post.json"

def load_env(env_path: pathlib.Path):
    if not env_path.exists():
        sys.exit(f".env not found: {env_path}")
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.split('#', 1)[0].strip()
        v = v.split(None, 1)[0] if v else v
        os.environ[k.strip()] = v

def must_env(name: str) -> str:
    v = os.environ.get(name, "")
    if not v:
        sys.exit(f"ENV missing: {name}")
    # ASCII 強制（LINE のヘッダで化けないため）
    try:
        v.encode("ascii")
    except UnicodeEncodeError:
        sys.exit(f"ENV {name} must be ASCII only")
    return v

def render_flex(ctx: dict) -> dict:
    # テンプレがあれば使う。無ければ簡易 fallback テキスト
    if not TEMPLATE.exists():
        return {"type": "text", "text": f"{ctx['title']}\n{ctx['body']}"}

    raw = TEMPLATE.read_text(encoding="utf-8")
    # すごく単純な置換（{{ key }}）
    for k, v in ctx.items():
        raw = raw.replace("{{ "+k+" }}", str(v))
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # テンプレが壊れていたらテキストにフォールバック
        return {"type": "text", "text": f"{ctx['title']}\n{ctx['body']}"}

def post_line_push(token: str, payload: dict) -> requests.Response:
    s = requests.Session()
    s.trust_env = False  # 環境プロキシ無効
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return s.post("https://api.line.me/v2/bot/message/push",
                  headers=headers, data=data, timeout=15)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD （未指定は今日）")
    ap.add_argument("--slot", type=int, default=1)
    ap.add_argument("--force", action="store_true", help="履歴ガード等を使う場合に備えたダミー")
    args = ap.parse_args()

    load_env(ENV)
    token = must_env("LINE_CHANNEL_ACCESS_TOKEN")
    to = must_env("LINE_USER_ID")

    date_str = args.date or datetime.date.today().isoformat()

    # ここでは外部データに依存せず、最小の文面を自動生成（既存テンプレに流し込める形）
    ctx = {
        "title": f"WANSTAGE トピック {date_str[5:].replace('-', '/')} #{args.slot}",
        "date": date_str,
        "slot": args.slot,
        "body": f"{date_str} の自動送信テスト（slot {args.slot}）",
        "tags": "wanstage, auto, daily",
        "image": "https://picsum.photos/seed/wanstage/1024/576",
        "url": "https://example.com/wanstage",
    }

    message = render_flex(ctx)
    payload = {"to": to, "messages": [message]}

    r = post_line_push(token, payload)
    text = (r.text or "")[:400]
    print("STATUS", r.status_code, text)
    # 成否で終了コードを分ける（自動実行用）
    sys.exit(0 if 200 <= r.status_code < 300 else 1)

if __name__ == "__main__":
    main()
