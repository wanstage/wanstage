#!/usr/bin/env bash
set -euo pipefail
NAME="$(basename "$0")"
CANDIDATES=(
  "./scripts/$NAME"
  "./$NAME"
  "./tools/$NAME"
)
for f in "${CANDIDATES[@]}"; do
  if [ -f "$f" ]; then
    exec "$f" "$@"
  fi
done
echo "[WANSTAGE] '$NAME' はまだ実装/配置されていません。"
echo "  置き場所候補: scripts/$NAME  または  tools/$NAME"
exit 127
