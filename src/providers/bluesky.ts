import { AtpAgent } from '@atproto/api';
import { readFile } from 'node:fs/promises';
import { basename } from 'node:path';

export async function postToBluesky(
  text: string,
  opts?: { imagePath?: string }
) {
  const id = process.env.BSKY_IDENTIFIER;
  const pw = process.env.BSKY_PASSWORD;
  if (!id || !pw) throw new Error('BSKY_* not set');

  const agent = new AtpAgent({ service: 'https://bsky.social' });
  await agent.login({ identifier: id, password: pw });

  let embed: any = undefined;
  if (opts?.imagePath) {
    const bytes = new Uint8Array(await readFile(opts.imagePath));
    const upload = await agent.uploadBlob(bytes, { encoding: 'image/jpeg' }); // 画像種別は必要に応じ変更
    embed = {
      $type: 'app.bsky.embed.images',
      images: [{ alt: basename(opts.imagePath), image: upload.data.blob }],
    };
  }
  const record: any = {
    $type: 'app.bsky.feed.post',
    text,
    createdAt: new Date().toISOString(),
  };
  if (embed) record.embed = embed;

  const res = await agent.post(record);
  return res;
}
