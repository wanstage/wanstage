#!/usr/bin/env bash
unset BASH_ENV
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cd "$HOME/WANSTAGE"

mkdir -p logs
ts="$(date +%F_%H%M%S)"
log="logs/gitleaks_${ts}.log"

echo "[$(date '+%F %T')] gitleaks scan start" | tee -a "$log"
if gitleaks detect --config .gitleaks.toml --redact --no-banner | tee -a "$log"; then
  status=0
else
  status=$?
fi
echo "[$(date '+%F %T')] gitleaks exit=$status" | tee -a "$log"

# Slack 通知（任意）
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
  text="gitleaks exit=${status} (${ts})"
  curl -s -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"${text}\"}" \
    "$SLACK_WEBHOOK_URL" >/dev/null || true
fi

exit 0
