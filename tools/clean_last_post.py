import json
import os
import re
import time

p = os.path.expanduser("~/WANSTAGE/logs/last_post.json")
if not os.path.exists(p):
    print("[CLEAN] skip (no last_post.json)")
    raise SystemExit(0)

j = json.load(open(p, encoding="utf-8"))
t = (j.get("text") or "").strip()


def from_fenced_json(txt: str):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(1))
    except Exception:
        return None
    parts = []
    if obj.get("text"):
        parts.append(obj["text"].strip())
    bullets = obj.get("bullets") or []
    if isinstance(bullets, list):
        for b in bullets:
            s = str(b).strip()
            if s:
                parts.append("・" + s)
    if obj.get("hashtags"):
        parts.append(str(obj["hashtags"]).strip())
    return "\n".join([x for x in parts if x]).strip()


def strip_fences(txt: str):
    return re.sub(r"```.*?```", "", txt, flags=re.S).strip()


rebuilt = from_fenced_json(t)
t = rebuilt if rebuilt else strip_fences(t)

if not t:
    post_txt = os.path.expanduser("~/WANSTAGE/post_text.txt")
    if os.path.exists(post_txt):
        t = open(post_txt, encoding="utf-8").read().strip()
    if not t:
        t = f"小さく始めて、コツコツ続けよう。{time.strftime('%Y/%m/%d')} #学び #AI活用 #生産性"

j["text"] = t
json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False)
print("[CLEAN] text length:", len(t))
