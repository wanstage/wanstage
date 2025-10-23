#!/usr/bin/env bash
set -euo pipefail

echo "→ git リポジトリでの掃除を始めます: $(pwd)"

echo "1. リモート追跡ブランチ整理 (prune)"
git fetch --prune

echo "2. 未追跡ファイルの確認 (dry run)"
git clean -n -d

SCRIPT_NAME=$(basename "$0")
echo "（注意）このスクリプト自身: $SCRIPT_NAME を除外対象にします。"

# ZSH_VERSION が未定義でもエラーにならないようにする
if [ -n "${ZSH_VERSION:-}" ]; then
  set +H
fi

if tty -s; then
  read -p "未追跡ファイルを実際に削除しますか？ (y/N): " ans
else
  echo "ノン対話モードのため、未追跡ファイルの削除はスキップされます。"
  ans="n"
fi

if [[ "${ans,,}" == "y" ]]; then
  git clean -f -d -e "$SCRIPT_NAME"
  echo "  未追跡ファイルを削除しました（$SCRIPT_NAME を除外）"
else
  echo "  未追跡ファイルの削除をスキップ"
fi

echo "3. ガーベジコレクション & 最適化"
git gc --prune=now

echo "掃除完了"
