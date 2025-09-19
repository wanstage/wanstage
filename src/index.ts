import express = require('express');

type LinkRec = {
  code: string;
  url: string;
  tags: string[];
  created_at: string; // ISO
  clicks: number;
};

const app = express();
app.use(express.json());

// ===== APIキー保護（環境変数 API_KEY が設定されている時だけ有効） =====
const API_KEY = process.env.API_KEY;
app.use('/api', (req, res, next) => {
  if (!API_KEY) return next(); // 未設定なら素通り
  const got = req.header('x-api-key');
  if (got === API_KEY) return next();
  return res.status(401).json({ error: 'unauthorized' });
});

// ===== インメモリ永続もどき（SQLite化するまでの暫定） =====
const links = new Map<string, LinkRec>();

// ヘルスチェック
app.get('/healthz', (_req, res) => res.json({ ok: true }));

// 短縮の作成
app.post('/api/shorten', (req, res) => {
  const url = (req.body?.url ?? '').toString();
  if (!url) return res.status(400).json({ error: 'Missing url' });
  const code = Math.random().toString(36).slice(2, 8);
  const now = new Date().toISOString();
  const rec: LinkRec = { code, url, tags: [], created_at: now, clicks: 0 };
  links.set(code, rec);
  res.json({ code, shortUrl: `http://127.0.0.1:3000/${code}` });
});

// クリックでリダイレクト
app.get('/:code', (req, res) => {
  const rec = links.get(req.params.code);
  if (!rec) return res.status(404).send('Not found');
  rec.clicks += 1;
  res.redirect(rec.url);
});

// クリック数参照
app.get('/api/stats/:code', (req, res) => {
  const rec = links.get(req.params.code);
  if (!rec) return res.status(404).json({ error: 'not found' });
  res.json({ code: rec.code, clicks: rec.clicks });
});

// 一覧取得（from/to/cursor/page_size）
// cursor は base64("ISO|code")
function encodeCursor(d: string, c: string) {
  return Buffer.from(`${d}|${c}`).toString('base64');
}
function decodeCursor(s: string) {
  try {
    const [d, c] = Buffer.from(s, 'base64').toString('utf8').split('|');
    return { d, c };
  } catch {
    return null;
  }
}

app.get('/api/links', (req, res) => {
  const from = req.query.from ? new Date(String(req.query.from)) : null;
  const to = req.query.to ? new Date(String(req.query.to)) : null;
  const pageSize = Math.min(Number(req.query.page_size ?? 100), 1000);
  const cursorQ =
    typeof req.query.cursor === 'string' ? req.query.cursor : null;
  const after = cursorQ ? decodeCursor(cursorQ) : null;

  // 並び：created_at 降順、同時刻は code 降順
  const all = Array.from(links.values()).sort((a, b) => {
    if (a.created_at === b.created_at) return b.code.localeCompare(a.code);
    return b.created_at.localeCompare(a.created_at);
  });

  // 範囲フィルタ
  const filtered = all.filter((r) => {
    const t = new Date(r.created_at).getTime();
    if (from && t < from.getTime()) return false;
    if (to && t > to.getTime()) return false;
    return true;
  });

  // カーソル適用（after より“後ろ”を返す＝次ページ）
  const startIdx = after
    ? filtered.findIndex(
        (r) => r.created_at === after.d && r.code === after.c
      ) + 1
    : 0;

  const page = filtered.slice(startIdx, startIdx + pageSize);
  const next =
    startIdx + page.length < filtered.length
      ? encodeCursor(
          page[page.length - 1].created_at,
          page[page.length - 1].code
        )
      : null;

  res.json({
    data: page.map((r) => ({
      code: r.code,
      url: r.url,
      tags: r.tags,
      created_at: r.created_at,
      clicks: r.clicks,
    })),
    next,
  });
});

const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running at http://0.0.0.0:${PORT}`);
});
