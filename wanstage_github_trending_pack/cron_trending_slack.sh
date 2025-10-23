#!/bin/zsh
set -eu
cd "\$HOME/WANSTAGE/wanstage_github_trending_pack"
source "\$HOME/WANSTAGE/.venv/bin/activate"

python3 fetch_github_trending.py
python3 fetch_github_code_stats.py

if [ -n "\${SLACK_WEBHOOK_URL:-}" ]; then
  LOG="logs/github_trending.json"
  if [ -f "\$LOG" ]; then
    top3=\$(jq -r '.data[:3][] | "\(.repo) ★\(.stars)"' "\$LOG")
    ts=\$(jq -r '.timestamp' "\$LOG")
    msg="📊 GitHub Trending Report (${ts})"
    i=1
    while read -r line; do
      msg+="\\n${i}️⃣ ${line}"
      i=\$((i+1))
    done <<< "\$top3"
    curl -s -X POST -H "Content-type: application/json" \
      --data "{\"text\":\"${msg}\"}" "\${SLACK_WEBHOOK_URL}" >/dev/null
  fi
fi
