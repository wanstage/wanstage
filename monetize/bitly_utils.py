import os
import sys

import requests

BITLY = os.getenv("BITLY_GENERIC_TOKEN", "")
API = "https://api-ssl.bitly.com/v4"
HEAD = {"Authorization": f"Bearer {BITLY}", "Content-Type": "application/json"} if BITLY else {}


def shorten(long_url):
    if not BITLY:
        return long_url
    r = requests.post(f"{API}/shorten", headers=HEAD, json={"long_url": long_url}, timeout=30)
    r.raise_for_status()
    return r.json().get("link", long_url)


def clicks(bitlink):
    if not BITLY:
        return 0
    link = bitlink.replace("https://", "").replace("http://", "")
    r = requests.get(f"{API}/bitlinks/{link}/clicks/summary", headers=HEAD, timeout=30)
    if r.status_code == 200:
        return r.json().get("total_clicks", 0)
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1]
    arg = sys.argv[2]
    if cmd == "shorten":
        print(shorten(arg))
    elif cmd == "clicks":
        print(clicks(arg))
