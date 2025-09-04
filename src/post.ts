import 'dotenv/config';
import { postToSlack } from './providers/slack.js';

async function main() {
  const msg =
    process.argv.slice(2).join(' ') ||
    `定期投稿 ${new Date().toLocaleString('ja-JP', {
      timeZone: process.env.TZ || 'Asia/Tokyo',
    })}`;
  await postToSlack(msg);
  console.log('Posted:', msg);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
