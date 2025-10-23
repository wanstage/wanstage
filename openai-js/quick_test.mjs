import OpenAI from "openai";
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const res = await client.responses.create({
  model: "gpt-5",               // 権限モデルでOK
  input: "Say hello in 5 words"
});
console.log(res.output_text ?? JSON.stringify(res, null, 2));
