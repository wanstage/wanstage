#!/usr/bin/env zsh
set -euo pipefail

# -------- 基本ユーティリティ --------
LOG="logs/repair.log"; mkdir -p "$(dirname "$LOG")"
ts(){ date '+%Y-%m-%d %H:%M:%S'; }
say(){ echo "[$(ts)] $*" | tee -a "$LOG" >&2; }
fail(){ say "ERROR: $*"; exit 1; }
mask_url(){ sed -E 's#https?://([^/]{1,6})[^ ]*#https://\1…#g'; }

# -------- .env をクリーン化（変数行だけ残す）--------
clean_env(){
  [ -f .env ] || :> .env
  cp -f .env ".env.bak.$(date +%s)"
  tr -d '\r' < .env > .env.tmp || true
  awk '/^[A-Za-z_][A-Za-z0-9_]*=/{print}' .env.tmp > .env || :> .env
  rm -f .env.tmp
  chmod 600 .env || true
  say ".env cleaned"
}

# -------- .env に key=value を upsert --------
upsert_env(){ # upsert_env KEY VALUE
  local k="$1" v="$2"
  if grep -q "^${k}=" .env 2>/dev/null; then
    awk -v k="$k" -v v="$v" -F= 'BEGIN{OFS="="} $1==k{$2=v;print k,v;next} {print}' .env > .env.tmp
  else
    cat .env > .env.tmp; echo "${k}=${v}" >> .env.tmp
  fi
  mv .env.tmp .env; chmod 600 .env || true
}

# -------- .env 読み込み --------
load_env(){ set -a; . ./.env; set +a; }

# -------- Slack最小通知（任意）--------
notify(){
  local msg="$1" url="${2:-}"
  echo "[NOTIFY] $(ts) ${msg} ${url}" >> logs/notify.log
  if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    local payload
    payload=$(printf '{"text":"[WANSTAGE] %s %s"}' "$(echo "$msg"|mask_url)" "$(echo "$url"|mask_url)")
    curl -sS -X POST "$SLACK_WEBHOOK_URL" -H 'content-type: application/json' --data "$payload" >/dev/null \
      && echo "ok[SLACK] $(ts) $(echo "$msg $url"|mask_url)" >> logs/notify.log \
      || echo "[SLACK] $(ts) NG $(echo "$msg $url"|mask_url)" >> logs/notify.log
  fi
}

# -------- Cloudflare API: トークン検証 --------
cf_verify(){
  [ -n "${CF_API_TOKEN:-}" ] || fail "CF_API_TOKEN が .env にありません"
  curl -fsS -H "Authorization: Bearer $CF_API_TOKEN" \
    https://api.cloudflare.com/client/v4/user/tokens/verify >/dev/null \
    || fail "CF_API_TOKEN 検証NG（権限/値を再確認）"
  say "CF_API_TOKEN verify OK"
}

# -------- Cloudflare API: Workers Subdomain 取得 --------
cf_get_subdomain(){
  [ -n "${CF_ACCOUNT_ID:-}" ] || fail "CF_ACCOUNT_ID が .env にありません"
  local sub
  sub=$(
    curl -fsS -H "Authorization: Bearer $CF_API_TOKEN" \
      "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/workers/subdomain" \
    | python3 - <<'PY' || true
import sys,json
try:
  d=json.load(sys.stdin)
  print(d.get("result",{}).get("subdomain",""))
except: print("")
PY
  )
  echo "$sub"
}

# -------- wrangler.toml から Worker 名取得（なければ既定）--------
get_service_name(){
  local name
  name=$(grep -E '^\s*name\s*=' cf-worker-notify/wrangler.toml 2>/dev/null \
         | head -1 | sed -E 's/.*=\s*"?([A-Za-z0-9_-]+)"?.*/\1/')
  [ -n "$name" ] && echo "$name" || echo "wanstage-worker"
}

# -------- /health チェック --------
check_health(){
  local url="${1:?}"
  curl -fsS "$url/health" >/dev/null
}

# ================== 本処理 ==================
say "start auto-repair"

# 1) .env クリーン
clean_env

# 2) 必須キーを案内（未定義なら空で置く→ユーザーが後で埋める）
grep -q '^CF_ACCOUNT_ID=' .env || upsert_env CF_ACCOUNT_ID ""
grep -q '^CF_API_TOKEN='  .env || upsert_env CF_API_TOKEN ""
load_env

# 3) トークン検証
cf_verify || exit 1

# 4) Subdomain 取得（UIで未有効だと空）
SUBDOMAIN="$(cf_get_subdomain || true)"
if [ -z "$SUBDOMAIN" ]; then
  say "Workers Subdomain 未有効化 or 権限不足。Cloudflareダッシュボードで一度 Subdomain を有効化してください。"
  notify "Workers Subdomain 未有効 / 要手動有効化" ""
  exit 2
fi
say "Subdomain = ${SUBDOMAIN}"

# 5) Worker名 → URL作成 → .env 反映
SERVICE="$(get_service_name)"
WORKER_URL="https://${SERVICE}.${SUBDOMAIN}.workers.dev"
upsert_env WORKER_URL "$WORKER_URL"
load_env
say "WORKER_URL upsert: $WORKER_URL"

# 6) /health チェック（NGならリトライ）
if check_health "$WORKER_URL"; then
  say "health OK: $WORKER_URL/health"
  notify "Worker health OK" "$WORKER_URL"
  exit 0
fi

say "health NG: 1回目。20秒待って再試行"
sleep 20
if check_health "$WORKER_URL"; then
  say "health OK: $WORKER_URL/health (2nd)"
  notify "Worker health OK (2nd)" "$WORKER_URL"
  exit 0
fi

say "health NG: 2回目。GitHub Actions の worker-deploy 確認推奨"
notify "Worker health NG" "$WORKER_URL"
exit 3
