import 'dotenv/config';
import fs from 'fs';

const { YT_REFRESH_TOKEN } = process.env;

if (!YT_REFRESH_TOKEN) {
  console.error('No refresh token found in .env.youtube');
  process.exit(1);
}

(async () => {
  try {
    const res = await fetch('https://oauth2.googleapis.com/revoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ token: YT_REFRESH_TOKEN }),
    });

    if (res.ok) {
      console.log('✅ Token revoked successfully.');
    } else {
      console.error('❌ Revoke failed:', await res.text());
    }

    // .env.youtube から YT_REFRESH_TOKEN 行を削除
    let env = fs.readFileSync('.env.youtube', 'utf8')
      .split('\n')
      .filter(line => !line.startsWith('YT_REFRESH_TOKEN='))
      .join('\n');
    fs.writeFileSync('.env.youtube', env.trimEnd() + '\n');
    console.log('🗑️  Local YT_REFRESH_TOKEN entry removed from .env.youtube');
  } catch (err) {
    console.error('Error:', err);
  }
})();
