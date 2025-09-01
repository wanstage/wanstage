import http from "node:http";
import ngrok from "@ngrok/ngrok";
const PORT = 8080;
const server = http.createServer((_, res) => {
  res.writeHead(200, {"Content-Type":"text/plain; charset=utf-8"});
  res.end("WANSTAGE local server :8080\n");
});
server.listen(PORT, async () => {
  console.log(`HTTP listening on http://localhost:${PORT}`);
  const listener = await ngrok.connect({ addr: PORT, authtoken_from_env: true });
  console.log(`Ingress established at: ${listener.url()}`);
});
