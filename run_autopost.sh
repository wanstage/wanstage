#!/bin/bash

echo "🐍 仮想環境をアクティブにするか、環境変数を確認してください"

echo "📸 画像取得中..."
img_output=$(python3 bin/image_generator.py)

if [ -z "$img_output" ]; then
  echo "⚠️ ローカル画像が見つかりません"
  img_path=""
  img_src="none"
else
  IFS='|' read -r img_path img_src <<< "$img_output"
  echo "🖼 画像選定完了：$img_path（source: $img_src）"
fi

echo "📝 SNS投稿文生成中..."
caption=$(python3 generate_post_template.py)

log_path="post_log.csv"
timestamp=$(date "+%Y-%m-%d %H:%M:%S")
echo "$timestamp,\"$caption\",\"$img_path\",$img_src" >> "$log_path"
echo "🗂 投稿ログに記録: $log_path"

echo "📲 投稿シミュレーション中..."
echo "📝 投稿内容: $caption"
[ -n "$img_path" ] && echo "🖼 使用画像: $img_path"

echo "✅ 実行完了！"
