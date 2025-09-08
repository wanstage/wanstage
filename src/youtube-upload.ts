import { google } from 'googleapis';
import fs from 'node:fs';

function getArg(name: string) {
  const hit = process.argv.find((a) => a.startsWith(`--${name}=`));
  return hit ? hit.split('=').slice(1).join('=') : '';
}

async function main() {
  const CLIENT_ID = process.env.YT_CLIENT_ID!;
  const CLIENT_SECRET = process.env.YT_CLIENT_SECRET!;
  const REFRESH_TOKEN = process.env.YT_REFRESH_TOKEN!;
  if (!CLIENT_ID || !CLIENT_SECRET || !REFRESH_TOKEN)
    throw new Error('Set YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN');

  const file = getArg('file');
  const title = getArg('title') || 'WANSTAGE 自動投稿';
  const description = getArg('description') || '';
  const tags = (getArg('tags') || '').split(',').filter(Boolean);
  const privacyStatus = getArg('privacy') || 'unlisted'; // public | private | unlisted

  if (!file || !fs.existsSync(file)) throw new Error(`file not found: ${file}`);

  const oauth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET);
  oauth2Client.setCredentials({ refresh_token: REFRESH_TOKEN });

  const youtube = google.youtube({ version: 'v3', auth: oauth2Client });

  const res = await youtube.videos.insert({
    part: ['snippet', 'status'],
    requestBody: {
      snippet: { title, description, tags },
      status: { privacyStatus },
    },
    media: { body: fs.createReadStream(file) as any },
  });

  console.log('✅ Uploaded. Video ID:', res.data.id);
}
main().catch((e) => {
  console.error(e);
  process.exit(1);
});
