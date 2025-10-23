from openai import OpenAI

client = OpenAI()

theme = "SNS収益化"
target = "副業に関心がある20代〜30代"
link = "https://note.com/wanstage_lab"

prompt = f"""
あなたはSNSマーケターです。
以下の情報を基に、noteへの自然な誘導文を作成してください。

テーマ: {theme}
ターゲット層: {target}
noteリンク: {link}

条件:
- 日本語
- 40〜100文字
- 不自然な宣伝口調は禁止
- 「→」「👉」「🔗」など視覚的マーカーを1個だけ使用
- フレーズ例: 続きはnoteで解説／詳細はこちら／note記事で公開中
"""

try:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )
    print("🧠 自動生成CTA：", resp.choices[0].message.content.strip())
except Exception as e:
    print(f"⚠️ CTA生成失敗: {e}")
