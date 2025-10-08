#!/bin/zsh
set -eu
cd "$HOME/WANSTAGE"
LOG="$HOME/WANSTAGE/logs/nightly_aggregate.log"; exec >>"$LOG" 2>&1
echo "[START] $(date "+%F %T") nightly_aggregate.sh"
trap 'st=$?; echo "[ERR] exit=$st at line $LINENO"; exit $st' ERR
if [ -f ./.env ]; then set -a; . ./.env; set +a; else echo "[WARN] .env missing"; fi
if [ -d "$HOME/WANSTAGE/.venv" ]; then . "$HOME/WANSTAGE/.venv/bin/activate"; fi
echo "[STEP] 集計スクリプト実行"
"$HOME/WANSTAGE/.venv/bin/python3" "$HOME/WANSTAGE/analytics/update_ranking.py" || python3 "$HOME/WANSTAGE/analytics/update_ranking.py"
echo "[STEP] 通知"
"$HOME/WANSTAGE/.venv/bin/python3" "$HOME/WANSTAGE/notify/notify_mux.py" "日次集計完了" || true
echo "[DONE] $(date "+%F %T") nightly_aggregate.sh"
