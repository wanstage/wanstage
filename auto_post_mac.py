import time


def simulate_post(text):
    print("📲 投稿シミュレーション中...")
    time.sleep(1)
    print(f"📝 投稿内容: {text}")
    print("✅ 投稿完了（仮）")


if __name__ == "__main__":
    # 投稿テンプレートを仮で読み込み（実運用ではファイルやAPI経由）
    post = "SNSでの収益化に興味がある方、副業のアイデアを広げてみませんか？詳しくはnoteで解説しています🔗 https://note.com/wanstage_lab"
    simulate_post(post)
