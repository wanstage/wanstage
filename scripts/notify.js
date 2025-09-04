import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const url = process.env.SLACK_WEBHOOK_URL;
if (!url) {
  console.error('SLACK_WEBHOOK_URL is missing');
  process.exit(1);
}

const payload = { text: `WANSTAGE OK ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}` };

const res = await fetch(url, {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify(payload),
});

if (!res.ok) {
  console.error('Slack error', await res.text());
  process.exit(1);
}

const userDir = join(process.env.HOME, 'Library', 'Application Support', 'Code', 'User');
writeFileSync(join(userDir, 'wanstage-last-notify.txt'), new Date().toISOString());
console.log('Sent:', payload.text);
