#!/usr/bin/env python3
import json, datetime, os

data = {
    "title": f"WANSTAGE Post {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "body": "自動生成されたサンプル投稿本文です。",
    "image": os.path.expanduser("~/WANSTAGE/media/sample.png"),
    "category": "default",
    "tags": ["wanstage", "auto", "test"],
}
print(json.dumps(data, ensure_ascii=False))
