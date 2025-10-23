import os
import sys

print("[notion_upsert_ga4] dummy: set NOTION_TOKEN/NOTION_DB_ID and implement upsert later.")
print("NOTION_TOKEN set:", bool(os.getenv("NOTION_TOKEN")))
print("NOTION_DB_ID  set:", bool(os.getenv("NOTION_DB_ID")))
sys.exit(0)
