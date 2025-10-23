#!/usr/bin/env python3
import csv
import os
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

BASE = os.path.expanduser("~/WANSTAGE")
LOG_PATH = f"{BASE}/logs/post_log.csv"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
if not SHEET_ID:
    print("[WARN] GOOGLE_SHEET_ID not set — skipping Sheets sync.")
    exit(0)


def upload_to_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(f"{BASE}/service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        sheet.clear()
        sheet.append_rows(reader)
    print(f"[OK] Synced to Google Sheets at {datetime.now()}")


if __name__ == "__main__":
    upload_to_sheets()
