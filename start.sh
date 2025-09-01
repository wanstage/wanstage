#!/usr/bin/env bash
set -euo pipefail
cd ~/WANSTAGE

# --- load env ---
if [ -f .wanstage.env ]; then set -a; . ./.wanstage.env; set +a; fi

# --- ensure node deps ---
[ -d node_modules/@ngrok/ngrok ] || { npm init -y >/dev/null 2>&1 || true; npm i @ngrok/ngrok >/dev/null 2>&1; }

# --- create server-env.mjs if missing ---
[ -f server-env.mjs ] || cat > server-env.mjs <<'JS'
import http from "node:http";
import ngrok from "@ngrok/ngrok";
const PORT = Number(process.env.PORT || 8080);

const server = http.createServer((_, res) => {
  res.writeHead(200, {"Content-Type":"text/plain; charset=utf-8"});
  res.end(`WANSTAGE local server :${PORT}\n`);
});

server.on('error', (e) => {
  console.error('SERVER_ERROR', e?.code || e?.message || e);
  process.exit(2);
});

server.listen(PORT, async () => {
  console.log(`HTTP listening on http://localhost:${PORT}`);
  const listener = await ngrok.connect({ addr: PORT, authtoken_from_env: true });
  console.log(`Ingress established at: ${listener.url()}`);
});
JS

mkdir -p logs out

# --- run & parse URL ---
URL=""
node server-env.mjs | while read -r line; do
  echo "$line"
  if echo "$line" | grep -q "Ingress established at:"; then
    URL="$(echo "$line" | awk '{print $NF}')"
    echo "$URL" > .latest_tunnel_url

    # SNS captions
    TS=$(date +"%Y-%m-%d %H:%M:%S")
    ID=$(date +"autogen_%Y%m%d_%H%M%S")
    mkdir -p out
    cat > "out/${ID}_instagram.txt" <<TXT
【本日公開】外出先からでも検証OK✨
ワンクリックで接続：${URL}

今日は「1分で動くWANSTAGE環境」を公開中。
スマホから確認→問題あればDMください🙌

#WANSTAGE #在宅ワーク #時短 #検証リンク
TXT
    cat > "out/${ID}_threads.txt" <<TXT
WANSTAGEのトンネル出た！🎉
外からも動作チェックできるよ → ${URL}
今日中に軽く触って、感想ちょうだい🙏
TXT
    cat > "out/${ID}_line.txt" <<TXT
WANSTAGEトンネルURL
${URL}
（開けない時はもう一度起動してね）
TXT

    # Slack通知
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
      curl -s -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"WANSTAGEトンネルURL: ${URL}\"}" \
        "$SLACK_WEBHOOK_URL" >/dev/null || true
    fi

    # Zapier→LINE通知
    if [ -n "${ZAPIER_LINE_HOOK:-}" ]; then
      curl -s -X POST -H 'Content-Type: application/json' \
        -d "{\"message\":\"WANSTAGEトンネルURL: ${URL}\"}" \
        "$ZAPIER_LINE_HOOK" >/dev/null || true
    fi

    # 反応ログの初期行
    mkdir -p logs
    cat >> logs/post_log.jsonl <<LOG
{"autogen_id":"${ID}","timestamp":"${TS}","url":"${URL}","platforms":["Instagram","Threads","LINE"],"構文分類":["結論先出し","数字強調","ポジティブ"],"engagement":0,"save":0,"click":0}
LOG
  fi
done
