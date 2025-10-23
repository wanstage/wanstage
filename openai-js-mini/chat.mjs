import OpenAI from "openai";
import readline from "readline";

const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  console.error("❌ OPENAI_API_KEY が設定されていません。`export OPENAI_API_KEY=...` で設定してください。");
  process.exit(1);
}
const client = new OpenAI({ apiKey });

const MODEL = process.env.OPENAI_MODEL || "gpt-4o-mini";

async function oneShot(prompt) {
  const res = await client.chat.completions.create({
    model: MODEL,
    messages: [{ role: "user", content: prompt }],
  });
  console.log(res.choices?.[0]?.message?.content?.trim() || "");
}

async function interactive() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const history = [];
  async function ask() {
    await new Promise(resolve => rl.question("You> ", async (q) => {
      if (!q || q.trim().toLowerCase() === "exit") { rl.close(); return resolve(); }
      history.push({ role: "user", content: q });
      const res = await client.chat.completions.create({
        model: MODEL,
        messages: history
      });
      const answer = res.choices?.[0]?.message?.content?.trim() || "";
      console.log(`GPT> ${answer}\n`);
      history.push({ role: "assistant", content: answer });
      resolve(ask());
    }));
  }
  await ask();
}

const arg = process.argv.slice(2).join(" ").trim();
if (arg) {
  oneShot(arg).catch(e => (console.error(e), process.exit(1)));
} else {
  console.log(`💬 ChatGPT CLI (${MODEL}) / 対話モード開始。終了は 'exit'`);
  interactive().catch(e => (console.error(e), process.exit(1)));
}
