import json
import os
import pathlib
import re
import time
import urllib.parse

import requests

P = os.path.expanduser("~/WANSTAGE/logs/last_post.json")
ORIGIN = os.getenv("SHORTENER_ORIGIN", "http://127.0.0.1:8000")
TOKEN = os.getenv("SHORTENER_ADMIN_TOKEN", "set-me")


def add_utm(u: str) -> str:
    pr = urllib.parse.urlparse(u)
    qs = dict(urllib.parse.parse_qsl(pr.query, keep_blank_values=True))
    if not any(k.startswith("utm_") for k in qs):
        qs.update(
            {
                "utm_source": "wanstage",
                "utm_medium": "social",
                "utm_campaign": time.strftime("post%Y%m%d"),
            }
        )
    return urllib.parse.urlunparse(pr._replace(query=urllib.parse.urlencode(qs)))


def find_urls(text: str) -> list[str]:
    return re.findall(r'https?://[^\s)>\]"}]+', text or "")


def shorten(long_url: str):
    r = requests.post(
        f"{ORIGIN}/admin/create",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"url": long_url},
        timeout=5,
    )
    r.raise_for_status()
    d = r.json()
    return d["code"], d["link"]


def main():
    if not pathlib.Path(P).exists():
        print("[upgrade] skip (no last_post.json)")
        return
    j = json.load(open(P, encoding="utf-8"))
    text = str(j.get("text", "")).strip()

    # 1) 本文からURLを抽出（なければ終了）
    urls = find_urls(text)
    if not urls:
        print("[upgrade] no URL in text; nothing to do")
        return
    base = urls[0]

    # 2) UTM を付与（既に付いていれば保持）
    long_url = add_utm(base)

    # 3) 短縮（失敗しても続行）
    short_code = j.get("short_code") or None
    short_url = j.get("short_url") or None
    if not short_url:
        try:
            short_code, short_url = shorten(long_url)
        except Exception as e:
            print("[upgrade] shortener failed:", e)

    # 4) 本文に短縮URLを併記（未記載なら追記）
    if short_url and short_url not in text:
        if "リンク:" in text or "http" in text:
            text = text + f"\nリンク: {short_url}"
        else:
            text = f"{text}\n{short_url}"

    # 5) JSON を拡張保存（既存キーは保持）
    j["text"] = text
    j.setdefault("long_url", long_url)
    if short_url:
        j["short_url"] = short_url
    if short_code:
        j["short_code"] = short_code
    j["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")

    tmp = P + ".tmp"
    json.dump(j, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, P)
    print(
        "[upgrade] ok:",
        {"short_url": j.get("short_url"), "short_code": j.get("short_code")},
    )


if __name__ == "__main__":
    main()
