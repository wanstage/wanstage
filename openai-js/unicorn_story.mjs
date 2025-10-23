import OpenAI from "openai";
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

(async () => {
  try {
    const res = await client.responses.create({
      model: "gpt-5",
      input: "Write a short bedtime story about a unicorn."
    });
    // SDKのバージョン差分に強い出力処理
    console.log(res.output_text ?? JSON.stringify(res, null, 2));
  } catch (err) {
    console.error("❌ OpenAI API error:", err?.message || err);
    process.exitCode = 1;
  }
})();
