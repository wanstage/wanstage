#!/usr/bin/env zsh
set -Eeuo pipefail
create_tmp=""; publish_tmp=""
log(){ printf '[%s] %s\n' "$(date '+%F %T')" "$*" ; }
fail(){ log "ERROR: $*"; exit 1; }
if [ -f "$HOME/WANSTAGE/.env" ]; then
  perl -0777 -ne 'BEGIN{$/=undef;} s/\x{3000}/ /g; s/[\x00-\x08\x0B\x0C\x0E-\x1F]//g; print $_;' \
    "$HOME/WANSTAGE/.env" > "$HOME/WANSTAGE/.env._norm" 2>/dev/null || true
  set -a; source "$HOME/WANSTAGE/.env._norm" 2>/dev/null || source "$HOME/WANSTAGE/.env"; set +a
fi

: "${IG_USER_ID:?IG_USER_ID not set}"
: "${IG_ACCESS_TOKEN:?IG_ACCESS_TOKEN not set}"
: "${IMAGE_URL:?IMAGE_URL not set}"
: "${CAPTION:?CAPTION not set}"
# バックアップ
cp -p ~/WANSTAGE/scripts/ig_post_now.sh ~/WANSTAGE/scripts/ig_post_now.sh.bak_$(date +%Y%m%d_%H%M%S)

# デバッグ版に差し替え（無言禁止・HTTP/JSON必ず出す）
cat > ~/WANSTAGE/scripts/ig_post_now.sh <<'SH'
#!/bin/bash
set -Eeuo pipefail

create_tmp=""; publish_tmp=""
log(){ printf '[%s] %s\n' "$(date '+%F %T')" "$*" ; }
fail(){ log "ERROR: $*"; exit 1; }

# .env 読み込み（全角スペース除去）
if [ -f "$HOME/WANSTAGE/.env" ]; then
  perl -0777 -ne 'BEGIN{$/=undef;} s/\x{3000}/ /g; s/[\x00-\x08\x0B\x0C\x0E-\x1F]//g; print $_;' \
    "$HOME/WANSTAGE/.env" > "$HOME/WANSTAGE/.env._norm" 2>/dev/null || true
  set -a; source "$HOME/WANSTAGE/.env._norm" 2>/dev/null || source "$HOME/WANSTAGE/.env"; set +a
fi

: "${IG_USER_ID:?IG_USER_ID not set}"
: "${IG_ACCESS_TOKEN:?IG_ACCESS_TOKEN not set}"
: "${IMAGE_URL:?IMAGE_URL not set}"
: "${CAPTION:?CAPTION not set}"

http() { # http <method> <url> [--data ...]
  method="$1"; shift
  url="$1"; shift
  curl -sS -X "$method" "$url" "$@" \
       -H "Accept: application/json" \
       --write-out "\n__HTTP_CODE__:%{http_code}\n"
}

# 0) 環境確認
log "IG_USER_ID=$(printf '%s' "$IG_USER_ID" | sed -E 's/^(.{3}).*(.{3})$/\1***\2/;t;s/.*/SET/')"
log "TOKEN_LEN=${#IG_ACCESS_TOKEN}"
log "IMAGE_URL=$IMAGE_URL"
log "CAPTION=$(printf '%s' "$CAPTION" | head -c 40)"

# 1) ユーザー確認
log "Step1: GET id,username"
resp="$(http GET "https://graph.facebook.com/v21.0/$IG_USER_ID?fields=id,username&access_token=$IG_ACCESS_TOKEN")" || true
printf '%s\n' "$resp"
code="$(printf '%s' "$resp" | awk -F: '/__HTTP_CODE__/{print $2}')"
[ "$code" = "200" ] || fail "user lookup http=$code"

# 2) メディア作成（ドライラン許可）
log "Step2: create media container"
resp="$(http POST "https://graph.facebook.com/v21.0/$IG_USER_ID/media?access_token=$IG_ACCESS_TOKEN" \
        --data-urlencode "image_url=$IMAGE_URL" \
        --data-urlencode "caption=$CAPTION")" || true
printf '%s\n' "$resp"
code="$(printf '%s' "$resp" | awk -F: '/__HTTP_CODE__/{print $2}')"
[ "$code" = "200" ] || fail "media create http=$code"
creation_id="$(printf '%s' "$resp" | sed -n 's/.*"id":"\{0,1\}\([^"]*\)".*/\1/p' | head -n1)"
[ -n "${creation_id:-}" ] || fail "no creation_id"

# 3) 公開（本番実行）
log "Step3: publish"
resp="$(http POST "https://graph.facebook.com/v21.0/$IG_USER_ID/media_publish?access_token=$IG_ACCESS_TOKEN" \
        --data-urlencode "creation_id=$creation_id")" || true
printf '%s\n' "$resp"
code="$(printf '%s' "$resp" | awk -F: '/__HTTP_CODE__/{print $2}')"
[ "$code" = "200" ] || fail "publish http=$code"

log "DONE"
