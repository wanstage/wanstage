import 'dotenv/config';
import OpenAI from 'openai';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  organization: process.env.OPENAI_ORG_ID,   // 無ければ未設定でOK
  project: process.env.OPENAI_PROJECT_ID     // 無ければ未設定でOK
});

async function safeCall(promise, onFail) {
  try { return await promise; }
  catch (e) {
    const code = e?.code || e?.error?.code || '';
    if (code === 'billing_hard_limit_reached') {
      console.warn('[WARN] Billing limit reached. Skipping image step.');
      return typeof onFail === 'function' ? onFail(e) : null;
    }
    throw e;
  }
}

async function pingText() {
  const res = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Say "WANSTAGE OK" only.' }]
  });
  console.log('CHAT_OK:', res.choices[0]?.message?.content);
}

async function generateImage() {
  if (process.env.WANSTAGE_ENABLE_IMAGE === "0") { console.log("IMG_SKIP by flag"); return; }
  const r = await safeCall(
    client.images.generate({
      model: 'gpt-image-1',
      prompt: 'A photorealistic image of Mount Fuji during sunrise',
      size: '1024x1024' // 有効サイズのみ
    }),
    () => null
  );
  if (!r) return; // スキップ（課金上限ヒット時）
  const b64 = r.data[0].b64_json;
  fs.writeFileSync(path.join(__dirname, 'fuji.png'), Buffer.from(b64, 'base64'));
  console.log('IMG_OK fuji.png');
}

(async () => {
  const keyLen = (process.env.OPENAI_API_KEY || '').length;
  if (!keyLen) {
    console.error('ERROR: OPENAI_API_KEY が読み込めていません (.env を確認)');
    process.exit(2);
  }
  console.log('KEY_LEN=', keyLen);
  await pingText();
  await generateImage();
  console.log('DONE');
})().catch(e => {
  console.error('FATAL', e.status || '', e.code || '', e.message);
  process.exit(1);
});
