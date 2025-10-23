import OpenAI from "openai";
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const res = await client.responses.create({ model: "gpt-4o-mini", input: "Say hello in 5 words" });
console.log(res.output_text ?? JSON.stringify(res, null, 2));
