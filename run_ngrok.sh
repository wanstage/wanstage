#!/usr/bin/env bash
set -euo pipefail
cd ~/WANSTAGE

echo "Paste your ngrok authtoken and press Enter:"
IFS= read -r NGROK_AUTHTOKEN
[ -n "$NGROK_AUTHTOKEN" ] || { echo "no token"; exit 1; }

mkdir -p "$HOME/Library/Application Support/ngrok"
cat > "$HOME/Library/Application Support/ngrok/ngrok.yml" <<EOF
version: "3"
authtoken: "$NGROK_AUTHTOKEN"
EOF
chmod 600 "$HOME/Library/Application Support/ngrok/ngrok.yml"

[ -d node_modules/@ngrok/ngrok ] || { npm init -y >/dev/null 2>&1 || true; npm i @ngrok/ngrok >/dev/null 2>&1; }

cat > wanstage-ngrok-all.mjs <<'EOF'
import http from 'node:http';
import ngrok from '@ngrok/ngrok';

const tryStart = (port) => new Promise((resolve, reject) => {
  const server = http.createServer((_, res) => {
    res.writeHead(200, {'Content-Type':'text/plain; charset=utf-8'});
    res.end(`WANSTAGE local server :${port}\n`);
  });
  server.once('error', reject);
  server.listen(port, async () => {
    console.log(`HTTP listening on http://localhost:${port}`);
    const listener = await ngrok.connect({ addr: port });
    console.log(`Ingress established at: ${listener.url()}`);
    resolve();
  });
});

const ports = [8090, 8080, 3000, 8000];
for (const p of ports) {
  try { await tryStart(p); process.exit(0); } catch (e) { continue; }
}
console.error('No available port among: ' + ports.join(', '));
process.exit(1);
EOF

node wanstage-ngrok-all.mjs
