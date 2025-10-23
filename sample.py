import os

from slack_sdk import WebClient

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
auth = client.auth_test()
print("Slack OK:", auth["user"])
