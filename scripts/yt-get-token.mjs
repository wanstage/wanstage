import 'dotenv/config';
import http from 'http';
import { spawn } from 'child_process';
import { google } from 'googleapis';

const { YT_CLIENT_ID, YT_CLIENT_SECRET } = process.env;
if (!YT_CLIENT_ID || !YT_CLIENT_SECRET) {
  throw new Error('Set YT_CLIENT_ID / YT_CLIENT_SECRET in .env');
}

const REDIRECT_URI = 'http://127.0.0.1:53682/callback';
const oauth2Client = new google.auth.OAuth2(YT_CLIENT_ID, YT_CLIENT_SECRET, REDIRECT_URI);
const AUTH_URL = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  prompt: 'consent',
  scope: ['https://www.googleapis.com/auth/youtube.upload'],
});

const server = http.createServer(async (req, res) => {
  try {
    if (!req.url?.startsWith('/callback')) {
      res.writeHead(404); res.end('Not Found'); return;
    }
    const urlObj = new URL(req.url, REDIRECT_URI);
    const code = urlObj.searchParams.get('code');

    if (!code) {
      res.writeHead(400); res.end('Missing code'); return;
    }

    res.writeHead(200, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('OK! You can close this tab and return to terminal.');

    const { tokens } = await oauth2Client.getToken(code);
    server.close();

    if (!tokens.refresh_token) {
      console.log('No refresh_token returned. Re-run with prompt=consent, or revoke previous grant in Google Account.');
    } else {
      console.log(`\nYT_REFRESH_TOKEN=${tokens.refresh_token}\n`);
      console.log('↑ この1行を .env にそのまま追記してください。');
    }
    process.exit(0);
  } catch (e) {
    console.error(e);
    try { res.writeHead(500); res.end('Error'); } catch {}
    process.exit(1);
  }
});

server.listen(53682, '127.0.0.1', () => {
  console.log('Listening on http://127.0.0.1:53682/callback');
  console.log('\nOpening browser for consent...\n');
  spawn('open', [AUTH_URL], { stdio: 'ignore', detached: true });
});
