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
