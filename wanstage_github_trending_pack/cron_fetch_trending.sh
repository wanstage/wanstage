#!/bin/zsh
set -eu
cd "/Users/okayoshiyuki/WANSTAGE/wanstage_github_trending_pack"
source "/Users/okayoshiyuki/WANSTAGE/.venv/bin/activate"
python3 fetch_github_trending.py
python3 fetch_github_code_stats.py
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  msg="📊 GitHubトレンド更新完了 $(date +%Y-%m-%d
