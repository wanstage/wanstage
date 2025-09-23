const { WebClient } = require("@slack/web-api");

(async () => {
  const slack = new WebClient(process.env.SLACK_BOT_TOKEN);
  const auth = await slack.auth.test();
  console.log("Slack OK:", auth.user);
})();
