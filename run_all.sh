#!/usr/bin/env bash
set -euo pipefail

# 環境変数
if [[ -f "$HOME/WANSTAGE/.env" ]]; then
  set -a
  source "$HOME/WANSTAGE/.env"
  set +a
fi

# Python 仮想環境
if [[ -d "$HOME/WANSTAGE/venv" ]]; then
  source "$HOME/WANSTAGE/venv/bin/activate"
fi

# Node 依存
if [[ -f "$HOME/WANSTAGE/package-lock.json" ]]; then
  npm ci --prefix "$HOME/WANSTAGE"
elif [[ -f "$HOME/WANSTAGE/package.json" ]]; then
  npm install --prefix "$HOME/WANSTAGE"
fi

# Python 依存
if [[ -f "$HOME/WANSTAGE/requirements.txt" ]]; then
  python3 -m pip install -r "$HOME/WANSTAGE/requirements.txt"
fi

# ログディレクトリ
mkdir -p "$HOME/WANSTAGE/logs"

# アプリ起動（必要に応じて変更）
cd "$HOME/WANSTAGE"
python3 app.py
# または: node server.mjs
