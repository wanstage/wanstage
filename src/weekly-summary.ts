import 'dotenv/config';
import { google } from 'googleapis';

type Row = Record<string, string>;

function parseRows(values: string[][]): Row[] {
  if (!values || values.length < 2) return [];
  const header = values[0].map((h) => h.trim().toLowerCase());
  return values.slice(1).map((r) => {
    const o: Row = {};
    header.forEach((h, i) => {
      o[h] = (r[i] ?? '').trim();
    });
    return o;
  });
}

function pick<T = string>(
  row: Row,
  candidates: string[],
  fallback: T | null = null
): T | null {
  for (const k of candidates) {
    const v = row[k.toLowerCase()];
    if (v !== undefined && v !== '') return v as unknown as T;
  }
  return fallback;
}

function toDateOrNull(s?: string | null) {
  if (!s) return null;
  const d = new Date(s);
  return isNaN(+d) ? null : d;
}

async function main() {
  const SHEET_ID = process.env.SHEET_ID!;
  if (!SHEET_ID) throw new Error('SHEET_ID is not set');

  // 認証は B64 / JSON / FILE のどれか
  const rawB64 = process.env.GOOGLE_SERVICE_ACCOUNT_B64;
  const rawJson = process.env.GOOGLE_SERVICE_ACCOUNT_JSON;
  const rawFile = process.env.GOOGLE_SERVICE_ACCOUNT_FILE;

  let creds: any;
  if (rawB64) creds = JSON.parse(Buffer.from(rawB64, 'base64').toString());
  else if (rawJson) creds = JSON.parse(rawJson);
  else if (rawFile)
    creds = JSON.parse(
      await (await import('fs/promises')).readFile(rawFile, 'utf8')
    );
  else throw new Error('Set one of GOOGLE_SERVICE_ACCOUNT_B64 / JSON / FILE');

  const auth = new google.auth.GoogleAuth({
    credentials: {
      client_email: creds.client_email,
      private_key: creds.private_key,
    },
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const sheets = google.sheets({ version: 'v4', auth });
  const range = 'A:Z'; // 1番目のシート全列想定
  const resp = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range,
  });
  const rows = parseRows(resp.data.values ?? []);

  // 列候補
  const timeKeys = ['timestamp', 'time', 'date'];
  const targetKeys = ['target', 'platform', 'to'];
  const msgKeys = ['message', 'text', 'body'];
  const tagsKeys = ['hashtags', 'tags'];
  const clicksKeys = ['clicks', 'click', 'ctr_clicks'];

  // 期間フィルタ
  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 3600 * 1000);

  const clean = rows
    .map((r) => {
      const tsStr = pick<string>(r, timeKeys, '') || '';
      const ts = toDateOrNull(tsStr) ?? toDateOrNull(r['created_at'] ?? null);
      return {
        ts,
        target: (pick<string>(r, targetKeys, '') || '').toLowerCase(),
        message: pick<string>(r, msgKeys, '') || '',
        hashtags: pick<string>(r, tagsKeys, '') || '',
        clicks: Number(pick<string>(r, clicksKeys, '0') || '0') || 0,
        raw: r,
      };
    })
    .filter((x) => x.target); // target が空は除外

  const total = clean.length;
  const last7 = clean.filter((x) => x.ts && x.ts >= sevenDaysAgo).length;

  // 送信先別
  const perTarget = new Map<string, number>();
  for (const r of clean)
    perTarget.set(r.target, (perTarget.get(r.target) || 0) + 1);
  const perTargetStr = [...perTarget.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${k}: ${v}`)
    .join(', ');

  // クリック合計（あれば）
  const totalClicks = clean.reduce((a, b) => a + (b.clicks || 0), 0);

  // ハッシュタグTop3（複数カンマ/空白区切り対応）
  const tagCount = new Map<string, number>();
  for (const r of clean) {
    const raw = r.hashtags;
    if (!raw) continue;
    const parts = raw
      .split(/[, \n]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    for (const t of parts) tagCount.set(t, (tagCount.get(t) || 0) + 1);
  }
  const topTags = [...tagCount.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([t, c]) => `#${t}(${c})`)
    .join(' ');

  // サンプル投稿（直近1件）
  const latest = [...clean].sort(
    (a, b) => (b.ts?.getTime() || 0) - (a.ts?.getTime() || 0)
  )[0];

  const lines = [
    `🧾 *週次サマリー*`,
    `・総投稿数: ${total}`,
    `・直近7日: ${last7}`,
    perTargetStr ? `・内訳: ${perTargetStr}` : ``,
    totalClicks ? `・クリック合計: ${totalClicks}` : ``,
    topTags ? `・ハッシュタグTop3: ${topTags}` : ``,
    latest
      ? `・直近: [${latest.target}] ${latest.message.slice(0, 80)}${latest.message.length > 80 ? '…' : ''}`
      : ``,
  ].filter(Boolean);

  const msg = lines.join('\n');
  await postSlack(msg);
}

async function postSlack(text: string) {
  const url = process.env.SLACK_WEBHOOK_URL;
  if (!url) {
    console.log('[dryrun] SLACK_WEBHOOK_URL 未設定\n' + text);
    return;
  }
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Slack error: ${await res.text()}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
