#!/bin/zsh
set -euo pipefail
BASE="$HOME/WANSTAGE"
cd "$BASE"

# 環境変数
if [ -f "$BASE/.env" ]; then set -a; source "$BASE/.env"; set +a; fi

# Python venv
if [ -d "$BASE/venv" ]; then source "$BASE/venv/bin/activate"; fi

# Node 依存
if [ -f "$BASE/package-lock.json" ]; then
  npm ci --prefix "$BASE"
elif [ -f "$BASE/package.json" ]; then
  npm install --prefix "$BASE"
fi

# Python 依存
if [ -f "$BASE/requirements.txt" ]; then
  python3 -m pip install -r "$BASE/requirements.txt"
fi

# ログディレクトリ
mkdir -p "$BASE/logs"

# 起動（存在するものを優先順に実行）
if [ -f "$BASE/app.py" ]; then
  python3 "$BASE/app.py"
elif [ -f "$BASE/server.mjs" ]; then
  node "$BASE/server.mjs"
elif [ -f "$BASE/app.js" ]; then
  node "$BASE/app.js"
else
  echo "No entrypoint found (app.py/server.mjs/app.js)" >&2
  exit 1
fi
