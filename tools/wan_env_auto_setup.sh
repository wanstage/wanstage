#!/bin/bash
set -e

echo "🔄 moviepy 関連環境を再構築中..."

PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
PIP_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/pip3"

echo "📦 moviepy をアンインストール中..."
$PIP_BIN uninstall -y moviepy || true

echo "📥 moviepy を再インストール中..."
$PIP_BIN install --upgrade moviepy

echo "📦 依存モジュールを再インストール中..."
$PIP_BIN install --upgrade imageio[ffmpeg] numpy decorator tqdm gTTS soundfile

echo "🔍 不正なファイルがないか確認中..."
if [ -f "$HOME/WANSTAGE/moviepy.py" ]; then
  echo "⚠️ '$HOME/WANSTAGE/moviepy.py' が存在しています。モジュール衝突の原因です。リネームまたは削除してください。"
else
  echo "✅ 'moviepy.py' の衝突は見つかりませんでした。"
fi

echo "✅ 完了：moviepy および依存モジュールの再構築が完了しました！"

echo "🧪 動作確認（インポートテスト）..."
$PYTHON_BIN -c "from moviepy.editor import ImageClip; print('🎉 moviepy.editor 正常に読み込みできました！')"
