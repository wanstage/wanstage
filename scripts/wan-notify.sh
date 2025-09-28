#!/usr/bin/env zsh
set -euo pipefail

# .env を読む（存在すれば）
if [ -f ".env" ]; then
  set -a; . ./.env; set +a
fi

log="logs/notify.log"; mkdir -p "$(dirname "$log")"
ts="$(date '+%Y-%m-%d %H:%M:%S')"
app="WANSTAGE"

msg="${1:-"(no message)"}"
url="${2:-""}"

# マスク表示用
mask_url() {
  # Webhook URL 等を見せない（ホストだけ）
  printf '%s' "$1" | sed -E 's#(https?://[^/]+)/.*#\1 (sent masked)#'
}

echo "[NOTIFY] $ts $msg ${url}" | tee -a "$log"

# --- Slack ---
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  payload=$(printf '{"text":"[%s] %s %s"}' "$app" "$msg" "$url")
  if curl -fsS -X POST -H 'Content-type: application/json' \
      --data "$payload" "$SLACK_WEBHOOK_URL" >/dev/null; then
    echo "ok[SLACK] $ts $msg ${url}" | tee -a "$log"
    echo "[SLACK] $ts $(mask_url "$SLACK_WEBHOOK_URL")" >>"$log"
  else
    echo "ng[SLACK] $ts $msg ${url}" | tee -a "$log"
  fi
fi

# --- LINE（Cloudflare Worker 経由・任意）---
# WORKER_URL が設定されていれば、そこへ投げる（DNS問題のバイパスにも使える）
if [ -n "${WORKER_URL:-}" ]; then
  if curl -fsS -X POST "$WORKER_URL" \
      -F "message=${msg} ${url}" >/dev/null; then
    echo "ok[LINE] $ts $msg ${url}" | tee -a "$log"
  else
    echo "ng[LINE] $ts $msg ${url}" | tee -a "$log"
  fi
else
  echo "[LINE]  $ts skip (worker unreachable) $msg ${url}" >>"$log"
fi

# --- Zapier（任意）---
if [ -n "${ZAP_WEBHOOK_URL:-}" ]; then
  zp=$(printf '{"msg":"%s","url":"%s"}' "$msg" "$url")
  if curl -fsS -X POST "$ZAP_WEBHOOK_URL" \
        -H 'content-type: application/json' \
        --data "$zp" >/dev/null; then
    echo "[ZAP]   $ts sent" >>"$log"
  else
    echo "[ZAP]   $ts NG" >>"$log"
  fi
fi

# ローカル記録
echo "[LOCAL] $ts $msg ${url} (SLACK=$([ -n "${SLACK_WEBHOOK_URL:-}" ] && echo set || echo unset) LINE=$([ -n "${WORKER_URL:-}" ] && echo set || echo unset))" >>"$log"
