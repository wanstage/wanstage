import os, json
from dotenv import load_dotenv
from google.analytics.data_v1beta import (
    BetaAnalyticsDataClient,
    RunReportRequest,
    DateRange,
    Metric,
    Dimension,
)
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

BASE = os.path.expanduser("~/WANSTAGE")
CLIENT_JSON = os.path.join(BASE, "keys", "ga4-oauth.json")
TOKEN_PATH = os.path.join(BASE, "keys", "token-ga4.json")
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def load_pid() -> str:
    load_dotenv(os.path.join(BASE, ".env"))
    pid = os.getenv("GA4_PROPERTY_ID", "").strip()
    assert pid.isdigit(), f"GA4_PROPERTY_ID invalid: {pid!r}"
    return pid


def get_creds():
    # 既存トークンがあれば再利用
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.valid:
            return creds
    # なければブラウザで同意 → token 保存
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_JSON, SCOPES)
    creds = flow.run_local_server(port=0)  # 自動でブラウザ起動
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    return creds


def main():
    pid = load_pid()
    creds = get_creds()
    client = BetaAnalyticsDataClient(credentials=creds)

    req = RunReportRequest(
        property=f"properties/{pid}",
        date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
        metrics=[Metric(name="activeUsers")],
        dimensions=[Dimension(name="date")],
    )
    resp = client.run_report(req)
    print("row_count:", resp.row_count)
    for r in resp.rows[:7]:
        print(r.dimension_values[0].value, r.metric_values[0].value)


if __name__ == "__main__":
    main()
