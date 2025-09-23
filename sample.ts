import { WebClient } from "@slack/web-api";

async function main() {
  const slack = new WebClient(process.env.SLACK_BOT_TOKEN);
  const auth = await slack.auth.test();
  console.log("Slack OK:", auth.user);
}

main().catch(console.error);
