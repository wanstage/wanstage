#!/bin/zsh
# --- WANSTAGE ONE BUTTON: 無料構成 自動投稿一括実行 ---
set -eu
set -a
. "$HOME/WANSTAGE/.env"
set +a

echo "=== 🚀 WANSTAGE_ONE_BUTTON start ==="
"$HOME/WANSTAGE/core/generate_post_from_prompt.py" || true
"$HOME/WANSTAGE/bin/wan-notify" || true
echo "✅ WANSTAGE ONE BUTTON complete"
