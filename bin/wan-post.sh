#!/usr/bin/env bash
set -Eeuo pipefail
WD="$HOME/WANSTAGE"
cd "$WD"

VENV="$WD/.venv"
. "$VENV/bin/activate"
PY="$VENV/bin/python"; PIP="$VENV/bin/pip"

# .env 読込
python - <<'PY' || true
from dotenv import load_dotenv; load_dotenv()
PY

# 軽量運用依存（不足だけ入れる）
REQS=(requests gspread google-auth google-auth-oauthlib python-dotenv)
for m in "${REQS[@]}"; do
  "$PY" - "$m" >/dev/null 2>&1 <<'PY' || "$PIP" install -q "$m"
import importlib,sys; importlib.import_module(sys.argv[1])
PY
done

# 実行フロー
# [DISABLED by script] if [ -x scripts/full_auto_post_flow.sh ]; then
  echo "[wan-post] run flow"
# [DISABLED by script]   echo "[RUN] full_auto_post_flow.sh"
# [DISABLED by script]   ./scripts/full_auto_post_flow.sh
elif [ -f analytics/update_post_log.py ]; then
  "$PY" analytics/update_post_log.py || true
else
# [DISABLED by script]   echo "[wan-post] no runnable flow found (scripts/full_auto_post_flow.sh or analytics/update_post_log.py)."
fi
