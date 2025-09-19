import dotenv from 'dotenv';
import fs from 'fs';
import { google } from 'googleapis';
import minimist from 'minimist';

// ENV を上書きしないで段階読み（ENV_FILE > .env.youtube > .env）
dotenv.config({ path: process.env.ENV_FILE || '.env', override: false });
dotenv.config({ path: '.env.youtube', override: false });
dotenv.config({ path: '.env', override: false });

const args = minimist(process.argv.slice(2), {
  string: ['title','desc','privacy','tags','file'],
  alias: { t:'title', d:'desc', p:'privacy', f:'file' },
  default: { privacy: 'unlisted' },
});

const filePath = args.file || args._[0];
const title = args.title || 'WANSTAGE Auto Upload';
const description = args.desc || 'Uploaded via WANSTAGE automation';
const tags = args.tags ? String(args.tags).split(',').map(s=>s.trim()).filter(Boolean) : [];
let privacyStatus = String(args.privacy || 'unlisted').toLowerCase();
if (!['public','unlisted','private'].includes(privacyStatus)) privacyStatus = 'unlisted';

if (!filePath || !fs.existsSync(filePath)) {
  console.error('Usage: node scripts/yt-upload.mjs <file.mp4> --title "..." --desc "..." [--privacy public|unlisted|private] [--tags a,b] [--file path]');
  console.error('Error: file not found:', filePath || '(missing)');
  process.exit(1);
}

const { YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN } = process.env;
if (!YT_CLIENT_ID || !YT_CLIENT_SECRET || !YT_REFRESH_TOKEN) {
  console.error('Missing YT OAuth envs', {
    YT_CLIENT_ID: YT_CLIENT_ID ? 'set' : '',
    YT_CLIENT_SECRET: YT_CLIENT_SECRET ? 'set' : 'missing',
    YT_REFRESH_TOKEN: YT_REFRESH_TOKEN ? 'set' : 'missing',
    ENV_FILE: process.env.ENV_FILE || '(not set)',
  });
  process.exit(1);
}

async function main() {
  const oauth2 = new google.auth.OAuth2(YT_CLIENT_ID, YT_CLIENT_SECRET);
  oauth2.setCredentials({ refresh_token: YT_REFRESH_TOKEN });

  // アクセストークンを先に取っておく（invalid_client 等の早期検知用）
  await oauth2.getAccessToken();

  const youtube = google.youtube({ version: 'v3', auth: oauth2 });

  const res = await youtube.videos.insert({
    part: ['snippet','status'],
    requestBody: {
      snippet: { title, description, tags },
      status: { privacyStatus },
    },
    media: { body: fs.createReadStream(filePath) },
  });

  const vid = res.data?.id;
  console.log('Upload OK', { id: vid, url: vid ? `https://youtu.be/${vid}` : '(unknown id)' });
}

main().catch(err => {
  // エラーの中身をそのまま見たいので標準化
  const msg = err?.errors?.[0]?.message || err?.message || String(err);
  console.error('Upload failed:', msg);
  if (err?.response?.data) console.error(JSON.stringify(err.response.data, null, 2));
  process.exit(1);
});
