import Database = require('better-sqlite3');
import fs from 'fs';
import path from 'path';

const DB_PATH = process.env.DB_PATH || path.join(process.cwd(), 'wanstage.db');
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.exec(`
CREATE TABLE IF NOT EXISTS links(
  code TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  tags_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS clicks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
`);

export type LinkRow = {
  code: string;
  url: string;
  tags_json: string;
  created_at: string;
};
function parseTags(tags_json: string): string[] {
  try {
    const v = JSON.parse(tags_json);
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

export function upsertLink(code: string, url: string, tags: string[] = []) {
  const stmt = db.prepare(`
    INSERT INTO links(code,url,tags_json)
    VALUES(@code,@url,@tags_json)
    ON CONFLICT(code) DO UPDATE SET url=excluded.url, tags_json=excluded.tags_json
  `);
  stmt.run({ code, url, tags_json: JSON.stringify(tags) });
}

export function addClick(code: string) {
  db.prepare(`INSERT INTO clicks(code) VALUES (?)`).run(code);
}

export function getClicksTotal(code: string): number {
  const r = db
    .prepare(`SELECT COUNT(*) AS n FROM clicks WHERE code=?`)
    .get(code) as { n: number };
  return r?.n ?? 0;
}

export function getLink(code: string) {
  const r = db.prepare(`SELECT * FROM links WHERE code=?`).get(code) as
    | LinkRow
    | undefined;
  if (!r) return null;
  return {
    code: r.code,
    url: r.url,
    tags: parseTags(r.tags_json),
    created_at: r.created_at,
  };
}

export function getLinksPaginated(params: {
  from?: string;
  to?: string;
  limit?: number;
  cursor?: string;
  q?: string;
}) {
  const limit = Math.min(Math.max(params.limit ?? 50, 1), 200);
  const where: string[] = [];
  const args: any[] = [];

  if (params.from) {
    where.push(`datetime(created_at) >= datetime(?)`);
    args.push(params.from);
  }
  if (params.to) {
    where.push(`datetime(created_at) < datetime(?)`);
    args.push(params.to + 'T23:59:59');
  }
  if (params.cursor) {
    where.push(`created_at < ?`);
    args.push(params.cursor);
  }
  if (params.q && params.q.trim()) {
    where.push(`(code LIKE ? OR url LIKE ? OR tags_json LIKE ?)`);
    const like = `%${params.q.trim()}%`;
    args.push(like, like, like);
  }

  const whereSql = where.length ? `WHERE ${where.join(' AND ')}` : '';
  const rows = db
    .prepare(
      `
    SELECT * FROM links
    ${whereSql}
    ORDER BY datetime(created_at) DESC
    LIMIT ?
  `
    )
    .all(...args, limit + 1) as LinkRow[];

  const hasMore = rows.length > limit;
  const slice = rows.slice(0, limit);
  const data = slice.map((r) => ({
    code: r.code,
    url: r.url,
    tags: parseTags(r.tags_json),
    created_at: r.created_at,
    clicks: getClicksTotal(r.code),
  }));
  const next = hasMore ? slice[slice.length - 1]?.created_at : null;
  return { data, next };
}

export function updateLinkUrl(code: string, url: string) {
  const r = db.prepare(`UPDATE links SET url=? WHERE code=?`).run(url, code);
  return r.changes > 0;
}

export function updateTags(
  code: string,
  op: 'add' | 'remove' | 'replace',
  tags: string[]
) {
  const row = db
    .prepare(`SELECT tags_json FROM links WHERE code=?`)
    .get(code) as { tags_json: string } | undefined;
  if (!row) return false;
  let current = parseTags(row.tags_json);

  if (op === 'add') {
    const set = new Set([...current, ...tags]);
    current = [...set];
  } else if (op === 'remove') {
    const rm = new Set(tags);
    current = current.filter((t) => !rm.has(t));
  } else if (op === 'replace') {
    current = [...new Set(tags)];
  }
  db.prepare(`UPDATE links SET tags_json=? WHERE code=?`).run(
    JSON.stringify(current),
    code
  );
  return true;
}

export function deleteLink(code: string) {
  db.prepare(`DELETE FROM clicks WHERE code=?`).run(code);
  const r = db.prepare(`DELETE FROM links WHERE code=?`).run(code);
  return r.changes > 0;
}
