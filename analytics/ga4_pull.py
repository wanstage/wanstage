import csv
import datetime
import os

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)

PROP = os.environ.get("GA4_PROPERTY_ID")  # 例: "123456789"
if not PROP:
    raise SystemExit("GA4_PROPERTY_ID env is required")


def run(days=1):
    client = BetaAnalyticsDataClient()  # GOOGLE_APPLICATION_CREDENTIALS を参照
    date_range = DateRange(
        start_date=(datetime.date.today() - datetime.timedelta(days=days)).isoformat(),
        end_date=datetime.date.today().isoformat(),
    )
    req = RunReportRequest(
        property=f"properties/{PROP}",
        dimensions=[
            Dimension(name="sessionSource"),
            Dimension(name="sessionMedium"),
            Dimension(name="campaign"),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="screenPageViews"),
            Metric(name="eventCount"),
            Metric(name="conversions"),
        ],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="sessionSource",
                string_filter=Filter.StringFilter(value="wanstage"),
            )
        ),
    )
    res = client.run_report(req)

    rows = []
    for r in res.rows:
        rows.append(
            {
                "date": datetime.date.today().isoformat(),
                "source": r.dimension_values[0].value,
                "medium": r.dimension_values[1].value,
                "campaign": r.dimension_values[2].value,
                "sessions": int(r.metric_values[0].value or 0),
                "users": int(r.metric_values[1].value or 0),
                "views": int(r.metric_values[2].value or 0),
                "events": int(r.metric_values[3].value or 0),
                "conversions": int(r.metric_values[4].value or 0),
            }
        )

    # ログCSVへ追記
    out = os.path.expanduser("~/WANSTAGE/logs/ga4_wanstage.csv")
    newfile = not os.path.exists(out)
    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=(
                list(rows[0].keys())
                if rows
                else [
                    "date",
                    "source",
                    "medium",
                    "campaign",
                    "sessions",
                    "users",
                    "views",
                    "events",
                    "conversions",
                ]
            ),
        )
        if newfile:
            w.writeheader()
        for row in rows:
            w.writerow(row)

    # 標準出力にもサマリ
    if rows:
        total = {
            "sessions": sum(r["sessions"] for r in rows),
            "users": sum(r["users"] for r in rows),
            "views": sum(r["views"] for r in rows),
            "events": sum(r["events"] for r in rows),
            "conversions": sum(r["conversions"] for r in rows),
        }
        print("[GA4] rows:", len(rows), "total:", total)
    else:
        print("[GA4] No rows (check filters / dates)")


if __name__ == "__main__":
    run(days=int(os.environ.get("GA4_DAYS", "1")))
