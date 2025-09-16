import gspread
from google.oauth2.service_account import Credentials

# Googleサービスアカウントの鍵ファイル（あなたのファイルに合わせてOK）
CREDS = "/Users/okayoshiyuki/WANSTAGE/google_credentials.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(CREDS, scopes=SCOPES)
gc = gspread.authorize(creds)

sh = gc.create("WANSTAGE Test Sheet")
print("作成完了:", sh.url)
