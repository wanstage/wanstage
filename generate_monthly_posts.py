import argparse, json, calendar
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

def build(month:str, per_day:int):
    today = date.today()
    if month == "next":
        y,m = (today + relativedelta(months=+1)).year, (today + relativedelta(months=+1)).month
    elif month == "this":
        y,m = today.year, today.month
    else:
        y,m = map(int, month.split("-"))  # e.g. 2025-10

    days = calendar.monthrange(y,m)[1]
    posts=[]
    for d in range(1, days+1):
        base = date(y,m,d)
        for i in range(per_day):
            idx = (i+1)
            posts.append({
                "date": base.isoformat(),
                "slot": idx,
                "title": f"WANSTAGE トピック {base:%m/%d} #{idx}",
                "body":  f"{base:%Y-%m-%d} の自動生成コンテンツ（スロット{idx}）。",
                "tags":  ["wanstage","auto","daily"],
                "image": "https://picsum.photos/seed/{:04d}/1024/576".format(hash((y,m,d,idx))%10000),
                "url":   "https://example.com/post/{:08d}".format(abs(hash((y,m,d,idx)))%10**8),
                "channel": "TW,IG"
            })
    return posts

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--month", default="next", help='this | next | YYYY-MM')
    ap.add_argument("--per-day", type=int, default=3)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    posts=build(args.month, args.per_day)
    # JSON
    with open(args.out_json, "w") as f: json.dump(posts, f, ensure_ascii=False, indent=2)
    # CSV
    df=pd.DataFrame(posts)
    df.to_csv(args.out_csv, index=False)

if __name__=="__main__":
    main()
