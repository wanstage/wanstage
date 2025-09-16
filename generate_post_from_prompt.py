import json
import os
import random
import time
from datetime import datetime

from dotenv import load_dotenv

BASE = os.path.expanduser("~/WANSTAGE")
LOGS = os.path.join(BASE, "logs")
os.makedirs(LOGS, exist_ok=True)
load_dotenv(os.path.join(BASE, ".env"))

TOPICS = ["今日の学び", "小さな自動化テク", "作業効率アップ", "AIで時短", "開発ログ"]
HASHTAGS = ["#自動化", "#AI活用", "#生産性", "#学び", "#WANSTAGE"]


def fallback():
    t = random.choice(TOPICS)
    body = f"{t}: 1つだけでも行動してみよう。{datetime.now():%Y/%m/%d}"
    tags = " ".join(random.sample(HASHTAGS, 3))
    return {
        "text": f"{body}\n{tags}",
        "bullets": [],
        "hashtags": "",
        "meta": {"engine": "fallback", "ts": time.strftime("%F %T")},
    }


def force_json(s: str):
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        try:
            return json.loads(s)
        except:
            pass
    return {"text": s, "bullets": [], "hashtags": ""}


def main():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    topic = os.getenv("CONTENT_TOPIC", "日常の学びとショートTips")
    cta = os.getenv("CONTENT_CTA", "フォローして続きもチェック！")
    fixed_tags = os.getenv("DEFAULT_HASHTAGS", "#学び #ライフハック #今日の積み上げ")
    prompt = f"""あなたはSNSのプロ編集者です。80〜130文字の本文、20字以内の箇条書き2〜3個、CTAとハッシュタグを作ってください。
JSONで出力: {{"text":"...", "bullets":["...","..."], "hashtags":"..."}}
テーマ: {topic}
CTA: {cta}
固定タグ: {fixed_tags}
"""
    out_json = None
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400,
            )
            content = resp.choices[0].message.content
            obj = force_json(content)
            text = (
                obj.get("text", "").strip()
                + "\n"
                + "\n".join([f"・{b}" for b in obj.get("bullets", []) if b])
                + "\n"
                + (obj.get("hashtags", "").strip() or fixed_tags)
            )
            out_json = {
                "text": text.strip(),
                "meta": {"engine": "openai", "model": model, "ts": time.strftime("%F %T")},
            }
        except Exception as e:
            fb = fallback()
            fb["meta"]["error"] = str(e)
            out_json = fb
    else:
        out_json = fallback()

    # ファイル出力
    with open(os.path.join(LOGS, "generated.json"), "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False)
    with open(os.path.join(LOGS, "post_text.txt"), "w", encoding="utf-8") as f:
        f.write(out_json["text"])
    # 標準出力にもJSON（ログから見たい場合）
    print(json.dumps(out_json, ensure_ascii=False))


if __name__ == "__main__":
    main()
