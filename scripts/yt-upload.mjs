import dotenv from 'dotenv';
import fs from 'fs';
import { google } from 'googleapis';
import minimist from 'minimist'
dotenv.config({ path: process.env.ENV_FILE || '.env', override: false });
dotenv.config({ path: process.env.ENV_FILE || '.env', override: false });

const args = minimist(process.argv.slice(2), {
  string: ['title', 'desc', 'privacy', 'tags', 'file'],
  alias: { t: 'title', d: 'desc', p: 'privacy' },
const filePath = args.file || args._[0];
const title = args.title || 'WANSTAGE Auto Upload';
const description = args.desc || 'Uploaded via WANSTAGE automation';
const tags = args.tags ? String(args.tags).split(',').map(s => s.trim()).filter(Boolean) : [];
let privacyStatus = (args.privacy || 'unlisted').toLowerCase();
if (!['public', 'unlisted', 'private'].includes(privacyStatus)) privacyStatus = 'unlisted';
if (!filePath || !fs.existsSync(filePath)) {
  console.error(
    'Usage: node scripts/yt-upload.mjs <file.mp4> --title "..." --desc "..." [--privacy public|unlisted|private] [--tags a,b]'
  );
  console.error('Error: file not found:', filePath || '(missing)');
  process.exit(1);
}
const { YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN } = process.env;
const mask = (s) => (s ? s.slice(0, 12) + '…' : '(none)');

if (!YT_CLIENT_ID || !YT_CLIENT_SECRET || !YT_REFRESH_TOKEN) {
  console.error('Missing YT OAuth envs {');
  console.error(`  YT_CLIENT_ID: '${YT_CLIENT_ID ? mask(YT_CLIENT_ID) : ''}'`);
  console.error(`  YT_CLIENT_SECRET: ${YT_CLIENT_SECRET ? 'set' : 'missing'}`);
  console.error(`  YT_REFRESH_TOKEN: ${YT_REFRESH_TOKEN ? 'set' : 'missing'}`);
  console.error('}');
  console.error('Hint: ENV_FILE=.env.youtube node scripts/yt-upload.mjs ... で .env.youtube を確実に読めます。');
  process.exit(1);
}
const oauth2 = new google.auth.OAuth2(YT_CLIENT_ID, YT_CLIENT_SECRET);
oauth2.setCredentials({ refresh_token: YT_REFRESH_TOKEN });

const youtube = google.youtube({ version: 'v3', auth: oauth2 });
try {
  const res = await youtube.videos.insert({
    part: ['snippet', 'status'],
    notifySubscribers: false,
    requestBody: {
      snippet: { title, description, tags },
      status: { privacyStatus },
    },
    media: { body: fs.createReadStream(filePath) },
  });

  const id = res.data.id;
  console.log('✅ Upload success');
  console.log('  id   :', id);
  console.log('  title:', res.data.snippet?.title);
  console.log('  url  :', id ? `https://youtu.be/${id}` : '(unknown)');
} catch (e) {
  // エラー詳細を出力
  const data = e?.response?.data;
  if (data) {
    console.error('Upload failed:', JSON.stringify(data, null, 2));
  } else {
    console.error(e);
  }
  process.exit(2);
}
