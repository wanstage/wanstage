#!/bin/zsh
# SNS収益集計（期間指定対応・未定義変数に強い）
set -euo pipefail

aggregate() {
  set +u  # ← ここで一旦ゆるめる（未定義でも受け取れるように）
  local ASOF="$(date +%Y-%m-%d)"
  local SINCE=""
  local UNTIL=""
  # 引数パース（--date/--since/--until）
  for arg in "$@"; do
    case "$arg" in
      --date=*)  ASOF="${arg#--date=}" ;;
      --since=*) SINCE="${arg#--since=}" ;;
      --until=*) UNTIL="${arg#--until=}" ;;
    esac
  done
  set -u  # ← 以降は厳格に戻す

  local ROOT="${HOME}/WANSTAGE"
  local LOG_DIR="$ROOT/logs"
  local OUT_DIR="$ROOT/out"
  local POST_LOG="$LOG_DIR/post.log"

  mkdir -p "$OUT_DIR" "$LOG_DIR"

  # Pythonで post.log を集計（ts= があれば期間フィルタ）
  python3 - "$POST_LOG" "$OUT_DIR" "$ASOF" "${SINCE:-}" "${UNTIL:-}" <<'PY'
import sys, json, re, collections, pathlib, os
from datetime import datetime

post_log, out_dir, asof, since, until = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
since_dt = datetime.min if not since else datetime.strptime(since, "%Y-%m-%d")
until_dt = datetime.max if not until else datetime.strptime(until, "%Y-%m-%d")

# 例行:
# [POST] ts=2025-10-10T20:45:00 ch=tiktok cap=... tags=#a #b
re_post = re.compile(r'^\[POST\]\s+(?:ts=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+)?ch=([^\s]+)\s+cap=(.*?)\s+tags=(.*)$')

def in_range(ts_s):
    if not ts_s:
        return True
    try:
        ts = datetime.strptime(ts_s, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return True
    return (since_dt.date() <= ts.date() <= until_dt.date())

per_channel = collections.Counter()
hashtags = collections.Counter()
total = 0

if os.path.exists(post_log):
    with open(post_log, encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            m = re_post.match(line)
            if not m:
                continue
            ts_s, ch, cap, tags = m.groups()
            if not in_range(ts_s):
                continue
            total += 1
            per_channel[ch] += 1
            tags = (tags or "").strip()
            if tags:
                for t in tags.split():
                    t = t.strip()
                    if not t: 
                        continue
                    while t.startswith('#'):
                        t = t[1:]
                    if t:
                        hashtags[t.lower()] += 1

summary = {
    "asof": asof,
    "range": {"since": since or "all", "until": until or "all"},
    "total_posts": total,
    "per_channel": dict(per_channel),
    "top_hashtags": [{"tag": k, "count": c} for k, c in hashtags.most_common(20)],
}

pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
json_path = os.path.join(out_dir, f"monetize_summary_{asof}.json")
txt_path  = os.path.join(out_dir, f"monetize_summary_{asof}.txt")

with open(json_path, "w", encoding="utf-8") as w:
    json.dump(summary, w, ensure_ascii=False, indent=2)

with open(txt_path, "w", encoding="utf-8") as w:
    w.write(f"AS OF {asof}\n")
    w.write(f"Range: since={since or 'all'} until={until or 'all'}\n")
    w.write(f"Total posts: {total}\n\n")
    w.write("[Per channel]\n")
    for ch, c in sorted(per_channel.items(), key=lambda x: (-x[1], x[0])):
        w.write(f"- {ch}: {c}\n")
    w.write("\n[Top hashtags]\n")
    for i, (k, c) in enumerate(hashtags.most_common(20), 1):
        w.write(f"{i:2d}. #{k}  x{c}\n")

print(out_dir)
PY
}

case "${1:-}" in
  aggregate) shift; aggregate "$@";;
  *) echo "usage: $(basename "$0") aggregate [--date=YYYY-MM-DD] [--since=YYYY-MM-DD] [--until=YYYY-MM-DD]" >&2; exit 1;;
esac
