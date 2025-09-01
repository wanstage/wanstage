import ngrok from '@ngrok/ngrok';
const PORT = process.env.PORT || 8080;
const listener = await ngrok.connect({
  addr: PORT,
  authtoken_from_env: true
});
console.log(`Ingress established at: ${listener.url()}`);
