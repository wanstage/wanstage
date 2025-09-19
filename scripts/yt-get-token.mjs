import http from 'http';
import { exec } from 'child_process';
import dotenv from 'dotenv';
import { google } from 'googleapis';

// .env 読み込み（.env.youtube を優先）
if (process.env.ENV_FILE) {
  dotenv.config({ path: process.env.ENV_FILE, override: true });
} else {
  dotenv.config({ path: '.env.youtube', override: false });
  dotenv.config({ path: '.env',         override: false });
}

const { YT_CLIENT_ID, YT_CLIENT_SECRET } = process.env;
const REDIRECT_URI = 'http://127.0.0.1:53682/callback';
const SCOPES = ['https://www.googleapis.com/auth/youtube.upload'];

if (!YT_CLIENT_ID || !YT_CLIENT_SECRET) {
  console.error('Missing YT_CLIENT_ID or YT_CLIENT_SECRET. Check your .env.youtube');
  process.exit(1);
}

const oauth2 = new google.auth.OAuth2(YT_CLIENT_ID, YT_CLIENT_SECRET, REDIRECT_URI);
const url = oauth2.generateAuthUrl({ access_type: 'offline', scope: SCOPES, prompt: 'consent' });

const server = http.createServer(async (req, res) => {
  if (!req.url.startsWith('/callback')) {
    res.writeHead(404); res.end('Not Found'); return;
  }
  const u = new URL(req.url, REDIRECT_URI);
  const code = u.searchParams.get('code');
  if (!code) {
    res.writeHead(400); res.end('Missing code'); return;
  }
  try {
    const { tokens } = await oauth2.getToken(code);
    res.writeHead(200, {'Content-Type':'text/plain; charset=utf-8'});
    res.end(`OK!\n\nrefresh_token:\n${tokens.refresh_token || '(none)'}\n\naccess_token:\n${tokens.access_token || '(none)'}\n`);
    console.log('\n=== TOKENS ===');
    console.log({ refresh_token: tokens.refresh_token, access_token: tokens.access_token, expiry_date: tokens.expiry_date });
    console.log('\nCopy the refresh_token and put it into .env.youtube as:\n  YT_REFRESH_TOKEN=1//....\n');
  } catch (e) {
    res.writeHead(500); res.end('Error exchanging code. Check terminal.');
    console.error(e);
  } finally {
    server.close();
  }
});

server.listen(53682, '127.0.0.1', () => {
  console.log('Listening on http://127.0.0.1:53682/callback');
  console.log('Opening browser for consent...');
  const opener = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'start ""' : 'xdg-open';
  exec(`${opener} "${url}"`);
});
