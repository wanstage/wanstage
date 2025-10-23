import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function withBackoff(fn, { retries = 5, baseMs = 800 } = {}) {
  let lastErr;
  for (let i = 0; i < retries; i++) {
    try { return await fn(); } catch (e) {
      lastErr = e;
      const code = e?.code || e?.error?.code;
      const status = e?.status;
      // 429/503/5xx はリトライ、それ以外は即エラー
      const retryable = status === 429 || status === 503 || (status >= 500 && status < 600);
      if (!retryable) break;
      const jitter = Math.random() * 200;
      const wait = Math.min(15000, baseMs * 2 ** i) + jitter;
      console.warn(`⏳ Retrying in ${Math.round(wait)}ms (attempt ${i + 1}/${retries})…`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw lastErr;
}

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    console.error("❌ OPENAI_API_KEY が未設定です。`.env` または環境変数を設定してください。");
    process.exit(1);
  }

  try {
    const resp = await withBackoff(() =>
      client.chat.completions.create({
        model: "gpt-4o",
        messages: [
          { role: "system", content: "You are a helpful assistant." },
          { role: "user", content: "Write a one-sentence bedtime story about a unicorn." },
        ],
        max_tokens: 50,
        temperature: 0.7,
      })
    );

    console.log("\n🦄 生成結果:");
    console.log(resp.choices[0]?.message?.content?.trim() || "(no content)");
    console.log("\n✅ 完了しました。");
  } catch (e) {
    const code = e?.code || e?.error?.code;
    const status = e?.status;

    if (code === "insufficient_quota" || status === 429) {
      // フォールバック：ダミー出力（レート制限・無料枠超過時に運用を止めない）
      console.warn("⚠️ OpenAIのクォータ/レート制限に達しました。フォールバック文を出力します。");
      console.log("\n🦄 生成結果(フォールバック):");
      console.log("A sleepy unicorn curled beneath moonlight and dreamed of sugar clouds.");
      process.exit(0);
    }

    console.error("❌ OpenAI呼び出しでエラー:", e);
    process.exit(2);
  }
}

main();
