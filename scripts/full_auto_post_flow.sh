#!/usr/bin/env zsh
set -Eeuo pipefail
cd "$(dirname "$0")/.."

ts="$(date '+%F %T')"
mkdir -p logs out

echo "[$ts] Generate post..." | tee -a logs/full_auto.log
TEXT='作業効率アップ：今日やることを3つに絞って、まず1つだけ終わらせよう。#生産性 #継続'
printf "%s\n" "$TEXT" > out/last_post.json
echo "[$ts] done." | tee -a logs/full_auto.log

# Slack通知（任意）
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  payload=$(printf '{"text":"%s"}' "$TEXT")
  curl -fsS -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" || true
else
  echo "[slack] SKIP (SLACK_WEBHOOK_URL 未設定)"
fi

# 付随：gitleaks（任意・設定済なら）
if command -v gitleaks >/dev/null 2>&1 && [ -f .gitleaks.toml ]; then
  echo "[$(date '+%F %T')] gitleaks scan start" | tee -a logs/full_auto.log
  if gitleaks detect --config .gitleaks.toml --redact --no-banner; then
    echo "[$(date '+%F %T')] gitleaks exit=0" | tee -a logs/full_auto.log
  else
    echo "[$(date '+%F %T')] gitleaks exit=$?" | tee -a logs/full_auto.log
  fi
fi
