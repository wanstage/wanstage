#!/usr/bin/env python3
import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def fetch_trending(language="python"):
    url = f"https://github.com/trending/{language}?since=daily"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    data = []
    for repo in soup.select("article.Box-row"):
        name = repo.h2.a["href"].strip("/")
        desc = repo.p.text.strip() if repo.p else ""
        stars = repo.select_one("a[href*='/stargazers']").text.strip()
        data.append({"repo": name, "desc": desc, "stars": stars})
    return data


if __name__ == "__main__":
    lang = os.getenv("TREND_LANG", "python")
    trending = fetch_trending(lang)
    out = {"timestamp": datetime.now().isoformat(), "language": lang, "data": trending}
    os.makedirs("logs", exist_ok=True)
    with open("logs/github_trending.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"✅ Trending fetched: {len(trending)} repos")
