#!/usr/bin/env python3
import json
import os
from datetime import datetime

import requests


def fetch_code_stats(keyword="AI"):
    url = f"https://api.github.com/search/code?q={keyword}"
    headers = {"Accept": "application/vnd.github+json"}
    r = requests.get(url, headers=headers)
    j = r.json()
    return {"keyword": keyword, "count": j.get("total_count", 0)}


if __name__ == "__main__":
    kw = os.getenv("CODE_KEYWORD", "AI")
    result = fetch_code_stats(kw)
    result["timestamp"] = datetime.now().isoformat()
    os.makedirs("logs", exist_ok=True)
    with open("logs/github_code_stats.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✅ Code search count: {result['count']}")
