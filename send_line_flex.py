#!/usr/bin/env python3
import os, sys, json, argparse, pathlib, datetime, requests

ROOT = pathlib.Path(__file__).resolve().parent
ENVFILE = ROOT / ".env"

def load_env_ascii(path: pathlib.Path):
    """ASCII だけの .env を読み込む（KEY=VALUE 形式）"""
    if not path.exists():
        return
    raw = path.read_text(errors="strict")
    # 非ASCII混入チェック
    bad = [(i,c) for i,c in enumerate(raw) if (ord(c)>127 and c!='\n')]
    if bad:
        sys.exit(f".env に非ASCIIが含まれます（例 {repr(bad[:5])}）")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k and (k not in os.environ):
            os.environ[k] = v

def as_date(s: str|None) -> str:
    if not s:
        return datetime.date.today().isoformat()
    return s

def build_flex(title: str, body: str, url: str, image: str) -> dict:
    """
    LINE Flex（最小・安全なBubble）
    - 公式仕様に合う基本プロパティのみ使用
    """
    return {
      "type": "flex",
      "altText": "WANSTAGE",
      "contents": {
        "type": "bubble",
        "hero": {
          "type": "image",
          "url": image,
          "size": "full",
          "aspectRatio": "16:9",
          "aspectMode": "cover"
        },
        "body": {
          "type": "box",
          "layout": "vertical",
          "contents": [
            { "type": "text", "text": title, "wrap": True, "weight": "bold", "size": "lg" },
            { "type": "text", "text": body,  "wrap": True, "size": "sm" }
          ]
        },
        "footer": {
          "type": "box",
          "layout": "horizontal",
          "contents": [
            { "type": "button", "style": "primary",
              "action": { "type": "uri", "label": "Open", "uri": url } }
          ]
        }
      }
    }

def main():
    load_env_ascii(ENVFILE)

    TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    TO    = os.environ.get("LINE_USER_ID")
    if not TOKEN or not TO:
        sys.exit("ENV: LINE_CHANNEL_ACCESS_TOKEN / LINE_USER_ID を設定してください (.env でも可)")

    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD。未指定は今日")
    ap.add_argument("--slot", type=int, default=1)
    args = ap.parse_args()
    date_str = as_date(args.date)

    # フェーズ①は固定文面でOK（Flexが仕様通りか検証用）
    title = f"WANSTAGE {date_str} SLOT#{args.slot}"
    body  = f"{date_str} のテスト配信（フェーズ①検証）。"
    url   = "https://example.com/"
    image = "https://picsum.photos/seed/wanstage/1024/576"

    message = build_flex(title, body, url, image)

    payload = { "to": TO, "messages": [ message ] }

    # --- requests: 環境プロキシ無効 & ヘッダは ASCII のみ ---
    s = requests.Session()
    s.trust_env = False
    headers = { "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json" }

    # 送信（本文は UTF-8 バイトにして渡す）
    r = s.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=15,
    )

    # ログ（返却JSONは一部だけ）
    body_preview = (r.text or "")[:200]
    print("STATUS", r.status_code, body_preview)
    if r.status_code != 200:
        # 具体的な失敗理由を出し、次のアクションを示す
        print("\n[NG] 失敗しました。チェック項目:")
        print("  1) アクセストークンが長期(チャネルアクセストークン)で正しいか")
        print("  2) ユーザーIDが正しいか（Botを友だち追加済みか）")
        print("  3) .env に全角/改行が混入していないか（ASCIIのみか）")
        print("  4) 会社内プロキシ等 → trust_env=False で無効化済み")
        sys.exit(1)

if __name__ == "__main__":
    main()
