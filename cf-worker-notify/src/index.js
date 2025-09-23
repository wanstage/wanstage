export default {
  async fetch(request, env, ctx) {
    const { pathname } = new URL(request.url);

    // 1) ヘルスチェック
    if (pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "content-type": "application/json" },
      });
    }

    // 2) LINE Notify へのパススルー（任意）
    //    GitHub Secrets に LINE_NOTIFY_TOKEN を入れた場合だけ動作
    if (pathname === "/line" && request.method === "POST") {
      if (!env.LINE_NOTIFY_TOKEN) {
        return new Response(JSON.stringify({ error: "LINE token not set" }), {
          status: 400,
          headers: { "content-type": "application/json" },
        });
      }
      const form = await request.formData().catch(() => null);
      const message = form?.get("message") || (await request.text());
      const body = new URLSearchParams({ message: message || "(no message)" });

      const r = await fetch("https://notify-api.line.me/api/notify", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.LINE_NOTIFY_TOKEN}`,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
      });
      const text = await r.text();
      return new Response(text, { status: r.status });
    }

    // 3) デフォルト応答
    return new Response("WANSTAGE Worker up");
  },
};
