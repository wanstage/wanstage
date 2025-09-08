export async function postViaZapier(
  to: 'x' | 'instagram' | 'bluesky' | 'mastodon' | 'slack',
  text: string,
  opts?: { image?: { filename: string; data: string }; video_name?: string }
) {
  const url = process.env.ZAPIER_HOOK_URL;
  if (!url) throw new Error('ZAPIER_HOOK_URL is not set');

  const body: any = { to, text };
  if (opts?.image) body.image = opts.image;
  if (opts?.video_name) body.video_name = opts.video_name;

  const r = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`Zapier error: ${await r.text()}`);
}
