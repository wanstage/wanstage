#!/bin/zsh
set -eu
BASE="$HOME/WANSTAGE"
source "$BASE/.venv/bin/activate"
set -a; source "$BASE/.env"; set +a

echo "=== 🚀 Auto Post Start $(date) ==="
python3 "$BASE/core/generate_post_from_prompt.py"
python3 "$BASE/core/post_to_instagram.py" || true
python3 "$BASE/notify/notify_slack_message.py" "✅ 投稿完了: $(date '+%H:%M')" || true
python3 "$BASE/notify/notify_line_message.py" "✅ 投稿完了: $(date '+%H:%M')" || true
echo "=== ✅ 完了 ==="
