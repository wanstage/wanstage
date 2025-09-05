const V = 'v21.0'; // Graph API version (必要に応じて更新)

export async function postToInstagram(text: string) {
  const { IG_USER_ID, IG_ACCESS_TOKEN } = process.env;
  if (!IG_USER_ID || !IG_ACCESS_TOKEN) {
    throw new Error('IG_USER_ID or IG_ACCESS_TOKEN missing');
  }

  // テキストのみ（画像なし）
  const createRes = await fetch(
    `https://graph.facebook.com/${V}/${IG_USER_ID}/media?access_token=${IG_ACCESS_TOKEN}`,
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ caption: text }),
    }
  );
  if (!createRes.ok)
    throw new Error(`IG create media error: ${await createRes.text()}`);
  const { id } = (await createRes.json()) as { id: string };

  const publishRes = await fetch(
    `https://graph.facebook.com/${V}/${IG_USER_ID}/media_publish?access_token=${IG_ACCESS_TOKEN}`,
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ creation_id: id }),
    }
  );
  if (!publishRes.ok)
    throw new Error(`IG publish error: ${await publishRes.text()}`);
}
