#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/WANSTAGE"
LOGDIR="$ROOT/logs"; mkdir -p "$LOGDIR"
OUT_JSON="$LOGDIR/last_post.json"

# 0) .env 読み込み
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi

ts() { date '+%Y-%m-%d %H:%M:%S'; }

echo "[$(ts)] Generate post..." | tee -a "$LOGDIR/full_auto.log"

PROMPT=${POST_PROMPT:-"短くシンプルに作業効率アップの投稿文を書いてください"}
MODEL=${OPENAI_TEXT_MODEL:-"gpt-4o-mini"}

gen_text() {
  if command -v openai >/dev/null 2>&1; then
    RAW="$(openai api chat.completions.create -m "$MODEL" -g user "$PROMPT" 2>/dev/null || true)"
    if [ "${RAW#\{}" != "$RAW" ]; then
      if command -v jq >/dev/null 2>&1; then
        printf '%s' "$RAW" | jq -r '.choices[0].message.content // .choices[0].text // .output_text // empty'
      else
        printf '%s' "$RAW"
      fi
    else
      printf '%s' "$RAW"
    fi
  fi
}

TEXT="$(gen_text || true)"
if [ -z "${TEXT// }" ]; then
  TEXT="作業効率アップ：今日やることを3つに絞って、まず1つだけ終わらせよう。#生産性 #継続"
  ENGINE="fallback"
else
  ENGINE="openai"
fi

TS="$(ts)"
MODEL_USED="$MODEL"
cat > "$OUT_JSON" <<JSON
{
  "text": $(printf '%s' "$TEXT" | python3 - <<'PY'
import sys,json
print(json.dumps(sys.stdin.read().strip(), ensure_ascii=False))
PY
),
  "link_url": "",
  "variant": {"cta":"👉 続きはプロフのリンクから","link_label":"詳細＆特典はこちら","variant_id":"A"},
  "meta": {"engine": "$ENGINE", "model": "$MODEL_USED", "ts": "$TS"}
}
JSON

# Slack通知
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
  python3 - <<'PY' 2>/dev/null || true
import os, json, ssl, urllib.request
try:
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    ctx = ssl.create_default_context()

p=os.path.expanduser('~/WANSTAGE/logs/last_post.json')
j=json.load(open(p,encoding='utf-8'))
msg=j.get("text","").strip() or "（本文なし）"
wh=os.environ.get("SLACK_WEBHOOK_URL")
if wh:
    data=json.dumps({"text":msg}).encode('utf-8')
    req=urllib.request.Request(wh, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        print("[slack] status:", r.status)
else:
    print("[slack] SLACK_WEBHOOK_URL 未設定")
PY
else
  echo "[slack] SKIP (SLACK_WEBHOOK_URL 未設定)"
fi

echo "[$(ts)] done." | tee -a "$LOGDIR/full_auto.log"
