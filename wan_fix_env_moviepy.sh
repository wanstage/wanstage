#!/usr/bin/env bash
set -eu
set -o pipefail

echo "=== 🧰 WANSTAGE環境をPython 3.11へ再構築 ==="

# 1. 安定版Python導入
brew install python@3.11

# 2. PATH切替
if ! grep -q "python@3.11" ~/.zshrc; then
  echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
fi
source ~/.zshrc || true

# 3. バージョン確認
echo "🔍 Python バージョン確認:"
which python3
python3 --version

# 4. 依存モジュール再導入
echo "📦 依存モジュール再インストール中..."
pip3 install --upgrade "imageio[ffmpeg]" moviepy numpy decorator tqdm gTTS soundfile || true

# 5. 動作確認
echo "🧪 moviepy.editor のインポート確認..."
python3 -c "from moviepy.editor import ImageClip; print('✅ moviepy.editor 読み込みOK')"

echo "🎉 完了！make_video_from_post.py の実行を再試行してください。"
