#!/usr/bin/env bash
set -u
TS="$(date +%Y%m%d_%H%M%S)"; LOGDIR="$HOME/WANSTAGE/logs"; OUT="$LOGDIR/vscode_diag_${TS}.log"; TARGET_DIR="${1:-$PWD}"
Y='\033[33m'; G='\033[32m'; C='\033[36m'; N='\033[0m'
say(){ printf "%b\n" "$*"; }; headr(){ say "${C}==> $*${N}"; }; warn(){ say "${Y}[WARN]${N} $*"; }; ok(){ say "${G}[OK]${N} $*"; }
both(){ printf "%s\n" "$*" | tee -a "$OUT"; }; line(){ both "----------------------------------------------------------------"; }
both "VSCode/Mac 簡易診断  $(date '+%Y-%m-%d %H:%M:%S')"; both "TARGET_DIR: $TARGET_DIR"; line
headr "基本環境"; both "SHELL: $SHELL"; sw_vers 2>/dev/null | tee -a "$OUT" || true; uname -a 2>/dev/null | tee -a "$OUT" || true
case ":$PATH:" in *":/opt/homebrew/bin:"*) ok "/opt/homebrew/bin in PATH";; *) warn "/opt/homebrew/bin 不足（M系は追加推奨）";; esac; line
headr "コマンド"; for c in zsh bash code python3 pip3 node npm jq git lsof; do
  if command -v "$c" >/dev/null 2>&1; then both "$(printf '%-8s' "$c"): $(command -v "$c")"; "$c" --version 2>&1 | head -n1 | tee -a "$OUT" || true
  else warn "$c が見つかりません"; fi; done; line
headr "VSCode"; if command -v code >/dev/null 2>&1; then { code --version; code --list-extensions --show-versions | head -n 20; } 2>&1 | tee -a "$OUT"; else warn "code コマンド未設定"; fi; line
headr "プロジェクト"; if [ -d "$TARGET_DIR" ]; then (cd "$TARGET_DIR" && pwd && /bin/ls -la | head -n 50) 2>&1 | tee -a "$OUT"; else warn "対象ディレクトリ未存在: $TARGET_DIR"; fi; line
headr "Python/Node"; python3 -V 2>&1 | tee -a "$OUT" || true; pip3 list --format=columns 2>/dev/null | head -n 30 | tee -a "$OUT" || true
[ -f "$TARGET_DIR/package.json" ] && { head -n 60 "$TARGET_DIR/package.json" | tee -a "$OUT"; } || both "package.json なし"; line
headr ".env (マスク表示)"; for envf in "$TARGET_DIR/.env" "$HOME/WANSTAGE/.env"; do
  [ -f "$envf" ] && { both "検出: $envf"; grep -E '^[A-Za-z0-9_]+=' "$envf" | sed 's/=.*$/=(set)/' | head -n 50 | tee -a "$OUT" >/dev/null; }; done; line
headr "LISTEN(3000/8000/8080) & プロセス"; command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP -sTCP:LISTEN | egrep '(:3000|:8000|:8080)' | tee -a "$OUT" || true
ps -ax | egrep 'python|node|uvicorn|vite|next|streamlit' | egrep -v egrep | head -n 50 | tee -a "$OUT" || true; line
both "ログ保存先: $OUT"; both "完了: $(date '+%Y-%m-%d %H:%M:%S')"
