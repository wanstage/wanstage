import json
import os
import pathlib
import time

ROOT = pathlib.Path.home() / "WANSTAGE"
DB = ROOT / "python_src" / "usage_db.json"
os.makedirs(DB.parent, exist_ok=True)
data = {}
if DB.exists():
    try:
        data = json.loads(DB.read_text(encoding="utf-8") or "{}")
    except Exception:
        data = {}
# 日付が変わったら usage を全ユーザー 0 に
today = time.strftime("%Y-%m-%d")
for uid, rec in list(data.items()):
    if rec.get("date") != today:
        data[uid] = {"date": today, "count": 0, "plan": rec.get("plan", "free")}
DB.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("[quota] reset done:", today)
