export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }

    // LINE Notify へのパススルー（必要な人だけ使う）
    const LINE_URL = "https://notify-api.line.me/api/notify";

    // 元リクエストのヘッダをコピー（不要ヘッダ除去）
    const fwd = new Headers(request.headers);
    for (const h of [
      "host","content-length","connection","keep-alive","transfer-encoding",
      "proxy-authorization","proxy-connection","cf-connecting-ip","cf-ew-via",
      "cf-ipcountry","cf-ray","cf-visitor","x-forwarded-proto","x-forwarded-for",
      "x-real-ip","via"
    ]) fwd.delete(h);

    // env.LINE_NOTIFY_TOKEN を使う（GitHub Actions で secret を wrangler に渡す前提）
    fwd.set("authorization", `Bearer ${env.LINE_NOTIFY_TOKEN}`);

    const init = { method: request.method, headers: fwd, body: request.body, redirect: "manual" };

    // 5xxのみリトライ
    async function withRetry(n=3) {
      let lastErr;
      for (let i=0;i<n;i++) {
        try {
          const res = await fetch(LINE_URL, init);
          if (res.status >= 500) { lastErr = new Error(`LINE ${res.status}`); }
          else return res;
        } catch (e) { lastErr = e; }
        await new Promise(r => setTimeout(r, 500*(i+1)));
      }
      throw lastErr ?? new Error("fetch failed");
    }

    try {
      const res = await withRetry();
      return new Response(res.body, { status: res.status, headers: res.headers });
    } catch (e) {
      return new Response(JSON.stringify({ error: String(e) }), {
        status: 502,
        headers: { "content-type": "application/json" }
      });
    }
  }
}
