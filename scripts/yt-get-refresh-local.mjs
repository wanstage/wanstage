import http from 'http';
import open from 'open';
import {google} from 'googleapis';
import dotenv from 'dotenv';

dotenv.config({ path: process.env.ENV_FILE || '.env.youtube' });

const { YT_CLIENT_ID, YT_CLIENT_SECRET } = process.env;
if (!YT_CLIENT_ID || !YT_CLIENT_SECRET) {
  console.error('ENV error: YT_CLIENT_ID / YT_CLIENT_SECRET がありません');
  process.exit(1);
}

const host='127.0.0.1', port=53682, redirectUri=`http://${host}:${port}/callback`;
const oauth2=new google.auth.OAuth2({clientId:YT_CLIENT_ID, clientSecret:YT_CLIENT_SECRET, redirectUri});
const scope=['https://www.googleapis.com/auth/youtube.upload'];
const authUrl=oauth2.generateAuthUrl({ access_type:'offline', prompt:'consent', scope });

const server=http.createServer(async (req,res)=>{
  try{
    if(!req.url.startsWith('/callback')){res.writeHead(404);res.end('Not found');return;}
    const url=new URL(req.url,`http://${req.headers.host}`); const code=url.searchParams.get('code');
    if(!code){res.writeHead(400);res.end('Missing code');return;}
    const {tokens}=await oauth2.getToken(code);
    const refresh=tokens.refresh_token; const access=tokens.access_token;
    res.writeHead(200,{'Content-Type':'text/plain; charset=utf-8'}); res.end('OK! このタブは閉じて大丈夫です。');
    server.close();
    if(!refresh){ console.error('refresh_token なし。アカウントのサードパーティアクセスを一度取り消して再試行を。'); process.exit(2); }
    const fs=await import('fs'); let env=fs.readFileSync('.env.youtube','utf8');
    env=env.replace(/^YT_REFRESH_TOKEN=.*$/m,'').trim()+`\nYT_REFRESH_TOKEN=${refresh}\n`; fs.writeFileSync('.env.youtube',env);
    console.log('保存完了',{ access_token:access?access.slice(0,12)+'…':'(none)', refresh_token:refresh.slice(0,12)+'…' });
  }catch(e){ console.error('Callback error:', e?.response?.data || e); process.exit(1); }
});

server.listen(port,host,async()=>{
  console.log(`Listening on http://${host}:${port}/callback`);
  console.log('Opening browser for consent...');
  await open(authUrl);
});
