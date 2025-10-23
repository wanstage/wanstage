import OpenAI from "openai";

const MODEL_PRIMARY   = process.env.OPENAI_MODEL || "gpt-4o-mini";   // 低コスト
const MODEL_FALLBACK1 = "gpt-4o-mini-translate";                      // 代替
const MODELS = [MODEL_PRIMARY, MODEL_FALLBACK1];

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async function callOnce(model, input) {
  return client.responses.create({ model, input });
}

// 429 を自動リトライ（指数バックオフ）、モデルも順次フォールバック
async function safeCall(input) {
  const maxAttempts = 4;           // 例：最大4回
  const baseDelayMs = 800;         // 初期待機
  for (const model of MODELS) {
    let attempt = 0;
    while (attempt < maxAttempts) {
      try {
        const res = await callOnce(model, input);
        return { model, res };
      } catch (e) {
        const status = e?.status || e?.code;
        if (status === 429) {
          const wait = Math.round(baseDelayMs * Math.pow(2, attempt));
          await new Promise(r => setTimeout(r, wait));
          attempt++;
          continue;
        }
        // 認可/鍵エラーなどは即時終了
        throw e;
      }
    }
    // このモデルは諦め、次のモデルへ
  }
  throw new Error("All models failed with rate/quota limits.");
}

(async () => {
  const input = "Say hello in 5 words";
  try {
    const { model, res } = await safeCall(input);
    console.log(`[OK] model=${model}`);
    console.log(res.output_text ?? JSON.stringify(res, null, 2));
  } catch (err) {
    console.error("❌ final error:", err?.message || err);
    process.exitCode = 1;
  }
})();
