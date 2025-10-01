#!/usr/bin/env bash
set -euo pipefail

echo "---- wrangler.toml ----"
cat wrangler.toml

# Workerエントリファイルがなければ作成
if [ ! -f cf-worker-notify/src/index.js ]; then
  mkdir -p cf-worker-notify/src
  cat > cf-worker-notify/src/index.js <<'JS'
addEventListener('fetch', e => e.respondWith(handle(e.request)));
async function handle(req) {
  const url = new URL(req.url);
  if (url.pathname === '/health') {
    return new Response(JSON.stringify({status:'ok'}), {
      headers: {'content-type': 'application/json'}
    });
  }
  return new Response('wan-notify-relay');
}
JS
fi

git add wrangler.toml cf-worker-notify/src/index.js
git commit -m "fix(worker): clean wrangler.toml & ensure /health" || true
git push

# 最新の Actions run ID を取る
RUN_ID="$(gh run list -L 10 --json databaseId,workflowName,status \
  --jq '.[] | select(.workflowName==".github/workflows/worker-deploy.yml") | .databaseId' | head -1 || true)"

if [ -z "$RUN_ID" ]; then
  RUN_ID="$(gh run list -L 1 --json databaseId --jq '.[0].databaseId' || true)"
fi

if [ -z "$RUN_ID" ]; then
  echo "⚠ RUN_IDが取得できません。GitHub Actionsの実行が見つからないかも。"
  exit 1
fi

gh run watch "$RUN_ID" || true

WORKER_URL="$(
  gh run view "$RUN_ID" --log 2>/dev/null \
  | grep -Eo 'https://[a-z0-9-]+\.workers\.dev' \
  | head -1
)"

echo "WORKER_URL=${WORKER_URL:-<not-found>}"

if [ -n "$WORKER_URL" ]; then
  echo -n "health: "
  curl -fsS "$WORKER_URL/health" && echo || echo "NG"
fi
