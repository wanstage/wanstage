#!/usr/bin/env python3
import os, json, datetime

PROMPT = os.environ.get("POST_PROMPT", "今日のAIトピックを紹介")
cat = os.environ.get("POST_CATEGORY", "tech")
media = os.path.join(os.environ["HOME"], "WANSTAGE", "media", "sample.png")
out = {
    "title": PROMPT[:40],
    "body": f"{PROMPT}\\n#AI #daily",
    "category": cat,
    "image": media,
    "tags": ["AI", "daily"],
}
print(json.dumps(out, ensure_ascii=False))
