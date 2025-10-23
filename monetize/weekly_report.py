import datetime as dt
import os

import gspread
import requests
from google.oauth2.service_account import Credentials

SHEET_ID = os.environ["SHEET_ID"]
SHEET_NAME = os.environ.get("SHEET_NAME", "KPI")
WEBHOOK = os.environ["SLACK_WEBHOOK_URL"]


def load_rows():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=scopes
    )
    ws = gspread.authorize(creds).open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    return ws.get_all_values()  # 1行目ヘッダ想定


def parse_rows(rows):
    # ヘッダ: [ts, text, long, short, code, total, byDayJson]
    head, *data = rows
    now = dt.datetime.now()
    since = now - dt.timedelta(days=7)
    w_total = 0
    top = []  # (clicks, short, text[:60])
    by_campaign = {}  # utm_campaign -> clicks

    for r in data:
        if len(r) < 7:
            continue
        ts, text, long_url, short_url, code, total, byday = r[:7]
        # 週次フィルタ（日時列はログ作成時刻、緩めに当週相当で集計）
        try:
            t = dt.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if t < since:
            continue

        clicks = int(total or 0)
        w_total += clicks
        top.append((clicks, short_url, (text or "")[:60].replace("\n", " ")))

        # utm_campaign 集計（簡易抽出）
        camp = ""
        if "utm_campaign=" in (long_url or ""):
            try:
                from urllib.parse import parse_qs, urlparse

                qs = parse_qs(urlparse(long_url).query)
                camp = (qs.get("utm_campaign") or [""])[0]
            except Exception:
                pass
        by_campaign[camp] = by_campaign.get(camp, 0) + clicks

    top = sorted(top, reverse=True)[:5]
    camp_sorted = sorted(by_campaign.items(), key=lambda x: x[1], reverse=True)
    return w_total, top, camp_sorted


def post_to_slack(total, top, camp_sorted):
    lines = []
    lines.append(f"*週次クリック合計*: *{total}*")
    if camp_sorted:
        lines.append("*キャンペーン別トップ*")
        for name, n in camp_sorted[:5]:
            lines.append(f"• `{name or '-'}:` {n}")
    if top:
        lines.append("*リンク別トップ*")
        for n, short, text in top:
            lines.append(f"• {n} クリック | {short} | {text}")
    text = "\n".join(lines) if lines else "データがありませんでした。"
    r = requests.post(WEBHOOK, json={"text": text}, timeout=5)
    r.raise_for_status()
    print("[OK] posted weekly report")


def main():
    rows = load_rows()
    total, top, camp_sorted = parse_rows(rows)
    post_to_slack(total, top, camp_sorted)


if __name__ == "__main__":
    main()
