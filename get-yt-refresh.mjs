import http from 'node:http'
import {execSync} from 'node:child_process'
import crypto from 'node:crypto'
import fs from 'node:fs'
import dotenv from 'dotenv'

dotenv.config({ path: '.env.youtube' })
const CID = process.env.YT_CLIENT_ID
const SEC = process.env.YT_CLIENT_SECRET
if (!CID || !SEC) {
  console.error('❌ .env.youtube に YT_CLIENT_ID / YT_CLIENT_SECRET を入れてください')
  process.exit(1)
}

// 設定（デスクトップアプリ: ループバックURI）
const PORT = 53682
const REDIRECT = `http://127.0.0.1:${PORT}/callback`
const SCOPE = 'https://www.googleapis.com/auth/youtube.upload'

// PKCE（S256）
const code_verifier = crypto.randomBytes(64).toString('base64url')
const code_challenge = crypto
  .createHash('sha256')
  .update(code_verifier)
  .digest('base64')
  .replace(/\+/g,'-')
  .replace(/\//g,'_')
  .replace(/=+$/,'')

const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
authUrl.searchParams.set('client_id', CID)
authUrl.searchParams.set('redirect_uri', REDIRECT)
authUrl.searchParams.set('response_type', 'code')
authUrl.searchParams.set('scope', SCOPE)
authUrl.searchParams.set('access_type', 'offline')
authUrl.searchParams.set('prompt', 'consent')
authUrl.searchParams.set('code_challenge', code_challenge)
authUrl.searchParams.set('code_challenge_method', 'S256')

// 受け取り用HTTPサーバ
const server = http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url, `http://127.0.0.1:${PORT}`)
    if (u.pathname !== '/callback') {
      res.statusCode = 404; res.end('Not found'); return
    }
    const code = u.searchParams.get('code')
    const err = u.searchParams.get('error')
    if (err) {
      res.statusCode = 400
      res.end(`OAuth error: ${err}`)
      console.error('❌ OAuth error:', err)
      server.close()
      return
    }
    if (!code) {
      res.statusCode = 400
      res.end('Missing code')
      console.error('❌ code がありません')
      server.close()
      return
    }

    // その場でトークン交換
    const body = new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: REDIRECT,
      client_id: CID,
      client_secret: SEC,
      code_verifier
    })
    const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {'Content-Type':'application/x-www-form-urlencoded'},
      body
    })
    const tokenJson = await tokenRes.json()
    if (!tokenRes.ok) {
      console.error('❌ Token exchange failed:', tokenJson)
      res.statusCode = 500
      res.end('Token exchange failed. Check terminal.')
      server.close()
      return
    }

    const refresh = tokenJson.refresh_token
    const access = tokenJson.access_token
    console.log('✅ token:', { hasRefresh: !!refresh, access_len: access?.length || 0 })
    if (!refresh) {
      console.error('⚠️ refresh_token が返っていません（consent が足りない/同じ consent の再認可など）')
    }

    // .env.youtube に保存（既存行を削除して追記）
    try {
      const envPath = '.env.youtube'
      let env = ''
      try { env = fs.readFileSync(envPath,'utf8') } catch {}
      env = env.split('\n').filter(l => !l.startsWith('YT_REFRESH_TOKEN=')).join('\n')
      env = env.replace(/\n+$/,'') + '\n'
      if (refresh) env += `YT_REFRESH_TOKEN=${refresh}\n`
      fs.writeFileSync(envPath, env)
      console.log('💾 .env.youtube を更新しました（YT_REFRESH_TOKEN を保存）')
    } catch (e) {
      console.error('❌ .env.youtube 書き込みに失敗:', e)
    }

    res.end('You can close this tab. Token saved locally.')
    server.close()
  } catch (e) {
    console.error('❌ handler error:', e)
    res.statusCode = 500; res.end('Internal error'); server.close()
  }
})

server.listen(PORT, '127.0.0.1', () => {
  console.log(`▶︎ Listening on ${REDIRECT}`)
  try {
    // macOS: open でブラウザ起動
    execSync(`open '${authUrl.toString()}'`)
  } catch {
    console.log('Open this URL in your browser:\n', authUrl.toString())
  }
})
