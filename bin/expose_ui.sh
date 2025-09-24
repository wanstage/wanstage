#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/WANSTAGE/logs"
mkdir -p "$LOG_DIR"
UI_LOG="$LOG_DIR/ui.log"
NGROK_LOG="$LOG_DIR/ngrok.log"
CF_LOG="$LOG_DIR/quick_tunnel_cloudflared.log"
PID_DIR="$LOG_DIR/pids"
mkdir -p "$PID_DIR"

# ▼設定
PORT="${PORT:-8501}"
APP="${APP:-$HOME/WANSTAGE/tmp/hello_streamlit.py}"
OPEN_BROWSER="${OPEN_BROWSER:-1}"     # 0で自動オープン抑止
HEALTH_PATH="${HEALTH_PATH:-/}"       # /health があればそこに変更
TIMEOUT_SEC="${TIMEOUT_SEC:-60}"      # トンネル取得タイムアウト(合計)

# ▼ユーティリティ
say_log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
have(){ command -v "$1" >/dev/null 2>&1; }

notify_slack(){
  local text="$1"
  if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -sS -X POST "$SLACK_WEBHOOK_URL" -H 'content-type: application/json' \
      --data "$(printf '{"text":"%s"}' "$text")" >/dev/null || true
  fi
}

wait_port(){
  local p=$1; local t=${2:-15}; local i=0
  until lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; do
    i=$((i+1)); [ $i -ge $t ] && return 1
    sleep 1
  done
}

curl_ok(){
  curl -fsS --max-time 5 "$1" >/dev/null 2>&1
}

# ▼UI(8501)起動（なければ最小のStreamlitを作る）
if [ ! -f "$APP" ]; then
  cat > "$APP" <<'PY'
import streamlit as st
st.set_page_config(page_title="WANSTAGE UI", layout="wide")
st.title("WANSTAGE UI")
st.write("Hello from Streamlit!")
PY
fi

if ! wait_port "$PORT" 1; then
  say_log "starting Streamlit UI on :$PORT"
  if [ -x "$HOME/WANSTAGE/.venv-runtime/bin/streamlit" ]; then
    UI_BIN="$HOME/WANSTAGE/.venv-runtime/bin/streamlit"
  else
    UI_BIN="$(command -v streamlit || true)"
  fi
  if [ -z "$UI_BIN" ]; then
    say_log "❌ streamlit が見つかりません。venv を有効化するか、pip install streamlit を実行してください。"
    exit 1
  fi
  nohup "$UI_BIN" run "$APP" --server.port "$PORT" --server.address 0.0.0.0 >>"$UI_LOG" 2>&1 &
  echo $! > "$PID_DIR/ui.pid"
fi

# UI疎通待ち
if ! wait_port "$PORT" 30; then
  say_log "❌ UIのポート :$PORT がLISTENしません。logs/ui.log を確認してください。"
  exit 1
fi

# ▼ngrok優先でトンネル取得（自分が起動したngrokだけ管理）
TUN_URL=""
if have ngrok; then
  say_log "trying ngrok"
  # 既存の自前ngrokを止める
  if [ -f "$PID_DIR/ngrok.pid" ] && kill -0 "$(cat "$PID_DIR/ngrok.pid")" 2>/dev/null; then
    kill "$(cat "$PID_DIR/ngrok.pid")" 2>/dev/null || true
    sleep 1
  fi
  # ngrok v3 はローカルAPIが :4040 で立つ
  nohup ngrok http "http://localhost:${PORT}" --log=stdout >"$NGROK_LOG" 2>&1 &
  echo $! > "$PID_DIR/ngrok.pid"

  # URL待ち
  for _ in $(seq 1 $TIMEOUT_SEC); do
    TUN_URL="$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[]?.public_url' 2>/dev/null | head -1 || true)"
    [ -n "$TUN_URL" ] && break
    sleep 1
  done
fi

# ▼Cloudflare Quick Tunnelにフォールバック（自分が起動したcloudflaredのみ管理）
if [ -z "$TUN_URL" ]; then
  if ! have cloudflared; then
    say_log "ngrok失敗 & cloudflared未インストール → brew install cloudflared を検討"
  else
    say_log "trying Cloudflare Quick Tunnel"
    if [ -f "$PID_DIR/cloudflared.pid" ] && kill -0 "$(cat "$PID_DIR/cloudflared.pid")" 2>/dev/null; then
      kill "$(cat "$PID_DIR/cloudflared.pid")" 2>/dev/null || true
      sleep 1
    fi
    : > "$CF_LOG"
    nohup cloudflared tunnel --no-autoupdate --url "http://localhost:${PORT}" >>"$CF_LOG" 2>&1 &
    echo $! > "$PID_DIR/cloudflared.pid"

    for _ in $(seq 1 $TIMEOUT_SEC); do
      TUN_URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$CF_LOG" | tail -1 || true)"
      [ -n "$TUN_URL" ] && break
      sleep 1
    done
  fi
fi

# ▼結果
if [ -n "$TUN_URL" ]; then
  # ヘルス確認
  HEALTH_URL="${TUN_URL%/}${HEALTH_PATH}"
  if curl_ok "$HEALTH_URL"; then
    say_log "✅ Public URL: $TUN_URL (health OK: $HEALTH_PATH)"
  else
    say_log "⚠ Public URL: $TUN_URL ただし $HEALTH_PATH は200系で応答せず（UIは生きてる可能性あり）"
  fi
  # クリップボード/ブラウザ/Slack
  command -v pbcopy >/dev/null 2>&1 && printf "%s" "$TUN_URL" | pbcopy || true
  [ "$OPEN_BROWSER" = "1" ] && open "$TUN_URL" 2>/dev/null || true
  notify_slack "[WANSTAGE] UI exposed: $TUN_URL"
  echo "$TUN_URL"
  exit 0
else
  say_log "❌ 公開URLの取得に失敗しました"
  echo "== tail ngrok =="
  tail -n 60 "$NGROK_LOG" 2>/dev/null || true
  echo "== tail cloudflared =="
  tail -n 60 "$CF_LOG" 2>/dev/null || true
  notify_slack "[WANSTAGE] UI expose FAILED"
  exit 1
fi
