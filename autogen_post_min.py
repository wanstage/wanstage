import os, time, json, urllib.parse as up, requests

SHORTENER_ORIGIN = os.getenv("SHORTENER_ORIGIN", "http://127.0.0.1:3000")
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
        f"{SHORTENER_ORIGIN}/api/shorten",
        json={"url": long_url},
        timeout=5,
    )
    r.raise_for_status()
    d = r.json()
    return d["code"], d.get("shortUrl") or d.get("link")


def save_last_post(obj: dict):
    with open(LAST, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    # ←ここをあなたの実データに合わせて組み込む
    main_text = "今日の投稿タイトルと本文です。"
    product_url = "https://example.com/path"

    long_url = add_utm(product_url)

    short_code, short_url = None, None
    try:
        short_code, short_url = shorten_url(long_url)
    except Exception as e:
        print("[shortener] fallback to long url:", e)

    post_text = "\n".join([x for x in [main_text, f"リンク: {short_url or long_url}"] if x])

    save_last_post(
        {
            "text": post_text,
            "long_url": long_url,
            "short_url": short_url,
            "short_code": short_code,
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    print("[OK] wrote", LAST)
    print(post_text)


if __name__ == "__main__":
    main()
