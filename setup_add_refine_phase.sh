#!/bin/zsh
set -eu
set -o pipefail

BASE="$HOME/WANSTAGE"
MACRO="$BASE/bin/wan_macro_flow.sh"

echo "=== 🧠 WANSTAGE: Refineフェーズ追加処理 ==="

if [ ! -f "$MACRO" ]; then
  echo "❌ $MACRO が見つかりません。既存マクロを作成してから実行してください。"
  exit 1
fi

# Refineフェーズが既にあるかチェック
if grep -q "gpt_refiner.py" "$MACRO"; then
  echo "ℹ️ すでにRefineフェーズが追加されています。"
  exit 0
fi

# wan_macro_flow.sh にフェーズ追加
cat <<'PATCH' >> "$MACRO"

# === 🧠 Refineフェーズ ===
if [ "$phase" = "refine" ] || [ "$phase" = "all" ]; then
  echo "🧠 改善フェーズ実行..." | tee -a "$LOGFILE"
  python3 "$BASE/core/gpt_refiner.py" >>"$LOGFILE" 2>&1
fi
PATCH

chmod +x "$MACRO"
echo "✅ Refineフェーズを $MACRO に追加しました。"
echo "試すには: bash ~/WANSTAGE/bin/wan_macro_flow.sh refine"
