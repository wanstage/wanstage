/* eslint-env node,commonjs */
/* eslint-disable @typescript-eslint/no-require-imports */
const PORT = process.env.PORT || 3001;
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(
    JSON.stringify({
      ok: true,
      service: 'wan-node-api',
      time: new Date().toISOString(),
    })
  );
});
server.listen(PORT, () => console.log(`[wan-node-api] listening on ${PORT}`));
