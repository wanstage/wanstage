#!/usr/bin/env python3
import csv
import datetime
import os
import random

CATS = ["dogs", "tech", "cats"]
CSV = os.path.join(os.environ["HOME"], "WANSTAGE", "logs", "revenue_log.csv")


def main():
    today = datetime.date.today().isoformat()
    rows = []
    for c in CATS:
        imp = random.randint(120, 480)
        ctr = 0.05
        cpc = 5.0
        clicks = round(imp * ctr)
        revenue = round(clicks * cpc, 2)
        rows.append([today, c, imp, clicks, ctr, cpc, revenue])
    newfile = not os.path.exists(CSV)
    with open(CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if newfile:
            w.writerow(["date", "category", "impressions", "clicks", "ctr", "cpc", "revenue"])
        w.writerows(rows)
    print(f"[OK] appended {len(rows)} rows -> {CSV}")


if __name__ == "__main__":
    main()
