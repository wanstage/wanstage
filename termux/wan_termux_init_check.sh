#!/data/data/com.termux/files/usr/bin/bash
set -eu
echo "=== ⚙️ WANSTAGE Termux 初期セットアップ開始 ==="
termux-setup-storage
sleep 2
pkg update -y && pkg upgrade -y
pkg install -y rclone termux-api
if ! rclone listremotes | grep -q '^gdrive:'; then
  echo "🔑 Google Drive接続が未設定です。設定を開始します。"
  rclone config create gdrive drive scope=drive
else
  echo "✅ Google Drive接続(gdrive:)が確認されました"
fi
mkdir -p /storage/emulated/0/WANSTAGE
rclone bisync gdrive:WANSTAGE /storage/emulated/0/WANSTAGE --resync --create-empty-src-dirs -L
if [ -d /storage/emulated/0/Pictures/Screenshots ]; then
  ln -sf /storage/emulated/0/Pictures/Screenshots /storage/emulated/0/WANSTAGE/screens
fi
CRONFILE="$HOME/.termux/cron.tab"
mkdir -p "$HOME/.termux"
echo "0 * * * * rclone bisync gdrive:WANSTAGE /storage/emulated/0/WANSTAGE -L" > "$CRONFILE"
rclone ls gdrive: | head -n 5 || true
echo "=== ✅ Termux初期化完了 ==="
