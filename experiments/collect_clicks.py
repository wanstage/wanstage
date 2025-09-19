#!/usr/bin/env python3
import csv
import json
import os
import re
import time
from urllib.parse import urlparse

import requests

BASE = os.path.expanduser("~/WANSTAGE")
LOGS = os.path.join(BASE, "logs")
SRC = os.path.join(LOGS, "last_post.json")
OUT = os.path.join(LOGS, "clicks_log.csv")

BITLY_TOKEN = os.environ.get("BITLY_TOKEN", "").strip()


def load_text():
    try:
        with open(SRC, encoding="utf-8") as f:
            j = json.load(f)
        return j.get("text", "")
    except Exception:
        return ""


def extract_urls(text):
    # 雑にURL抽出
    urls = re.findall(r'https?://[^\s)>\]"}]+', text)
    # 末尾の句読点/引用記号を落とす
    return [u.rstrip(".,)]}\"'") for u in urls]


def is_bitlink(u: str):
    try:
        host = urlparse(u).hostname or ""
        return host.endswith("bit.ly") or host.endswith("bitly.com") or host.endswith("j.mp")
    except Exception:
        return False


def bitly_clicks_24h(bitlink: str) -> int:
    """
    Bitly v4 clicks summary (last 24h)
    GET /v4/bitlinks/{bitlink}/clicks/summary?unit=day&units=1
    bitlink は "bit.ly/xxxx" の形で渡す（スキーマ無し）
    """
    if not BITLY_TOKEN:
        return 0
    parsed = urlparse(bitlink)
    # "domain/path" 形式へ
    if parsed.scheme:
        bit_id = f"{parsed.netloc}{parsed.path}"
    else:
        bit_id = bitlink
    url = f"https://api-ssl.bitly.com/v4/bitlinks/{bit_id}/clicks/summary"
    params = {"unit": "day", "units": 1}
    headers = {"Authorization": f"Bearer {BITLY_TOKEN}"}
    r = requests.get(url, headers=headers, params=params, timeout=20)
    if r.status_code != 200:
        return 0
    data = r.json()
    # {"total_clicks": N}
    return int(data.get("total_clicks", 0) or 0)


def main():
    os.makedirs(LOGS, exist_ok=True)

    text = load_text()
    urls = extract_urls(text)

    # Bitlyの短縮URLだけカウント
    bitlinks = [u for u in urls if is_bitlink(u)]
    total = 0
    for u in bitlinks[:5]:
        try:
            total += bitly_clicks_24h(u)
        except Exception:
            pass

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    newfile = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if newfile:
            w.writerow(["timestamp", "urls_count", "bitlinks_count", "clicks_24h"])
        w.writerow([ts, len(urls), len(bitlinks), total])

    print(
        f"[clicks] row appended: {ts} urls={len(urls)} bitlinks={len(bitlinks)} clicks_24h={total}"
    )


if __name__ == "__main__":
    main()
