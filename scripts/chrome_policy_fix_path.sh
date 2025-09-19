#!/usr/bin/env bash
set -euo pipefail

# 正しいパスに再作成
DIR="/Library/Managed Preferences/com.google.Chrome"
PLIST="$DIR/com.google.Chrome.plist"

sudo mkdir -p "$DIR"

# 最小6本（Bitly/Bitwarden/uBlock Lite/JSON Formatter/Tag Assistant/Postman）
EXTS=(
  "iabeihobmhlgpkcgjiloemdbofjbdcic;https://clients2.google.com/service/update2/crx"
  "nngceckbapebfimnlniiiahkandclblb;https://clients2.google.com/service/update2/crx"
  "ddkjiahejlhfcafbddmgiahcphecmpfh;https://clients2.google.com/service/update2/crx"
  "bcjindcccaagfpapjjmafapmmgkkhgoa;https://clients2.google.com/service/update2/crx"
  "kejbdjndbnbjgmefkgdddjlbokphdefk;https://clients2.google.com/service/update2/crx"
  "aicmkgpgakddgnaphhhpliifpcfhicfo;https://clients2.google.com/service/update2/crx"
)

# 既存キー削除＆作り直し
sudo /usr/libexec/PlistBuddy -c "Delete :ExtensionInstallForcelist" "$PLIST" 2>/dev/null || true
if [ ! -f "$PLIST" ]; then
  sudo /usr/libexec/PlistBuddy -c "Save" "$PLIST" 2>/dev/null || true
fi
sudo /usr/libexec/PlistBuddy -c "Add :ExtensionInstallForcelist array" "$PLIST"

i=0
for v in "${EXTS[@]}"; do
  sudo /usr/libexec/PlistBuddy -c "Add :ExtensionInstallForcelist:$i string $v" "$PLIST"
  i=$((i+1))
done

sudo chmod 644 "$PLIST"

echo "[*] New policy file:"
echo "    $PLIST"
sudo /usr/libexec/PlistBuddy -c "Print :ExtensionInstallForcelist" "$PLIST"

echo "[*] Restarting Chrome..."
osascript -e 'quit app "Google Chrome"' >/dev/null 2>&1 || true
sleep 2
open -a "Google Chrome"

echo "[*] Verify with:"
echo "    /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --show-policy | grep -A3 ExtensionInstallForcelist"
echo "    or chrome://policy → Reload policies"
