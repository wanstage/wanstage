LOGS = "logs"
LOGS = "logs"
LOGS = "logs"
LOGS = "logs"
LOGS = "logs"
LOGS = "logs"
LOGS = "logs"
import pandas as pd

# ダミーデータ生成（本来はSNS API連携）
data = [
    {"post_id": "001", "likes": 34, "comments": 5, "views": 400},
    {"post_id": "002", "likes": 12, "comments": 2, "views": 180},
    {"post_id": "003", "likes": 0, "comments": 0, "views": 50},
]
df = pd.DataFrame(data)
log_path = f"{LOGS}/reaction_log.csv"
df.to_csv(log_path, index=False)
print(f"✅ 反応ログ作成: {log_path}")
