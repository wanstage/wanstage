#!/usr/bin/env bash
set -euo pipefail
LOG="$HOME/WANSTAGE/logs"
mkdir -p "$LOG"

# 1) Ensure UI(:8501) is running
if ! lsof -iTCP:8501 -sTCP:LISTEN >/dev/null 2>&1; then  # noqa: E701
  nohup "$HOME/WANSTAGE/.venv-runtime/bin/streamlit" run "$HOME/WANSTAGE/tmp/hello_streamlit.py" \
    --server.port 8501 --server.address 0.0.0.0 >> "$LOG/ui.log" 2>&1 &
  sleep 2
fi

# 2) Try ngrok first (if available)
pkill -f "ngrok http" 2>/dev/null || true
if command -v ngrok >/dev/null 2>&1; then
  nohup ngrok http http://localhost:8501 --log=stdout > "$LOG/ngrok.log" 2>&1 &
  sleep 2
  NGURL="$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[]?.public_url' | head -1 || true)"
else
  NGURL=""
fi

# 3) Fallback to Cloudflare Quick Tunnel if ngrok URL is empty
if [ -z "$NGURL" ]; then
  pkill -f "cloudflared tunnel --no-autoupdate --url" 2>/dev/null || true
  nohup /opt/homebrew/bin/cloudflared tunnel --no-autoupdate --url http://localhost:8501 \
    >> "$LOG/quick_tunnel_cloudflared.log" 2>&1 &
  URL=""
  for i in 1 2 3; do
    sleep 2
    URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG/quick_tunnel_cloudflared.log" | tail -1 || true)"
    [ -n "$URL" ] && break
  done
else
  URL="$NGURL"
fi

# 4) Open or dump logs on failure
if [ -n "$URL" ]; then
  echo "Public URL: $URL"
  printf "%s" "$URL" | pbcopy
  open "$URL"
else
  echo "Failed to expose UI"
  echo "== cloudflared log tail =="
  tail -n 60 "$LOG/quick_tunnel_cloudflared.log" 2>/dev/null || true
  exit 1
fi
