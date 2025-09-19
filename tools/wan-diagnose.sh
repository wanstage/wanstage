#!/usr/bin/env bash
set -u
BASE="$HOME/WANSTAGE"
VENV="$BASE/.venv"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"
RED='\033[31m'; GRN='\033[32m'; YEL='\033[33m'; CYA='\033[36m'; NC='\033[0m'

say(){ printf "%b\n" "$@"; }
ok(){ say "${GRN}[OK]${NC} $*"; }
ng(){ say "${RED}[NG]${NC} $*"; }
warn(){ say "${YEL}[WARN]${NC} $*"; }
info(){ say "${CYA}[INFO]${NC} $*"; }

say "==== WANSTAGE Diagnose ===="

# 0) ディレクトリ
[ -d "$BASE" ] && ok "BASE exists: $BASE" || { ng "BASE missing: $BASE"; exit 1; }

# 1) venv / python
if [ -x "$PY" ]; then
  ok "venv python: $PY"
  "$PY" -V
else
  ng "venv python not found: $PY"
fi

# 2) Python 必須モジュール
REQS=(python-dotenv google-analytics-data google-auth-oauthlib gspread google-auth requests)
MISSING=()
for m in "${REQS[@]}"; do
  "$PY" - "$m" >/dev/null 2>&1 <<'PY' || MISSING+=("$1")
import importlib,sys; importlib.import_module(sys.argv[1])
PY
done
if [ "${#MISSING[@]}" -gt 0 ]; then
  ng "missing packages: ${MISSING[*]}"
else
  ok "all required packages importable"
fi

# 3) ファイル存在
FILES=(
  "$BASE/keys/ga4-oauth.json"
  "$BASE/keys/ga4-sa.json"
  "$BASE/keys/token-ga4.json"
  "$BASE/analytics/ga4_quick_oauth.py"
  "$BASE/analytics/ga4_to_slack.py"
  "$BASE/analytics/ga4_quick.py"
  "$BASE/scripts/full_auto_post_flow.sh"
  "$BASE/.env"
)
for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then ok "file exists: $f"; else warn "file missing: $f"; fi
done

# 4) .env 必須キー
DOTENV_OK=$("$PY" - <<'PY'
import os, sys
from dotenv import load_dotenv
p=os.path.expanduser('~/WANSTAGE/.env')
load_dotenv(p)
pid=os.getenv('GA4_PROPERTY_ID','').strip()
nt=os.getenv('NOTION_TOKEN','')
nd=os.getenv('NOTION_DB_ID','')
sw=os.getenv('SLACK_WEBHOOK_URL','')
print("PID_OK" if pid.isdigit() else "PID_NG")
print("NOTION_TOKEN:" + ("SET" if bool(nt) else "EMPTY"))
print("NOTION_DB_ID:" + ("SET" if bool(nd) else "EMPTY"))
print("SLACK_WEBHOOK_URL:" + ("SET" if bool(sw) else "EMPTY"))
PY
)
echo "$DOTENV_OK" | while read -r line; do
  case "$line" in
    PID_OK) ok "GA4_PROPERTY_ID looks valid (digits)";;
    PID_NG) ng "GA4_PROPERTY_ID invalid (must be digits only)";;
    NOTION_TOKEN:SET) ok "NOTION_TOKEN set";;
    NOTION_TOKEN:EMPTY) warn "NOTION_TOKEN empty";;
    NOTION_DB_ID:SET) ok "NOTION_DB_ID set";;
    NOTION_DB_ID:EMPTY) warn "NOTION_DB_ID empty";;
    SLACK_WEBHOOK_URL:SET) ok "SLACK_WEBHOOK_URL set";;
    SLACK_WEBHOOK_URL:EMPTY) warn "SLACK_WEBHOOK_URL empty";;
  esac
done

# 5) ADC / OAuth 状態
GAC="${GOOGLE_APPLICATION_CREDENTIALS:-}"
if [ -n "$GAC" ]; then
  if [ -f "$GAC" ]; then
    ok "GOOGLE_APPLICATION_CREDENTIALS points to file: $GAC"
  else
    ng "GOOGLE_APPLICATION_CREDENTIALS set but file missing: $GAC"
  fi
else
  info "GOOGLE_APPLICATION_CREDENTIALS not set (OAuth route expected)"
fi
[ -f "$BASE/keys/token-ga4.json" ] && ok "OAuth token exists: keys/token-ga4.json" || info "OAuth token not found yet"

# 6) GA4 クライアント作成テスト（ネットワーク呼び出しなし）
"$PY" - <<'PY' && ok "GA4 client construct test passed" || ng "GA4 client construct test failed"
import os
from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2.service_account import Credentials as SACreds
from google.oauth2.credentials import Credentials as OAuthCreds

base = os.path.expanduser('~/WANSTAGE')
pid_ok = False
load_dotenv(os.path.join(base,'.env'))
pid = os.getenv('GA4_PROPERTY_ID','').strip()
pid_ok = pid.isdigit()
assert pid_ok

gac = os.getenv('GOOGLE_APPLICATION_CREDENTIALS','').strip()
if gac and os.path.exists(gac):
    creds = SACreds.from_service_account_file(gac, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
else:
    tok = os.path.join(base,'keys','token-ga4.json')
    if os.path.exists(tok):
        creds = OAuthCreds.from_authorized_user_file(tok, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
    else:
        raise SystemExit("No creds available (neither GA4 SA file nor OAuth token)")
client = BetaAnalyticsDataClient(credentials=creds)
PY

# 7) Slack URL 形式チェック（実送信なし）
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  case "$SLACK_WEBHOOK_URL" in
    https://hooks.slack.com/services/*) ok "Slack webhook format looks OK";;
    *) warn "Slack webhook format unusual";;
  esac
else
  warn "Slack webhook is empty"
fi

# 8) pm2
if command -v pm2 >/dev/null 2>&1; then
  ok "pm2 found: $(command -v pm2)"
  pm2 ls || warn "pm2 ls reported non-zero"
else
  warn "pm2 not found. If you use nvm: export PATH=\"$HOME/.nvm/versions/node/v22.19.0/bin:\$PATH\""
fi

# 9) crontab 登録確認
CRON_NOW="$(crontab -l 2>/dev/null || true)"
echo "$CRON_NOW" | grep -q 'ga4_quick' && ok "cron: GA4 QUICK entry exists" || warn "cron: GA4 QUICK entry not found"
echo "$CRON_NOW" | grep -q 'wan-post.sh' && ok "cron: wan-post entry exists" || warn "cron: wan-post entry not found"

# 10) 代表ログ
for logf in "$BASE/logs/cron_ga4_quick.log" "$BASE/logs/cron_ga4.log" "$BASE/logs/full_auto.log"; do
  if [ -f "$logf" ]; then
    info "tail: $logf"
    tail -n 10 "$logf"
  fi
done

say "==== Diagnose Finished ===="
