import dotenv from 'dotenv';
import prompts from 'prompts';
import { google } from 'googleapis';

dotenv.config({ path: process.env.ENV_FILE || '.env.youtube' });

const cid = process.env.YT_CLIENT_ID || process.env.YOUTUBE_CLIENT_ID;
const sec = process.env.YT_CLIENT_SECRET || process.env.YOUTUBE_CLIENT_SECRET;

if (!cid || !sec) {
  console.error('Missing YT_CLIENT_ID / YT_CLIENT_SECRET in env (ENV_FILE=.env.youtube).');
  process.exit(1);
}

const oauth2 = new google.auth.OAuth2({
  clientId: cid,
  clientSecret: sec,
  redirectUri: 'http://localhost'  // デスクトップ型クライアントでOK
});

const authUrl = oauth2.generateAuthUrl({
  access_type: 'offline',              // refresh_token をもらう
  prompt: 'consent',                   // 既に同意済でも毎回 refresh_token を出す
  scope: ['https://www.googleapis.com/auth/youtube.upload']
});

console.log('\n=== STEP 1: 下のURLをブラウザで開いて同意してください ===\n');
console.log(authUrl + '\n');

const { pasted } = await prompts({
  type: 'text',
  name: 'pasted',
  message: '同意後に表示された (エラー400でもOK) ブラウザのURL全体を貼り付けて Enter:'
});

try {
  const u = new URL(pasted);
  const code = u.searchParams.get('code');
  if (!code) throw new Error('URLに code= が見つかりません。貼り付けた内容を確認してください。');

  const { tokens } = await oauth2.getToken(code);
  if (!tokens.refresh_token) {
    console.error('refresh_token が取得できませんでした。OAuthクライアント種別/同意画面/スコープを確認してください。');
    console.error(tokens);
    process.exit(1);
  }

  console.log('\n=== STEP 2: refresh_token を .env.youtube に追記します ===');
  console.log('(値の頭は 1// で始まります)');

  // 既存の YT_REFRESH_TOKEN 行を削除してから追記する場合は sed 等を使うのが安全
  console.log(`\n実行例:\n  sed -i '' '/^YT_REFRESH_TOKEN=/d' .env.youtube; \\\n  printf 'YT_REFRESH_TOKEN=%s\\n' '${tokens.refresh_token}' >> .env.youtube\n`);
  console.log('取得した refresh_token:');
  console.log(tokens.refresh_token);

} catch (e) {
  console.error('エラー:', e.message || e);
  process.exit(1);
}
