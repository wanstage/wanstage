import 'dotenv/config';
import express from 'express';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

import messageController from './controllers/message.js';
import enqueteController from './controllers/enquete.js';
import loginController from './controllers/login.js';

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use('/messages', messageController);
app.use('/api/enquetes', enqueteController);
app.use('/api/login', loginController);

const publicDir = (() => {
  const cands = [
    require('node:path').resolve(process.cwd(), 'public'),
    require('node:path').resolve(__dirname, 'public'),
  ];
  for (const c of cands) {
    try {
      if (fs.existsSync(c)) return c;
    } catch {}
  }
  return cands[0];
})();
app.use('/', express.static(publicDir));
app.get('/healthz', (_req, res) => res.status(200).send('ok'));
app.use((_req, res) => {
  res.status(200).sendFile(path.join(publicDir, 'index.html'));
});
app.get(/.*/, (_req, res) => {
  res.status(200).sendFile(path.join(publicDir, 'index.html'));
});

const port = Number(process.env.PORT) || 3000;
app.listen(port, () => {
  console.log(`ポート${port}番で起動したよ〜！`);
});

export default app;

app.use((_req, res) =>
  res.status(200).sendFile(path.join(publicDir, 'index.html'))
);

app.get('/healthz', (_req, res) => res.status(200).send('ok'));
