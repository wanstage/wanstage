// scripts/yt-get-token.js
require('dotenv').config();
const readline = require('readline');
const { google } = require('googleapis');

async function main() {
  const clientId = process.env.YT_CLIENT_ID;
  const clientSecret = process.env.YT_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    throw new Error('Set YT_CLIENT_ID / YT_CLIENT_SECRET in .env');
  }

  const redirectUri = 'urn:ietf:wg:oauth:2.0:oob'; // OOBフロー
  const oauth2Client = new google.auth.OAuth2(clientId, clientSecret, redirectUri);

  const scopes = ['https://www.googleapis.com/auth/youtube.upload'];
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: scopes,
  });

  console.log('\n==== YouTube OAuth 認可フロー ====');
  console.log('1) 下のURLをブラウザで開いて認可してください:');
  console.log(authUrl);
  console.log('\n2) 表示された「認可コード」をここに貼り付けて Enter を押してください。\n');

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  rl.question('Code: ', async (code) => {
    rl.close();
    try {
      const { tokens } = await oauth2Client.getToken(code.trim());
      console.log('\n=== 取得成功 ===');
      console.log('YT_REFRESH_TOKEN=' + tokens.refresh_token);
      console.log('\nこの値を .env に追記してください。');
    } catch (err) {
      console.error('Error retrieving access token', err);
    }
  });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
