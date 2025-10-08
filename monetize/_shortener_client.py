import os, requests

ORIGIN = os.getenv("SHORTENER_ORIGIN", "http://127.0.0.1:8000")
TOKEN = os.getenv("SHORTENER_ADMIN_TOKEN", "set-me")


def add_utm(url: str) -> str:
    import urllib.parse as up, time

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
        f"{ORIGIN}/admin/create",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={"url": long_url},
        timeout=5,
    )
    r.raise_for_status()
    d = r.json()
    return d["code"], d["link"]
