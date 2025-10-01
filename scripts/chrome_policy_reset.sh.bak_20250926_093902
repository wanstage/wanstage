#!/usr/bin/env bash
set -euo pipefail

# Chrome 拡張の強制導入ポリシーを「最小6本」に差し替える
# 管理対象 PLIST（macOS ローカルポリシー）
PLIST="/Library/Managed Preferences/com.google.Chrome.plist"

# 6本の拡張（ID;CRX 更新URL）
EXTS=(
  "iabeihobmhlgpkcgjiloemdbofjbdcic;https://clients2.google.com/service/update2/crx"  # Bitly
  "nngceckbapebfimnlniiiahkandclblb;https://clients2.google.com/service/update2/crx"  # Bitwarden
  "ddkjiahejlhfcafbddmgiahcphecmpfh;https://clients2.google.com/service/update2/crx"  # uBlock Origin Lite
  "bcjindcccaagfpapjjmafapmmgkkhgoa;https://clients2.google.com/service/update2/crx"  # JSON Formatter
  "kejbdjndbnbjgmefkgdddjlbokphdefk;https://clients2.google.com/service/update2/crx"  # Tag Assistant
  "aicmkgpgakddgnaphhhpliifpcfhicfo;https://clients2.google.com/service/update2/crx"  # Postman Interceptor
)

echo "[*] Reset policy at: $PLIST"
# 既存のキーを消す（無ければ無視）
sudo /usr/libexec/PlistBuddy -c "Delete :ExtensionInstallForcelist" "$PLIST" 2>/dev/null || true
# 空配列を作る
sudo /usr/libexec/PlistBuddy -c "Add :ExtensionInstallForcelist array" "$PLIST"

# 配列に順番に追加
i=0
for v in "${EXTS[@]}"; do
  sudo /usr/libexec/PlistBuddy -c "Add :ExtensionInstallForcelist:$i string $v" "$PLIST"
  i=$((i+1))
done

# 権限整える
sudo chmod 644 "$PLIST"

echo "[*] Applied list:"
sudo /usr/libexec/PlistBuddy -c "Print :ExtensionInstallForcelist" "$PLIST"

echo "[*] Restarting Chrome to reload policies..."
osascript -e 'quit app "Google Chrome"' >/dev/null 2>&1 || true
sleep 2
open -a "Google Chrome"

echo "[*] Done. 反映の確認:"
echo "    1) ターミナル: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --show-policy | grep -A3 ExtensionInstallForcelist"
echo "    2) Chrome アドレスバー: chrome://policy → Reload policies"
