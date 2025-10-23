#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WANSTAGE GPT Refiner
高反応投稿を再分析し、改良済みの再投稿データを自動生成
"""

import csv
import json
import os
from datetime import datetime

import openai

BASE = os.path.expanduser("~/WANSTAGE")
LOG_FILE = os.path.join(BASE, "logs", "reaction_log.csv")
OUT_FILE = os.path.join(BASE, "logs", f"autogen_repost_{datetime.now():%Y%m%d}.json")

openai.api_key = os.getenv("OPENAI_API_KEY", "")


def read_top_reactions(path, top_n=3):
    if not os.path.exists(path):
        print(f"⚠️ ログが見つかりません: {path}")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sorted_rows = sorted(reader, key=lambda x: float(x.get("reaction_score", 0)), reverse=True)
        return sorted_rows[:top_n]


def refine_text(text):
    prompt = f"""
次のSNS投稿をより魅力的に書き直してください。
制約:
- 文字数: 100〜200字
- ポジティブな感情
- ハッシュタグ3個まで
- 曖昧な表現を削除

投稿本文:
{text}
"""
    try:
        res = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return res["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ GPT呼び出し失敗: {e}")
        return text


def main():
    print("=== 🧠 WANSTAGE Refiner 実行開始 ===")
    top_posts = read_top_reactions(LOG_FILE)
    if not top_posts:
        print("⚠️ 高反応投稿が見つかりません。")
        return
    refined = []
    for post in top_posts:
        new_text = refine_text(post.get("content", ""))
        refined.append(
            {
                "original": post.get("content", ""),
                "refined": new_text,
                "reaction_score": post.get("reaction_score", ""),
            }
        )
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(refined, f, ensure_ascii=False, indent=2)
    print(f"✅ 再投稿データを保存: {OUT_FILE}")


if __name__ == "__main__":
    main()
