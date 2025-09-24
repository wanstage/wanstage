import { chromium } from 'playwright';
import fs from 'fs';

const userDataDir = process.env.PW_USER_DATA || `${process.env.HOME}/WANSTAGE/.pw`;
const context = await chromium.launchPersistentContext(userDataDir, { headless: true });
const page = await context.newPage();
const url = process.env.TARGET_URL || 'https://example.com/report';

await page.goto(url, { waitUntil: 'networkidle' });
// 初回は PWDEBUG=1 で手動ログインしてCookie保存
// 例: PWDEBUG=1 node download_csv.mjs

const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.click(process.env.CSV_BUTTON_SELECTOR || 'text=Export CSV'),
]);

const out = `${process.env.HOME}/WANSTAGE/logs/report-${Date.now()}.csv`;
await download.saveAs(out);
console.log('saved:', out);

await context.close();
