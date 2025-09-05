import { readFile } from 'node:fs/promises';
import { basename, extname } from 'node:path';
import { postToSlack } from './providers/slack.ts';
import { postViaZapier, ZapierImage } from './providers/zapier.ts';

function pickArg(flag: string): string | undefined {
  const m = process.argv.find((a) => a.startsWith(`--${flag}=`));
  return m ? m.replace(`--${flag}=`, '') : undefined;
}
function hasFlag(flag: string): boolean {
  return process.argv.includes(`--${flag}`);
}
function mimeFromExt(p: string): string {
  const e = extname(p).toLowerCase();
  if (e === '.jpg' || e === '.jpeg') return 'image/jpeg';
  if (e === '.png') return 'image/png';
  if (e === '.gif') return 'image/gif';
  if (e === '.webp') return 'image/webp';
  return 'application/octet-stream';
}

async function buildZapierImage(
  imagePath?: string
): Promise<ZapierImage | undefined> {
  if (!imagePath) return undefined;
  const buf = await readFile(imagePath);
  const mime = mimeFromExt(imagePath);
  const b64 = Buffer.from(buf).toString('base64');
  return {
    filename: basename(imagePath),
    data: `data:${mime};base64,${b64}`,
  };
}

function decorateMessage(raw: string): string {
  const parts: string[] = [];
  if (hasFlag('dateprefix')) {
    const stamp = new Date()
      .toLocaleString('ja-JP', { timeZone: process.env.TZ || 'Asia/Tokyo' })
      .replace(/\//g, '/');
    parts.push(`[${stamp}]`);
  }
  parts.push(raw);

  const hs = pickArg('hashtags') ?? process.env.DEFAULT_HASHTAGS ?? '';
  const tags = hs
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  if (tags.length)
    parts.push(tags.map((t) => (t.startsWith('#') ? t : `#${t}`)).join(' '));

  return parts.join(' ');
}

function pickTarget(): 'slack' | 'x' | 'instagram' | 'bluesky' | 'mastodon' {
  const to = (pickArg('to') ?? 'slack').toLowerCase();
  if (['slack', 'x', 'instagram', 'bluesky', 'mastodon'].includes(to))
    return to as any;
  return 'slack';
}

async function main() {
  const target = pickTarget();
  const imagePath = pickArg('image');
  const msgArg = process.argv
    .filter((a) => !a.startsWith('--'))
    .slice(2)
    .join(' ');
  const message = msgArg || `定期投稿 ${new Date().toISOString()}`;
  const finalMsg = decorateMessage(message);
  const zapierImage = await buildZapierImage(imagePath);

  // Slack はローカル直投
  if (target === 'slack') {
    await postToSlack(finalMsg);
    console.log(`Posted(slack):`, finalMsg);
    return;
  }

  // それ以外は Zapier 経由（鍵が無くても動く）
  await postViaZapier(target, finalMsg, zapierImage);
  console.log(`Posted(zapier→${target}):`, finalMsg);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
