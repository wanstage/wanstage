import csv
import json
import os
import random
import time
from pathlib import Path

LOG = Path(os.path.expanduser("~/WANSTAGE/logs/ab_log.csv"))
LOG.parent.mkdir(parents=True, exist_ok=True)
variants = {
    "cta": ["👉 続きはプロフのリンクから", "🔗 今すぐチェック"],
    "link_label": ["おすすめはこちら", "詳細＆特典はこちら"],
}


def pick(seed=None):
    random.seed(seed or int(time.time()) // 3600)  # 1hごとに切替
    choice = {k: random.choice(v) for k, v in variants.items()}
    choice["variant_id"] = "A" if list(variants.values())[0].index(choice["cta"]) == 0 else "B"
    return choice


def log(platform, choice, dest_url):
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ts", "platform", "variant_id", "cta", "link_label", "url"])
        w.writerow(
            [
                time.strftime("%F %T"),
                platform,
                choice["variant_id"],
                choice["cta"],
                choice["link_label"],
                dest_url,
            ]
        )


if __name__ == "__main__":
    import sys

    platform = sys.argv[1] if len(sys.argv) > 1 else "multi"
    url = sys.argv[2] if len(sys.argv) > 2 else ""
    c = pick()
    log(platform, c, url)
    print(json.dumps(c, ensure_ascii=False))
