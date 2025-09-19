import os, datetime as dt, json, urllib.request
from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest

load_dotenv()
prop  = os.getenv("GA4_PROPERTY_ID")
cred  = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
hook  = os.getenv("SLACK_WEBHOOK_URL")
days  = int(os.getenv("GA4_DAYS", "1"))

if not prop:  raise SystemExit("GA4_PROPERTY_ID env is required")
if not cred or not os.path.isfile(cred): raise SystemExit("GOOGLE_APPLICATION_CREDENTIALS not found")
if not hook:  raise SystemExit("SLACK_WEBHOOK_URL env is required")

client = BetaAnalyticsDataClient()
req = RunReportRequest(
    property=f"properties/{prop}",
    date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
    metrics=[Metric(name=m) for m in ("activeUsers","newUsers","sessions","screenPageViews")]
)
res = client.run_report(req)
vals = [mv.value for mv in res.rows[0].metric_values]
keys = ("activeUsers","newUsers","sessions","screenPageViews")
today = dt.date.today().isoformat()

text = "\n".join([
    f"*GA4 Daily* ({today}, last {days}d)",
    *[f"- {k}: {v}" for k,v in zip(keys, vals)]
])

data = json.dumps({"text": text}).encode()
req = urllib.request.Request(hook, data=data, headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=10) as r:
    print("[Slack] sent:", r.status)
