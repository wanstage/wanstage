#!/usr/bin/env python3
import os
import socket
import sys

import requests
from requests.exceptions import RequestException

TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "").strip()


def can_resolve(h="notify-api.line.me"):
    try:
        socket.getaddrinfo(h, 443)
        return True
    except OSError:
        return False


def main(msg):
    if not TOKEN:
        print("[WARN] LINE token not set; skip")
        return 0
    if not can_resolve():
        print("[WARN] DNS NG for notify-api.line.me; skip")
        return 0
    try:
        r = requests.post(
            "///api/notify",
            headers={"Authorization": f"Bearer {TOKEN}"},
            data={"message": msg},
            timeout=10,
        )
        print("[OK] LINE notify" if r.status_code == 200 else f"[WARN] LINE status={r.status_code}")
        return 0
    except RequestException as e:
        print(f"[WARN] LINE notify error: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "WANSTAGE notification"))
