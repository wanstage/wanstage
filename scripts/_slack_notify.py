import os, json, ssl, urllib.request

try:
    import certifi

    ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    ctx = ssl.create_default_context()

p = os.path.expanduser("~/WANSTAGE/logs/last_post.json")
j = json.load(open(p, encoding="utf-8"))
msg = j.get("text", "").strip() or "（本文なし）"
wh = os.environ.get("SLACK_WEBHOOK_URL")
if wh:
    data = json.dumps({"text": msg}).encode("utf-8")
    req = urllib.request.Request(wh, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        print("[slack] status:", r.status)
else:
    print("[slack] SKIP (SLACK_WEBHOOK_URL 未設定)")
