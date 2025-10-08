import os, time, urllib.parse as _up, requests

SHORTENER_ORIGIN = os.getenv("SHORTENER_ORIGIN", "http://127.0.0.1:8000")
SHORTENER_ADMIN_TOKEN = os.getenv("SHORTENER_ADMIN_TOKEN", "set-me")


def add_utm(url: str) -> str:
    try:
        pr = _up.urlparse(url)
        qs = dict(_up.parse_qsl(pr.query, keep_blank_values=True))
        if not any(k.startswith("utm_") for k in qs):
            qs.update(
                {
                    "utm_source": "wanstage",
                    "utm_medium": "social",
                    "utm_campaign": time.strftime("post%Y%m%d"),
                }
            )
        return _up.urlunparse(pr._replace(query=_up.urlencode(qs)))
    except Exception:
        return url


def shorten_url(long_url: str) -> tuple[str, str]:
    """自前短縮APIで (code, short_url) を返す。失敗時は例外送出。"""
    r = requests.post(
        f"{SHORTENER_ORIGIN}/admin/create",
        headers={"Authorization": f"Bearer {SHORTENER_ADMIN_TOKEN}"},
        json={"url": long_url},
        timeout=5,
    )
    r.raise_for_status()
    d = r.json()
    return d["code"], d["link"]
