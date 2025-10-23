#!/bin/zsh
# === auto_intel_gen.py 互換層導入 ===
set -eu
BASE="$HOME/WANSTAGE/core"
TARGET="$BASE/auto_intel_gen.py"

if ! grep -q "compat_args" "$TARGET"; then
  echo "🩹 auto_intel_gen.py に互換層を追加中..."
  /usr/bin/sed -i '' '1i\
import sys\
# --- 互換層: 古い引数 (--mode, --env) 無視対応 ---\
compat_args = {"--mode","--env"}\
sys.argv = [a for a in sys.argv if not any(c in a for c in compat_args)]\
' "$TARGET"
  echo "✅ 互換層を追加しました"
else
  echo "✅ 既に互換層あり"
fi
