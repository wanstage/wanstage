import json
import os
import subprocess
import urllib.request


def notify_zapier(text: str, title: str = "WANSTAGE"):
    url = os.environ.get("ZAPIER_WEBHOOK_URL", "")
    if not url:
        return False, "no_zapier_webhook"
    try:
        data = json.dumps({"text": text, "title": title}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return (200 <= r.status < 300), f"HTTP{r.status}"
    except Exception as e:
        return False, str(e)


def notify(text: str, title: str = "WANSTAGE"):
    # 1) wan-notify があればそれを優先（あなたの環境に最適化済み）
    wn = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin", "wan-notify")
    if os.path.exists(wn) and os.access(wn, os.X_OK):
        try:
            subprocess.run([wn, text, title], check=False)
            return True, "wan-notify"
        except Exception:
            pass
    # 2) 直接 Zapier
    ok, info = notify_zapier(text, title)
    return ok, info
