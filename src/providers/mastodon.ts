import { readFile } from 'node:fs/promises';

/**
 * Mastodon に投稿（画像は任意）
 * 必要な環境変数:
 *   - MASTO_INSTANCE 例: "mstdn.jp"
 *   - MASTO_TOKEN    (アクセストークン)
 */
export async function postToMastodon(
  text: string,
  opts?: { imagePath?: string; mimeType?: string }
) {
  const instance = process.env.MASTO_INSTANCE;
  const token = process.env.MASTO_TOKEN;
  if (!instance || !token) {
    throw new Error('MASTO_INSTANCE or MASTO_TOKEN missing');
  }

  // 画像があれば先に media をアップロード
  let mediaId: string | undefined;
  if (opts?.imagePath) {
    const bytes = await readFile(opts.imagePath); // Buffer (Uint8Array)
    // Buffer の使用領域だけを ArrayBuffer に切り出す（型エラー回避）
    const ab = bytes.buffer.slice(
      bytes.byteOffset,
      bytes.byteOffset + bytes.byteLength
    );
    const mime = opts.mimeType ?? 'image/jpeg';

    const mediaForm = new FormData();
    mediaForm.append('file', new Blob([ab], { type: mime }), 'image');

    const up = await fetch(`https://${instance}/api/v2/media`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: mediaForm,
    });
    if (!up.ok)
      throw new Error(`Mastodon media upload error: ${await up.text()}`);
    const uploaded = (await up.json()) as { id: string };
    mediaId = uploaded.id;
  }

  const statusForm = new FormData();
  statusForm.append('status', text);
  if (mediaId) statusForm.append('media_ids[]', mediaId);

  const res = await fetch(`https://${instance}/api/v1/statuses`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: statusForm,
  });
  if (!res.ok) throw new Error(`Mastodon post error: ${await res.text()}`);
}
