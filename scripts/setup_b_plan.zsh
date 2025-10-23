#!/usr/bin/env zsh
set -euo pipefail
set +H 2>/dev/null || true   # zsh の "!" 履歴展開を無効化

REPO="wanstage/wanstage"
ASSET_DIR="拡散用"
ZIP_PREFIX="kakusan"
TAG=${1:-assets-$(date +%Y%m%d)}
RELEASE_TITLE="拡散用 assets ($(date +%Y-%m-%d))"
RELEASE_NOTE="CIでは取得せず、必要時のみダウンロード"

# 必要コマンド確認
for cmd in gh zip git; do
  command -v "$cmd" >/dev/null || { echo "[ERR] '$cmd' が見つかりません"; exit 1; }
done

echo "[STEP] .gitattributes / .gitignore 整備 & index から除外"
git lfs untrack "$ASSET_DIR/**" || true
sed -i '' -e '/拡散用\/\*\*/d' .gitattributes 2>/dev/null || true
grep -qE '^/拡散用/?$' .gitignore 2>/dev/null || echo "/拡散用/" >> .gitignore
git rm -r --cached "$ASSET_DIR" 2>/dev/null || true
git add .gitignore .gitattributes
git commit -m "chore: stop tracking heavy assets (use Releases/S3)" || true
git push origin main || true

# zip 作成（日本語名保持・再帰）
if [ -d "$ASSET_DIR" ]; then
  ZIP="${ZIP_PREFIX}_$(date +%Y%m%d).zip"
  echo "[STEP] ZIP 作成: $ZIP"
  /usr/bin/zip -qry "$ZIP" "$ASSET_DIR"
else
  echo "[INFO] '$ASSET_DIR' なし → ZIP は作りません"
  ZIP=""
fi

echo "[STEP] Release 作成/更新: $TAG"
if gh release view "$TAG" >/dev/null 2>&1; then
  echo "[INFO] 既存タグ $TAG に追記します"
else
  echo "[INFO] 新規作成します: $TAG"
  gh release create "$TAG" -t "$RELEASE_TITLE" -n "$RELEASE_NOTE"
fi

if [ -n "$ZIP" ] && [ -f "$ZIP" ]; then
  echo "[STEP] アセットアップロード（上書き許可）: $ZIP"
  gh release upload "$TAG" "$ZIP" --clobber
fi

echo "[STEP] gh release download 検証"
rm -rf /tmp/_wan_release_test && mkdir -p /tmp/_wan_release_test
pushd /tmp/_wan_release_test >/dev/null
gh release download "$TAG" -p "${ZIP_PREFIX}_*.zip" -R "$REPO"
find . -name "${ZIP_PREFIX}_*.zip" -print0 | xargs -0 -I{} unzip -q {} -d .
popd >/dev/null
echo "[OK] download & unzip 確認完了: /tmp/_wan_release_test"
