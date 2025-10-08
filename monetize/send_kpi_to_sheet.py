import os, json, datetime as dt, requests, gspread
from google.oauth2.service_account import Credentials

# --- env ---
SPREADSHEET_ID = os.environ.get("SHEET_ID", "<スプレッドシートID>")
SHEET_NAME = os.environ.get("SHEET_NAME", "KPI")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
SHORTENER_ORIGIN = os.getenv("SHORTENER_ORIGIN", "http://127.0.0.1:8000")
SHORTENER_ADMIN_TOKEN = os.getenv("SHORTENER_ADMIN_TOKEN", "set-me")

LAST = os.path.expanduser("~/WANSTAGE/logs/last_post.json")


def get_clicks(code: str) -> int:
    if not code:
        return 0
    try:
        r = requests.get(
            f"{SHORTENER_ORIGIN}/admin/stats",
            headers={"Authorization": f"Bearer {SHORTENER_ADMIN_TOKEN}"},
            params={"code": code},
            timeout=5,
        )
        r.raise_for_status()
        d = r.json()
        return int((d.get("stats") or {}).get("total", 0))
    except Exception as e:
        print("[kpi] clicks fetch failed:", e)
        return 0


def main():
    with open(LAST, encoding="utf-8") as f:
        last = json.load(f)

    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = last.get("text", "")
    long_url = last.get("long_url", "")
    short_url = last.get("short_url", "")
    code = last.get("short_code", "")

    clicks_total = get_clicks(code)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SHEET_NAME)

    row = [ts, text, long_url, short_url, code, clicks_total]
    ws.append_row(row, value_input_option="RAW")
    print("[OK] appended:", row)


if __name__ == "__main__":
    main()
