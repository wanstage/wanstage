#!/usr/bin/env python3
import os, json, pathlib

BASE = os.path.expanduser("~/WANSTAGE")
ENV_PATH = os.path.join(BASE, ".env")

def load_env_file():
    if not os.path.exists(ENV_PATH): return {}
    out = {}
    for line in pathlib.Path(ENV_PATH).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip().strip("'").strip('"')
    return out

def send_line(msg: str):
    # 1) 環境変数を最優先
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    to_user = os.getenv("LINE_TO_USER", "").strip()

    # 2) 無ければ .env を読む
    if not token or not to_user:
        envf = load_env_file()
        token = token or envf.get("LINE_CHANNEL_ACCESS_TOKEN","").strip()
        to_user = to_user or envf.get("LINE_TO_USER","").strip()

    debug = {
        "source": "env+file",
        "LINE_CHANNEL_ACCESS_TOKEN_len": len(token),
        "LINE_TO_USER_len": len(to_user),
        "module": __file__,
    }
    print(json.dumps({"debug": debug}, ensure_ascii=False))

    if not token or not to_user:
        return False, "LINE disabled (env missing)"

    try:
        import requests
    except Exception:
        return False, "requests not installed"

    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"to": to_user, "messages": [{"type": "text", "text": msg}]}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        return (r.status_code == 200), f"LINE status={r.status_code} body={r.text[:160]}"
    except Exception as e:
        return False, f"LINE err={e}"

if __name__ == "__main__":
    ok, log = send_line("test")
    print(json.dumps({"ok": ok, "log": log}, ensure_ascii=False))
