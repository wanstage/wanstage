import { google } from 'googleapis';

function startOfNDaysAgo(n: number) {
  const d = new Date(); d.setDate(d.getDate()-n);
  d.setHours(0,0,0,0); return d;
}
function inLast7Days(tsJst: string) {
  // JST文字列が来る想定。Date.parseでUTC扱いになるが7日程度の集計なら許容
  const t = new Date(tsJst); return t >= startOfNDaysAgo(7);
}
async function postToSlack(webhook: string, text: string) {
  const r = await fetch(webhook, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ text }) });
  if (!r.ok) throw new Error(await r.text());
}
(async () => {
  const SHEET_ID = process.env.SHEET_ID!;
  const SLACK = process.env.SLACK_WEBHOOK_URL!;
  const auth = new google.auth.GoogleAuth({
    credentials: JSON.parse(process.env.GCP_SA_JSON!),
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });
  const sheets = google.sheets({ version:'v4', auth });
  const range = 'A:G'; // timestamp_jst..route
  const res = await sheets.spreadsheets.values.get({ spreadsheetId: SHEET_ID, range });
  const rows = (res.data.values||[]).slice(1); // drop header
  const recent = rows.filter(r => inLast7Days(r[0] || ''));
  const byPlatform = new Map<string, number>();
  for (const r of recent) {
    const p = (r[1]||'').toLowerCase();
    byPlatform.set(p, (byPlatform.get(p)||0)+1);
  }
  const total = recent.length;
  const lines = [`📊 WANSTAGE 直近7日レポート（投稿数）: ${total}件`];
  for (const [p,c] of byPlatform) lines.push(`- ${p}: ${c}`);
  await postToSlack(SLACK, lines.join('\n'));
  console.log('Report sent.');
})().catch(e=>{ console.error(e); process.exit(1); });
