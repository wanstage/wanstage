import 'dotenv/config';
import fs from 'fs';
import { google } from 'googleapis';
import minimist from 'minimist';

const args = minimist(process.argv.slice(2), {
  string: ['title','desc','privacy','tags'],
  alias: { t:'title', d:'desc', p:'privacy' }
});

const filePath = args._[0];
const title = args.title || 'WANSTAGE Auto Upload';
const description = args.desc || 'Uploaded via WANSTAGE automation';
const tags = args.tags ? args.tags.split(',') : [];
let privacyStatus = (args.privacy || 'unlisted').toLowerCase();
if (!['public','unlisted','private'].includes(privacyStatus)) privacyStatus = 'unlisted';

if (!filePath || !fs.existsSync(filePath)) {
  console.error('Usage: node scripts/yt-upload.mjs <file.mp4> --title "..." --desc "..." [--privacy public|unlisted|private] [--tags a,b]');
  process.exit(1);
}

const { YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN } = process.env;
const mask = s => s ? String(s).slice(0,6)+'…' : s;
if (!YT_CLIENT_ID || !YT_CLIENT_SECRET || !YT_REFRESH_TOKEN) {
  console.error('Missing YT OAuth envs', {
    YT_CLIENT_ID: mask(YT_CLIENT_ID),
    YT_CLIENT_SECRET: YT_CLIENT_SECRET ? 'set' : 'missing',
    YT_REFRESH_TOKEN: YT_REFRESH_TOKEN ? 'set' : 'missing',
  });
  process.exit(1);
}

const oauth2 = new google.auth.OAuth2(YT_CLIENT_ID, YT_CLIENT_SECRET);
oauth2.setCredentials({ refresh_token: YT_REFRESH_TOKEN });
const youtube = google.youtube({ version: 'v3', auth: oauth2 });

(async () => {
  try {
    const res = await youtube.videos.insert({
      part: ['snippet','status'],
      requestBody: { snippet: { title, description, tags }, status: { privacyStatus } },
      media: { body: fs.createReadStream(filePath) }
    });
    const vid = res.data?.id;
    if (vid) {
      console.log(`Video ID: ${vid}`);
      console.log(`Watch: https://youtu.be/${vid}`);
    } else {
      console.log('No video id:', res.data);
    }
  } catch (e) {
    console.error('Upload failed:', e?.errors || e?.response?.data || e);
    process.exit(1);
  }
})();
