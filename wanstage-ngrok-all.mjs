import http from 'node:http';
import ngrok from '@ngrok/ngrok';

const PORT = process.env.PORT || 8080;

const server = http.createServer((_, res) => {
  res.writeHead(200, {'Content-Type':'text/plain; charset=utf-8'});
  res.end('WANSTAGE local server :8080\n');
}).listen(PORT, async () => {
  console.log(`HTTP listening on http://localhost:${PORT}`);
  const listener = await ngrok.connect({ addr: PORT }); // yml から authtoken を読む
  console.log(`Ingress established at: ${listener.url()}`);
});
