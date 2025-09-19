import os, datetime as dt
from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest

load_dotenv()
prop = os.getenv("GA4_PROPERTY_ID")
cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
days = int(os.getenv("GA4_DAYS", "1"))

if not prop:
    raise SystemExit("GA4_PROPERTY_ID env is required")
if not cred or not os.path.isfile(cred):
    raise SystemExit("GOOGLE_APPLICATION_CREDENTIALS not found: %s" % cred)

client = BetaAnalyticsDataClient()
date_range = DateRange(start_date=f"{days}daysAgo", end_date="today")
metrics = [Metric(name=m) for m in ("activeUsers","newUsers","sessions","screenPageViews")]
req = RunReportRequest(property=f"properties/{prop}", date_ranges=[date_range], metrics=metrics)
res = client.run_report(req)

today = dt.date.today().isoformat()
print(f"[GA4 quick] days={days} as of {today}")
for m, cell in zip([m.name for m in metrics], res.rows[0].metric_values):
    print(f"  - {m}: {cell.value}")
