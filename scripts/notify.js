const url = process.env.SLACK_WEBHOOK_URL;
if (!url) { console.error('SLACK_WEBHOOK_URL is missing'); process.exit(1); }

const text = `WANSTAGE 自動化OK ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}`;
await fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text })
}).then(async r => {
  if (!r.ok) { console.error('Slack error', await r.text()); process.exit(1); }
  console.log('Sent:', text);
});
