# 
mkdir -p ~/WANSTAGE/scripts ~/WANSTAGE/logs

# ig_post_now.sh Instagram Graph API1
cat > ~/WANSTAGE/scripts/ig_post_now.sh <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

cleanup(){ rm -f "$create_tmp" "$publish_tmp" 2>/dev/null || true; }
trap cleanup EXIT

ts(){ date -u '+%F %T'; }

need(){ command -v "$1" >/dev/null 2>&1 || { printf '[%s] missing %s\n' "$(ts)" "$1" >&2; exit 127; }; }

mask_mid(){
  local s="${1:-}" keep=${2:-4} end=${3:-4}
  local n=${#s}
  if (( n <= keep + end )); then printf '%s' "$s"; return; fi
  local h="${s:0:keep}" t="${s: -end}" stars=$(( n - keep - end )) buf
  printf -v buf '%*s' "$stars" ''
  buf=${buf// /'*'}
  printf '%s%s%s' "$h" "$buf" "$t"
}

need curl
need python3

: "${IG_USER_ID:?}"
: "${IG_ACCESS_TOKEN:?}"
: "${IMAGE_URL:?}"
: "${CAPTION:=}"

printf '[%s] IG_USER_ID=%s\n' "$(ts)" "$(mask_mid "${IG_USER_ID}" 3 3)"
printf '[%s] IG_ACCESS_TOKEN=%s (len=%d)\n' "$(ts)" "$(mask_mid "${IG_ACCESS_TOKEN}" 4 4)" "${#IG_ACCESS_TOKEN}"
printf '[%s] IMAGE_URL=%s\n' "$(ts)" "${IMAGE_URL}"
printf '[%s] CAPTION=%s\n' "$(ts)" "${CAPTION}"

echo "[DEBUG] Starting Step 1: Create media container"
create_tmp=$(mktemp)
if ! curl -fsS -X POST "https://graph.facebook.com/v21.0/${IG_USER_ID}/media" \
  -F "image_url=${IMAGE_URL}" \
  -F "caption=${CAPTION}" \
  -F "access_token=${IG_ACCESS_TOKEN}" \
  >"${create_tmp}"; then
  printf '[%s] create_failed\n' "$(ts)" >&2
  [ -s "${create_tmp}" ] && cat "${create_tmp}" >&2 || true
  exit 1
fi
create=$(<"${create_tmp}")

printf '[%s] create response: %s\n' "$(ts)" "$create"

printf '[%s] parsing create response...\n' "$(ts)"
cid=$(printf '%s' "$create" | python3 - <<'PY'
import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get("id",""))
except Exception as e:
    print("", file=sys.stdout)
    print("[DEBUG] parse error:", e, file=sys.stderr)
PY
)

if [[ -z "$cid" ]]; then
  printf '[%s] bad_create_response\n' "$(ts)" >&2
  printf '%s\n' "$create" >&2
  exit 1
fi

echo "[DEBUG] Starting Step 2: Publish container"
publish_tmp=$(mktemp)
if ! curl -fsS -X POST "https://graph.facebook.com/v21.0/${IG_USER_ID}/media_publish" \
  -F "creation_id=${cid}" \
  -F "access_token=${IG_ACCESS_TOKEN}" \
  >"${publish_tmp}"; then
  printf '[%s] publish_failed\n' "$(ts)" >&2
  [ -s "${publish_tmp}" ] && cat "${publish_tmp}" >&2 || true
  exit 1
fi
publish=$(<"${publish_tmp}")

printf '[%s] publish response: %s\n' "$(ts)" "$publish"

printf '[%s] parsing publish response...\n' "$(ts)"
pid=$(printf '%s' "$publish" | python3 - <<'PY'
import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get("id",""))
except Exception as e:
    print("", file=sys.stdout)
    print("[DEBUG] parse error:", e, file=sys.stderr)
PY
)

if [[ -z "$pid" ]]; then
  printf '[%s] bad_publish_response\n' "$(ts)" >&2
  printf '%s\n' "$publish" >&2
  exit 1
fi

printf '[%s] container=%s post=%s\n' "$(ts)" "$cid" "$pid"
SH

chmod +x ~/WANSTAGE/scripts/ig_post_now.sh


