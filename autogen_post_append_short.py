import os, time, json, urllib.parse as up, requests

SHORTENER_ORIGIN = os.getenv("SHORTENER_ORIGIN", "http://127.0.0.1:8000")
SHORTENER_ADMIN_TOKEN = os.getenv("SHORTENER_ADMIN_TOKEN", "set-me")
LOGS = os.path.expanduser("~/WANSTAGE/logs")
os.makedirs(LOGS, exist_ok=True)
LAST = os.path.join(LOGS, "last_post.json")


def add_utm(url: str) -> str:
    pr = up.urlparse(url)
    qs = dict(up.parse_qsl(pr.query, keep_blank_values=True))
    if not any(k.startswith("utm_") for k in qs):
        qs.update(
            {
                "utm_source": "wanstage",
                "utm_medium": "social",
                "utm_campaign": time.strftime("post%Y%m%d"),
            }
        )
    return up.urlunparse(pr._replace(query=up.urlencode(qs)))


def shorten_url(long_url: str) -> tuple[str, str]:
    r = requests.post(
        f"{SHORTENER_ORIGIN}/admin/create",
        headers={"Authorization": f"Bearer {SHORTENER_ADMIN_TOKEN}"},
        json={"url": long_url},
        timeout=5,
    )
    r.raise_for_status()
    d = r.json()
    return d["code"], d.get("link") or d.get("shortUrl")


def main():
    # 例: 既存生成済み本文
    main_text = "今日の投稿タイトルと本文です。"
    product_url = "https://example.com/path"
    long_url = add_utm(product_url)

    try:
        code, short_url = shorten_url(long_url)
    except Exception as e:
        print("[shortener] skip:", e)
        code, short_url = None, None

    post_text = main_text + ("\nリンク: " + (short_url or long_url))
    last = {
        "text": post_text,
        "long_url": long_url,
        "short_url": short_url,
        "short_code": code,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(LAST, "w", encoding="utf-8") as f:
        json.dump(last, f, ensure_ascii=False, indent=2)

    print("[OK] wrote", LAST)
    print(post_text)


if __name__ == "__main__":
    main()
