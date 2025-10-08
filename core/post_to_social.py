#!/usr/bin/env python3
import json, sys

if len(sys.argv) < 2:
    print("usage: post_to_social.py <json>", file=sys.stderr)
    sys.exit(2)
data = json.load(open(sys.argv[1], encoding="utf-8"))
cap = (data.get("caption") or "").replace("\n", " ")[:60]
print(
    json.dumps(
        {
            "instagram": {"ok": True, "log": f"[instagram] posted '{cap}...'"},
            "tiktok": {"ok": True, "log": f"[tiktok] posted '{cap}...'"},
        },
        ensure_ascii=False,
    )
)
