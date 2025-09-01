import http from 'node:http';
const PORT = process.env.PORT || 8080;
const server = http.createServer((_, res) => {
  res.writeHead(200, {'Content-Type':'text/plain; charset=utf-8'});
  res.end('WANSTAGE local server :8080\n');
});
server.listen(PORT, () => console.log(`HTTP listening on http://localhost:${PORT}`));
