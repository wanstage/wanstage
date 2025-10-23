#!/usr/bin/env zsh
set -euo pipefail

ROOT="$HOME/WANSTAGE"
ts="$(date +%Y%m%d_%H%M%S)"
echo "[-] Disable stray calls to full_auto_post_flow.sh  ($ts)"

# 1) ターゲット一覧（見つかったファイルのみ処理）
targets=(
  "$ROOT/agent.sh"
  "$ROOT/python_src/scheduler_main.py"
  "$ROOT/tools/wan-diagnose.sh"
  "$ROOT/bin/project/wan-post.sh"
  "$ROOT/bin/wan-post.sh"
  "$ROOT/scripts/run_magic_flow_now.sh"
  "$ROOT/remote/app.py"
)

# 2) バックアップ & コメントアウト（行内に full_auto_post_flow.sh を含む行を # で無効化）
for f in $targets; do
  if [[ -f "$f" ]]; then
    cp "$f" "$f.bak_${ts}"
    # 行頭にコメントを付ける（同行内に文字があってもOK）
    perl -i -pe 's/^(.*full_auto_post_flow\.sh.*)$/# [DISABLED by script] $1/g' "$f"
    echo "[patched] $f"
  fi
done

# 3) 念のため “scripts/” にダミーを常設（どこから呼ばれても安全に終了）
mkdir -p "$ROOT/scripts"
cat > "$ROOT/scripts/full_auto_post_flow.sh" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
LOG_DIR="${WAN_LOG_DIR:-$HOME/WANSTAGE/logs}"
mkdir -p "$LOG_DIR"
{
  echo "$(date +'%F %T') [noop] full_auto_post_flow.sh is disabled; doing nothing."
} >> "$LOG_DIR/full_auto.log"
exit 0
EOS
chmod +x "$ROOT/scripts/full_auto_post_flow.sh"
echo "[stub] $ROOT/scripts/full_auto_post_flow.sh created"

# 4) 検証：まだ呼び出しが残っていないか再スキャン
echo
echo "== re-scan =="
grep -R --line-number --color -e 'full_auto_post_flow\.sh' "$ROOT" || echo "(no more references)"

echo
echo "done."
