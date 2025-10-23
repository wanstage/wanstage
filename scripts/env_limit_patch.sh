#!/bin/zsh
set -eu
set -o pipefail

ENV_FILE="$HOME/WANSTAGE/.env"
BACKUP_FILE="$HOME/WANSTAGE/.env.bak_$(date +%Y%m%d_%H%M%S)"

echo "=== 🧭 WANSTAGE課金制御版 .env 自動生成 ==="
cp "$ENV_FILE" "$BACKUP_FILE"
echo "🗂 バックアップを作成: $BACKUP_FILE"

cat <<'EOF' >> "$ENV_FILE"

# === WANSTAGE API構成（課金制御版） ===
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
WAN_AI_MODEL="gpt-4o-mini"
WAN_AI_TEMPERATURE=0.8

# --- 料金制御設定 ---
WAN_MAX_TOKENS_PER_MIN=8000
WAN_MONTHLY_TOKEN_LIMIT=1000000
WAN_BILLING_ALERT="on"

# --- 画像生成 ---
WAN_IMAGE_GEN="dall-e-3-mini"
WAN_IMAGE_SIZE="1024x1024"

# --- 通知・ログ ---
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXXX/XXXX/XXXX"
LINE_NOTIFY_FALLBACK="on"
LOG_DIR="$HOME/WANSTAGE/logs"

# --- ローカル出力 ---
OUT_DIR="$HOME/WANSTAGE/out/insta"
DB_PATH="$HOME/WANSTAGE/post_log.sqlite3"

EOF

echo "✅ .env に課金制御構成を追記しました。"
echo "👉 既存のキーは保持済み。Slack通知・LINE設定はそのまま使えます。"
