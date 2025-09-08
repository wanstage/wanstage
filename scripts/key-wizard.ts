import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { readFileSync, writeFileSync, existsSync, appendFileSync } from "node:fs";
import { EOL } from "node:os";

function setKV(lines: string[], key: string, val: string) {
  if (!val) return;
  const i = lines.findIndex(l => l.startsWith(key + "="));
  const line = `${key}=${val}`;
  if (i >= 0) lines[i] = line; else lines.push(line);
}

async function main() {
  const rl = createInterface({ input, output });
  console.log("=== WANSTAGE: Key Wizard ===");

  // Slack は既にOKなので省略可能

  const wantX = (await rl.question("X（Twitter）を設定しますか？ [y/N]: ")).trim().toLowerCase() === "y";
  let X_APP_KEY="", X_APP_SECRET="", X_ACCESS_TOKEN="", X_ACCESS_SECRET="";
  if (wantX) {
    X_APP_KEY      = (await rl.question("  X_APP_KEY: ")).trim();
    X_APP_SECRET   = (await rl.question("  X_APP_SECRET: ")).trim();
    X_ACCESS_TOKEN = (await rl.question("  X_ACCESS_TOKEN: ")).trim();
    X_ACCESS_SECRET= (await rl.question("  X_ACCESS_SECRET: ")).trim();
  }

  const wantIG = (await rl.question("Instagramを設定しますか？ [y/N]: ")).trim().toLowerCase() === "y";
  let IG_USER_ID="", IG_ACCESS_TOKEN="", IG_GRAPH_VERSION="v20.0";
  if (wantIG) {
    IG_USER_ID       = (await rl.question("  IG_USER_ID: ")).trim();
    IG_ACCESS_TOKEN  = (await rl.question("  IG_ACCESS_TOKEN（長期トークン）: ")).trim();
    const v = (await rl.question(`  IG_GRAPH_VERSION [${IG_GRAPH_VERSION}]: `)).trim();
    if (v) IG_GRAPH_VERSION = v;
  }

  const wantZap = (await rl.question("Zapier/Webhook を設定しますか？ [y/N]: ")).trim().toLowerCase() === "y";
  let ZAPIER_HOOK_URL="";
  if (wantZap) {
    ZAPIER_HOOK_URL = (await rl.question("  ZAPIER_HOOK_URL: ")).trim();
  }

  await rl.close();

  const envPath = ".env";
  const lines = existsSync(envPath)
    ? readFileSync(envPath, "utf8").split(/\r?\n/)
    : [];

  if (wantX) {
    setKV(lines, "X_APP_KEY", X_APP_KEY);
    setKV(lines, "X_APP_SECRET", X_APP_SECRET);
    setKV(lines, "X_ACCESS_TOKEN", X_ACCESS_TOKEN);
    setKV(lines, "X_ACCESS_SECRET", X_ACCESS_SECRET);
  }
  if (wantIG) {
    setKV(lines, "IG_USER_ID", IG_USER_ID);
    setKV(lines, "IG_ACCESS_TOKEN", IG_ACCESS_TOKEN);
    setKV(lines, "IG_GRAPH_VERSION", IG_GRAPH_VERSION);
  }
  if (wantZap) {
    setKV(lines, "ZAPIER_HOOK_URL", ZAPIER_HOOK_URL);
  }

  if (!lines.find(l => l.startsWith("TZ="))) lines.push("TZ=Asia/Tokyo");

  writeFileSync(envPath, lines.filter(Boolean).join(EOL) + EOL);
  try { appendFileSync(".gitignore", "\n.env\n", { flag: "a" }); } catch {}

  console.log("\n✔ .env を更新しました。必要ならもう一度実行して上書きできます。");
}
main().catch(e => { console.error(e); process.exit(1); });
