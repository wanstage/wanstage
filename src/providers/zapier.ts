export type ImagePayload = { filename: string; data: string } | undefined;

export async function postViaZapier(
  to: 'x' | 'instagram' | 'slack' | 'bluesky' | 'mastodon',
  text: string,
  image?: ImagePayload
) {
  const url = process.env.ZAPIER_HOOK_URL;
  if (!url) throw new Error('ZAPIER_HOOK_URL is not set');
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ to, text, image }),
  });
  if (!r.ok) throw new Error(`Zapier error: ${await r.text()}`);
}
