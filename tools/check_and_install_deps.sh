#!/bin/bash
set -euo pipefail

PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
PIP_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/pip3"

REQUIRED_MODULES=("moviepy" "imageio[ffmpeg]" "numpy" "decorator" "tqdm" "gTTS" "soundfile")

echo "🔍 必要な依存を確認中..."

for MODULE in "${REQUIRED_MODULES[@]}"; do
  MODULE_NAME="${MODULE%%[*]}"  # "imageio[ffmpeg]" → "imageio"
  if ! "$PYTHON_BIN" -c "import ${MODULE_NAME}" &> /dev/null; then
    echo "📦 モジュールが見つかりません: ${MODULE_NAME} → インストール中..."
    "$PIP_BIN" install "$MODULE"
  else
    echo "✅ ${MODULE_NAME} は既にインストール済みです"
  fi
done

echo "✅ 依存関係はすべて整いました！"
