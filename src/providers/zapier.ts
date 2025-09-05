export type ZapierImage = { filename: string; data: string };

export async function postViaZapier(
  to: 'x' | 'instagram' | 'bluesky' | 'mastodon' | 'slack',
  text: string,
  image?: ZapierImage
) {
  const url = process.env.ZAPIER_HOOK_URL;
  if (!url) throw new Error('ZAPIER_HOOK_URL is not set');

  const payload: Record<string, unknown> = { to, text };
  if (image) payload.image = image;

  const r = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`Zapier error: ${await r.text()}`);
}
