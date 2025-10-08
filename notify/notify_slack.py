#!/usr/bin/env python3
import os, json

try:
    import requests
except Exception:

    def send_slack(msg: str):
        return False, "requests not installed"

else:

    def send_slack(msg: str):
        url = os.getenv("SLACK_WEBHOOK_URL", "").strip()
        if not url:
            return False, "Slack disabled"
        try:
            r = requests.post(url, json={"text": msg}, timeout=10)
            return (r.status_code in (200, 204)), f"Slack status={r.status_code}"
        except Exception as e:
            return False, f"Slack err={e}"


if __name__ == "__main__":
    ok, log = send_slack("test")
    print(json.dumps({"ok": ok, "log": log}, ensure_ascii=False))
