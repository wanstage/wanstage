#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
photo_poem_generate.py - 感情共感＋写真ポエム自動生成
WANSTAGE photo poem mode
"""

import json
import os
import sys
from pathlib import Path

from openai import OpenAI

# --- 初期設定 ---
BASE = Path.home() / "WANSTAGE"
OUT_DIR = BASE / "out" / "insta"
OUT_DIR.mkdir(parents=True, exist_ok=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_photo_poem(image_path: str):
    """
    画像を解析し、感情共感ポエムを自動生成する
    """
    # 1️⃣ 画像特徴（簡易的にファイル名から推定）
    filename = Path(image_path).stem
    prompt_context = f"この写真の情景は「{filename}」です。"

    # 2️⃣ GPTプロンプト
    prompt = f"""
{prompt_context}
写真から感じる情景をもとに、短い日本語の詩（ポエム）を作成してください。
- 最大3行
- 感情表現を含める
- トーンは「やさしく・余白のある」
- 絵文字は使わない
出力はJSONで返してください:
{{
  "caption": "詩の本文",
  "hashtags": ["#ポエム", "#情景", "#感情共感"]
}}
    """

    # 3️⃣ GPT生成
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    text = resp.choices[0].message.content.strip()

    # 4️⃣ JSON整形
    try:
        data = json.loads(text)
    except Exception:
        data = {"caption": text, "hashtags": ["#photo_poem", "#WANSTAGE"]}

    # 5️⃣ 保存
    out_path = OUT_DIR / f"auto_poem_{Path(image_path).stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "caption": data["caption"],
                "hashtags": data["hashtags"],
                "image": image_path,
                "category": "empathy_poem",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"✅ photo poem 生成完了: {out_path}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ 使用方法: python3 core/photo_poem_generate.py <画像パス>")
        sys.exit(1)
    generate_photo_poem(sys.argv[1])
