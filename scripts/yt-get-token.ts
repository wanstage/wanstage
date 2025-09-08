import { google } from 'googleapis';
import readline from 'node:readline/promises';

const CLIENT_ID = process.env.YT_CLIENT_ID!;
const CLIENT_SECRET = process.env.YT_CLIENT_SECRET!;
const REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob';

async function main(){
  if(!CLIENT_ID || !CLIENT_SECRET) throw new Error('Set YT_CLIENT_ID / YT_CLIENT_SECRET');
  const oAuth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);
  const scopes = ['https://www.googleapis.com/auth/youtube.upload'];
  const authUrl = oAuth2Client.generateAuthUrl({ access_type:'offline', scope:scopes, prompt:'consent' });
  console.log('Open this URL and authorize:\n', authUrl);

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const code = await rl.question('Paste the code here: ');
  rl.close();

  const { tokens } = await oAuth2Client.getToken(code.trim());
  console.log('\n=== SAVE THESE ===');
  console.log('YT_REFRESH_TOKEN=', tokens.refresh_token);
}
main().catch(e=>{ console.error(e); process.exit(1); });
