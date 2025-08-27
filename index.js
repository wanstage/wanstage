import ngrok from "@ngrok/ngrok";

(async function() {
  const listener = await ngrok.connect({ addr: 8000, authtoken_from_env: true });
  console.log(`Ingress established at: ${listener.url()}`);
})();
