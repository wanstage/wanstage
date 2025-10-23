#!/usr/bin/env zsh
set -euo pipefail
ROOT="$HOME/WANSTAGE"
LOGDIR="$ROOT/logs"; mkdir -p "$LOGDIR"
OUT="$LOGDIR/magic_flow_$(date +%Y%m%d_%H%M%S).log"

# .env 読込（Slack/LINE/Sheets/Notionなど）
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi

# 1) 魔法プロンプトを環境変数に投入（投稿文・台本の生成方針）
export POST_PROMPT=$'WANSTAGE_FULL_AUTO_MAGIC_FLOW\nカテゴリ：作業系 / 地域密着 / 感情共感（ランダム分散）\n画像：~/WANSTAGE/assets/images/ からランダム選択\n構文分類：結論先出し・数字強調・ネガポジ反転\n出力形式：JSON + Canva構成 + Instagram/Threads/LINE投稿文\nZapier通知：LINE + Slack\n収益ログ：Google Sheets + Notion\n通知タイミング：即時（手動実行）'

# 2) 既存の本番フローを実行
# [DISABLED by script] #   ※ 以前作った full_auto_post_flow.sh をそのまま呼び出し
#   ※ このスクリプト内で：台本/投稿文生成 → 画像選定 → Instagram投稿
#                            → Slack/LINE通知 → ログ保存 まで一括実行
# [DISABLED by script] echo "[RUN] full_auto_post_flow.sh" | tee -a "$OUT"
# [DISABLED by script] bash "$ROOT/full_auto_post_flow.sh" | tee -a "$OUT"

# 3) Flex通知＋DB登録（あれば）
if [ -x "$ROOT/wanstage_flex_notify_and_dbgen.sh" ]; then
  echo "[RUN] wanstage_flex_notify_and_dbgen.sh" | tee -a "$OUT"
  bash "$ROOT/wanstage_flex_notify_and_dbgen.sh" | tee -a "$OUT"
fi

echo "[DONE] Magic flow finished at $(date '+%F %T')" | tee -a "$OUT"

# 4) 成果の要約だけ標準出力に（Slackなどから見やすく）
tail -n 50 "$OUT" || true
