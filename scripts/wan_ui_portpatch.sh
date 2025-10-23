#!/bin/zsh
# === WANSTAGE: Streamlitポート自動回避パッチ ===
set -eu
set -o pipefail

TARGET="$HOME/WANSTAGE/ui_main.py"
BACKUP="${TARGET}.bak_$(date +%Y%m%d_%H%M%S)"

echo "=== 🧩 WANSTAGE UIポート自動回避パッチ（標準モード） ==="

if [ ! -f "$TARGET" ]; then
  echo "❌ $TARGET が見つかりません。"
  exit 1
fi

if grep -q 'STREAMLIT_SERVER_PORT' "$TARGET"; then
  echo "✅ すでにポート自動設定が含まれています。変更不要です。"
  exit 0
fi

cp "$TARGET" "$BACKUP"
echo "🗂 バックアップ作成: $BACKUP"

TMP=$(mktemp)
{
  echo 'import os'
  echo 'os.environ["STREAMLIT_SERVER_PORT"] = "0"'
  echo ''
  cat "$TARGET"
} > "$TMP"

mv "$TMP" "$TARGET"
echo "✅ パッチを適用しました: $TARGET"
echo "=== 完了 ==="
