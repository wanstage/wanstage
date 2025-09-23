from slack_sdk import WebClient
import os

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
auth = client.auth_test()
print("Slack OK:", auth["user"])
