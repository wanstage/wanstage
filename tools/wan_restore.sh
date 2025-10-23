#!/bin/bash
set -euo pipefail
BASE="$HOME/WANSTAGE"
SRC_SYNC="$HOME/WANSTAGE/backups/WANSTAGE_sync"
EXC="$BASE/.sync-exclude.txt"

if [ -d "$SRC_SYNC" ]; then
  echo "♻️ rsync restore ← $SRC_SYNC → $BASE"
  rsync -avh --delete --info=progress2 \
    --exclude-from="$EXC" \
    "$SRC_SYNC/" "$BASE/"
else
  echo "❓ rsyncミラーが見つかりません。tar.gzを指定してください:"
  echo "例) $0 /Users/you/WANSTAGE/backups/WANSTAGE-YYYYMMDD-HHMMSS.tar.gz"
  TAR="${1:-}"
  [ -f "$TAR" ] || { echo "❌ tar.gz未指定/不存在"; exit 1; }
  echo "🗜 展開中: $TAR → $BASE"
  tar -xzf "$TAR" -C "$BASE"
fi

echo "🛠 依存を再構築（Python/Node）"
cd "$BASE"
# Python
if [ -f "requirements.lock.txt" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  # 0.4.0を避けるconstraints（後段で作成）を優先使用
  if [ -f "constraints.txt" ]; then
    pip install -r requirements.lock.txt -c constraints.txt
  else
    pip install -r requirements.lock.txt
  fi
fi
# Node
if [ -f "package.json" ]; then
  if [ -f "package-lock.json" ]; then
    npm ci || npm install --legacy-peer-deps
  else
    npm install --legacy-peer-deps
  fi
fi

echo "✅ Restore done."
