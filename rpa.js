import { chromium } from 'playwright';
const url = process.env.TARGET_URL || 'https://example.com';
const text = process.env.MESSAGE || 'WANSTAGE RPA OK';

const run = async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto(url);
  // 必要なDOM操作をここに（クリック/入力など）
  console.log(text);
  await b.close();
};
run();
