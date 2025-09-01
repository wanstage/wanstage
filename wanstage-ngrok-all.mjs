import 'dotenv/config';
import ngrok from 'ngrok';

const authtoken = process.env.NGROK_AUTHTOKEN;
if (!authtoken) {
  console.error('NGROK_AUTHTOKEN is missing. Set it in ~/.zshrc or .env');
  process.exit(1);
}

const port = 8090;
const region = process.env.NGROK_REGION || 'jp';

console.log(`HTTP listening on http://localhost:${port}`);
try {
  const url = await ngrok.connect({
    addr: port,
    authtoken,
    region,
    proto: 'http'
  });
  console.log('✅ ngrok tunnel:', url);
} catch (e) {
  console.error('❌ ngrok failed:', e?.message || e);
  process.exit(1);
}
