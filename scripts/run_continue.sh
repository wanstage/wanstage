#!/usr/bin/env zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "[DEBUG] ROOT=$ROOT"
CONT_DIR="$ROOT/externals/continue"
[ -d "$CONT_DIR" ] || CONT_DIR="$ROOT/continue"
echo "[DEBUG] CONT_DIR=$CONT_DIR"
if [ ! -d "$CONT_DIR" ]; then echo "[ERROR] continue dir missing"; exit 1; fi
if [ -f "$CONT_DIR/main.py" ]; then
  echo "[DEBUG] Exec: python3 $CONT_DIR/main.py $*"
  exec python3 "$CONT_DIR/main.py" "$@"
elif [ -f "$CONT_DIR/app.py" ]; then
  echo "[DEBUG] Exec: python3 $CONT_DIR/app.py $*"
  exec python3 "$CONT_DIR/app.py" "$@"
elif [ -f "$CONT_DIR/index.js" ]; then
  echo "[DEBUG] Exec: node $CONT_DIR/index.js $*"
  exec node "$CONT_DIR/index.js" "$@"
elif [ -f "$CONT_DIR/package.json" ]; then
  echo "[DEBUG] Exec: npm --prefix $CONT_DIR run start -- $*"
  exec npm --prefix "$CONT_DIR" run start -- "$@"
else
  echo "[ERROR] entry not found (main.py/app.py/index.js/package.json)"
  exit 1
fi
