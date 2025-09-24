const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const userDataDir = process.env.PW_USER_DATA || process.env.HOME + '/WANSTAGE/.pw';
  const context = await chromium.launchPersistentContext(userDataDir, { headless: true });
  const page = await context.newPage();
  const url = process.env.TARGET_URL || 'https://example.com/report';

  await page.goto(url, { waitUntil: 'networkidle' });
  // ログインが必要なサイトは、一度 headful で userDataDir にログイン状態を保存しておく
  // 例: PWDEBUG=1 node download_csv.js で手動ログイン → 次回から自動

  const [ download ] = await Promise.all([
    page.waitForEvent('download'),
    page.click(process.env.CSV_BUTTON_SELECTOR || 'text=Export CSV')
  ]);
  const out = `${process.env.HOME}/WANSTAGE/logs/report-${Date.now()}.csv`;
  await download.saveAs(out);
  console.log('saved:', out);

  await context.close();
})();
