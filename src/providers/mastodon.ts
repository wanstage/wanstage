import { File, FormData } from 'formdata-node';
import { Readable as _Readable } from 'node:stream';
import { fileURLToPath as _fileURLToPath } from 'node:url';
import { lookup as mimeLookup } from 'mime-types';
import { request } from 'undici';
import { readFile } from 'node:fs/promises';
import { basename } from 'node:path';

type ImagePayload = { path?: string; bytes?: Uint8Array; mimeType?: string };

async function uploadMedia(
  base: string,
  token: string,
  image: ImagePayload
): Promise<string> {
  const fd = new FormData();
  if (image.path) {
    const buf = await readFile(image.path);
    const mime =
      image.mimeType ||
      (mimeLookup(image.path) || 'application/octet-stream').toString();
    const file = new File([buf], basename(image.path), { type: mime });
    fd.set('file', file);
  } else if (image.bytes) {
    const mime = image.mimeType || 'application/octet-stream';
    const file = new File([image.bytes], 'image', { type: mime });
    fd.set('file', file);
  } else {
    throw new Error('No image provided');
  }
  const res = await request(`${base}/api/v2/media`, {
    method: 'POST',
    body: fd as any,
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.statusCode >= 300)
    throw new Error(
      `media upload failed: ${res.statusCode} ${await res.body.text()}`
    );
  const json: any = await res.body.json();
  return json.id as string;
}

export async function postToMastodon(
  text: string,
  opts?: { image?: ImagePayload }
) {
  const base = process.env.MASTO_BASE_URL;
  const token = process.env.MASTO_TOKEN;
  if (!base || !token) throw new Error('MASTO_* not set');

  const body: any = { status: text, visibility: 'public' };
  if (opts?.image) {
    const mediaId = await uploadMedia(base, token, opts.image);
    body.media_ids = [mediaId];
  }

  const res = await request(`${base}/api/v1/statuses`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (res.statusCode >= 300)
    throw new Error(`post failed: ${res.statusCode} ${await res.body.text()}`);
  return await res.body.json();
}
