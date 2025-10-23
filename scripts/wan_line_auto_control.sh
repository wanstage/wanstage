#!/bin/zsh
set -eu
LOG="$HOME/WANSTAGE/logs/line_control.log"
mkdir -p "$(dirname "$LOG")"

echo "=== 🧩 LINE Auto Control $(date) ===" >>"$LOG"

LINE_LIMIT_REACHED=$(grep -q "429" "$HOME/WANSTAGE/logs/notify_line.log" 2>/dev/null && echo 1 || echo 0)

if [ "$LINE_LIMIT_REACHED" = "1" ]; then
  echo "⚠️ LINE月間上限検出：Slack通知に切替" >>"$LOG"
  export WAN_NOTIFY_LINE_LIMITED=true
  python3 "$HOME/WANSTAGE/notify/notify_slack_message.py" "⚠️ WANSTAGE自動切替：LINE上限検出 → Slackのみ運用継続"
else
  echo "✅ LINE利用可能：通常運用" >>"$LOG"
fi
