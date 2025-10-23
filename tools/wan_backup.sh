#!/bin/bash
set -euo pipefail
BASE="$HOME/WANSTAGE"
DEST="$HOME/WANSTAGE/backups"
EXC="$BASE/.sync-exclude.txt"
STAMP=$(date +"%Y%m%d-%H%M%S")

mkdir -p "$DEST"
echo "📦 rsync backup → $DEST/WANSTAGE_sync/"
rsync -avh --delete --info=progress2 \
  --exclude-from="$EXC" \
  "$BASE/" "$DEST/WANSTAGE_sync/"

echo "🗜 追加でアーカイブ作成（コード＆設定のみ）"
TMP="$DEST/WANSTAGE-$STAMP.tar.gz"
tar --exclude-from="$EXC" -czf "$TMP" -C "$BASE" .

echo "🔐 SHA256生成"
shasum -a 256 "$TMP" > "$TMP.sha256"

echo "✅ Backup done:"
echo " - rsync mirror : $DEST/WANSTAGE_sync/"
echo " - archive      : $TMP"
echo " - checksum     : $TMP.sha256"
