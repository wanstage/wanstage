#!/data/data/com.termux/files/usr/bin/bash
# --- WANSTAGE Pixel Termux Setup ---
set -eu

echo "=== 📱 WANSTAGE Termux Setup 開始 ==="

# 1️⃣ パッケージ更新
pkg update -y && pkg upgrade -y

# 2️⃣ rclone 導入
pkg install -y rclone

# 3️⃣ Google Drive 設定（初回のみ対話）
if ! rclone listremotes | grep -q '^gdrive:'; then
  echo "🔑 Google Drive 接続設定を開始します。ブラウザで認証してください。"
  rclone config create gdrive drive scope=drive
fi

# 4️⃣ WANSTAGE フォルダ作成
mkdir -p /storage/emulated/0/WANSTAGE

# 5️⃣ 初回同期（Drive → Pixel）
rclone bisync gdrive:WANSTAGE /storage/emulated/0/WANSTAGE --resync --create-empty-src-dirs -L

# 6️⃣ スクショ同期フォルダを統合
if [ -d /storage/emulated/0/Pictures/Screenshots ]; then
  ln -sf /storage/emulated/0/Pictures/Screenshots /storage/emulated/0/WANSTAGE/screens
  echo "🖼️ スクショフォルダを WANSTAGE/screens にリンクしました"
fi

# 7️⃣ 定期同期（毎時間）
echo "0 * * * * rclone bisync gdrive:WANSTAGE /storage/emulated/0/WANSTAGE -L" > ~/.termux/cron.tab 2>/dev/null || true
echo "=== ✅ WANSTAGE Pixel セットアップ完了 ==="
