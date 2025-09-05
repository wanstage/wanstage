import 'dotenv/config';
import { postToSlack } from './providers/slack.ts';
import { postToX } from './providers/x.ts';
import { postToInstagram } from './providers/instagram.ts';
import { postToMastodon } from './providers/mastodon.ts';
import { postViaZapier } from './providers/zapier.ts';
import { readFile } from 'node:fs/promises';

function pickTarget(): 'slack' | 'x' | 'instagram' | 'bluesky' | 'mastodon' {
  const toArg = process.argv.find((a) => a.startsWith('--to=')) || '';
  const to = toArg.replace('--to=', '').toLowerCase();
  if (['slack', 'x', 'instagram', 'bluesky', 'mastodon'].includes(to))
    return to as any;
  return 'slack';
}
function addDatePrefix(s: string) {
  return `[${new Date().toLocaleString('ja-JP', { timeZone: process.env.TZ || 'Asia/Tokyo' })}] ${s}`;
}
function addHashtags(s: string, tags?: string) {
  if (!tags) return s;
  const list = tags
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
  if (!list.length) return s;
  const line = list.map((t) => (t.startsWith('#') ? t : `#${t}`)).join(' ');
  return `${s} ${line}`.trim();
}
async function maybeBuildImagePayload(imagePath?: string) {
  if (!imagePath) return undefined;
  const bytes = new Uint8Array(await readFile(imagePath));
  return { path: imagePath, bytes, mimeType: undefined as string | undefined };
}

async function main() {
  const args = process.argv.slice(2).filter((a) => !a.startsWith('--to='));
  const opts = Object.fromEntries(
    process.argv
      .slice(2)
      .filter((a) => a.startsWith('--'))
      .map((a) => {
        const [k, v = ''] = a.replace(/^--/, '').split('=');
        return [k, v];
      })
  ) as Record<string, string>;

  const target = pickTarget();
  const msgRaw =
    args.filter((a) => !a.startsWith('--')).join(' ') ||
    `定期投稿 ${new Date().toISOString()}`;
  const withDate = 'dateprefix' in opts ? addDatePrefix(msgRaw) : msgRaw;
  const finalMsg = addHashtags(
    withDate,
    opts.hashtags || process.env.DEFAULT_HASHTAGS
  );

  const imagePayload = await maybeBuildImagePayload(opts.image);

  // 直投（秘密が揃っていれば）：X / IG / Mastodon
  if (target === 'x' && process.env.X_APP_KEY) {
    await postToX(finalMsg);
    console.log(`Posted(x):`, finalMsg);
    return;
  }
  if (target === 'instagram' && process.env.IG_USER_ID) {
    await postToInstagram(finalMsg);
    console.log(`Posted(ig):`, finalMsg);
    return;
  }
  if (
    target === 'mastodon' &&
    process.env.MASTO_BASE_URL &&
    process.env.MASTO_TOKEN
  ) {
    await postToMastodon(finalMsg, { image: imagePayload });
    console.log(`Posted(mastodon):`, finalMsg);
    return;
  }

  // Slack はローカル直投（従来どおり）
  if (target === 'slack') {
    await postToSlack(finalMsg);
    console.log(`Posted(slack):`, finalMsg);
    return;
  }

  // その他/鍵不足 → Zapier 経由で中継
  if (!process.env.ZAPIER_HOOK_URL)
    throw new Error(
      `${target.toUpperCase()} secrets are missing and ZAPIER_HOOK_URL not set`
    );
  await postViaZapier(target as any, finalMsg, imagePayload);
  console.log(`Posted(zapier→${target}):`, finalMsg);
}
main().catch((e) => {
  console.error(e);
  process.exit(1);
});
