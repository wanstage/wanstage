#!/bin/bash
set -euo pipefail

BASE="$HOME/WANSTAGE"
BIN="$BASE/bin"
CORE="$BASE/core"
LOGS="$BASE/logs"
SETUP="$BASE/setup"

mkdir -p "$BIN" "$CORE" "$LOGS" "$SETUP"

# === 1. reaction_logger.py ===
cat <<'PYEOF' > "$CORE/reaction_logger.py"
import pandas as pd
import datetime

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
PYEOF

# === 2. notify_slack_flex.py ===
cat <<'PYEOF' > "$CORE/notify_slack_flex.py"
import os, json, requests

webhook = os.environ.get("SLACK_WEBHOOK_URL")
msg = {
  "blocks": [
    { "type": "section", "text": { "type": "mrkdwn", "text": "📊 *投稿の反応ログ通知*\n自動通知が完了しました。" } }
  ]
}
if webhook:
    r = requests.post(webhook, json=msg)
    print("✅ Slack通知送信済")
else:
    print("⚠️ Slack Webhook 未設定")
PYEOF

# === 3. sheets_uploader.py ===
cat <<'PYEOF' > "$CORE/sheets_uploader.py"
print("🔧 Google Sheets アップロード処理は未実装（ここに追加）")
PYEOF

# === 4. wan_phase8_all.sh ===
cat <<'SH' > "$BIN/wan_phase8_all.sh"
#!/bin/bash
set -euo pipefail

echo "=== 📊 Phase 8 実行開始 ==="
python3 ~/WANSTAGE/core/reaction_logger.py
python3 ~/WANSTAGE/core/notify_slack_flex.py
python3 ~/WANSTAGE/core/sheets_uploader.py
echo "✅ Phase 8 完了: $(date)"
SH
chmod +x "$BIN/wan_phase8_all.sh"

echo "✅ 生成完了: $BIN/wan_phase8_all.sh"
echo "▶️ 実行するには: bash $BIN/wan_phase8_all.sh"
