#!/usr/bin/env python3
import json
import os
import sys
import urllib.parse

import yaml

cfg_path = os.path.join(os.environ["HOME"], "WANSTAGE", "config", "links.yaml")
if os.path.exists(cfg_path):
    cfg = yaml.safe_load(open(cfg_path))
else:
    cfg = {"utm": {}, "links": {}}

utm = cfg.get("utm", {})
links = cfg.get("links", {})

data = json.load(sys.stdin)
category = data.get("category", "")

key = (category + "_ai").lower().replace("-", "_")
base = links.get(key) or links.get(category) or ""

if base:
    u = urllib.parse.urlparse(base)
    q = dict(urllib.parse.parse_qsl(u.query))
    q.update(
        {
            "utm_source": utm.get("source", "ig"),
            "utm_medium": utm.get("medium", "social"),
            "utm_campaign": utm.get("campaign", "default"),
        }
    )
    base = urllib.parse.urlunparse(
        (u.scheme, u.netloc, u.path, u.params, urllib.parse.urlencode(q), u.fragment)
    )

body = data.get("body", "")
caption = body + "\n" + (base if base else "")

output = {
    "caption": caption,
    "image": data.get("image"),
    "category": category,
    "title": data.get("title"),
    "tags": data.get("tags"),
}
print(json.dumps(output, ensure_ascii=False))
