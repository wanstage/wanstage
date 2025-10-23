#!/usr/bin/env python3
import json
import sys
import urllib.parse


def add_utm(url: str) -> str:
    if not url:
        return ""
    u = urllib.parse.urlparse(url)
    q = dict(urllib.parse.parse_qsl(u.query))
    q.update({"utm_source": "ig", "utm_medium": "social", "utm_campaign": "wanstage"})
    return urllib.parse.urlunparse(
        (u.scheme, u.netloc, u.path, u.params, urllib.parse.urlencode(q), u.fragment)
    )


raw = sys.stdin.read().strip()
src = json.loads(raw) if raw else {}
url = add_utm("https://example.com")
caption = (src.get("body", "") + "\n" + url).strip()
out = {**src, "caption": caption}
print(json.dumps(out, ensure_ascii=False))
