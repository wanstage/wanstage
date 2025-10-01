#!/usr/bin/env zsh
set -Eeuo pipefail
setopt extended_glob null_glob

# Usage: fix-scripts.zsh [TARGET_DIR] [--shell=zsh|bash|keep] [--fix=apply|warn|dry-run]
target="${1:-$HOME/WANSTAGE/scripts}"
shell_policy="zsh"     # zsh | bash | keep
fix_mode="apply"       # apply | warn | dry-run

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --shell=*) shell_policy="${1#*=}";;
    --fix=*)   fix_mode="${1#*=}";;
    -h|--help) echo "Usage: $0 [TARGET] [--shell=zsh|bash|keep] [--fix=apply|warn|dry-run]"; exit 0;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
  shift
done

[[ -d "$target" ]] || { echo "ERR: not found: $target" >&2; exit 1; }
case "$shell_policy" in zsh|bash|keep) ;; *) echo "ERR: --shell must be zsh|bash|keep" >&2; exit 2;; esac
case "$fix_mode" in apply|warn|dry-run) ;; *) echo "ERR: --fix must be apply|warn|dry-run" >&2; exit 2;; esac

# zsh ネイティブの再帰グロブで .sh / .py を列挙（サブディレクトリ含む）
typeset -a files
files=($target/**/*.(sh|py)(.N))
if (( ${#files} == 0 )); then
  echo "No .sh/.py under $target"
  exit 0
fi

want() { echo "#!/usr/bin/env $1"; }

fix_shebang() {
  local f="$1" want_line
  case "$shell_policy" in
    keep) echo "KEEP shebang: $f"; return 0;;
    zsh)  want_line="$(want zsh)";;
    bash) want_line="$(want bash)";;
  esac
  local first; first="$(head -n1 "$f" 2>/dev/null || true)"
  if [[ "$first" == '#!'* ]]; then
    [[ "$first" == "$want_line"* ]] && { echo "OK   shebang: $f"; return 0; }
    case "$fix_mode" in
      dry-run|warn) echo "WARN shebang -> ${shell_policy}: $f (no change)";;
      apply) sed -i '' "1s|^#!.*$|${want_line}|" "$f"; echo "FIX  shebang -> ${shell_policy}: $f";;
    esac
  else
    case "$fix_mode" in
      dry-run|warn) echo "WARN add shebang -> ${shell_policy}: $f (no change)";;
      apply) sed -i '' "1s|^|${want_line}\n|" "$f"; echo "ADD  shebang -> ${shell_policy}: $f";;
    esac
  fi
}

normalize_lf() {
  local f="$1"
  if LC_ALL=C grep -q $'\r$' "$f"; then
    case "$fix_mode" in
      dry-run|warn) echo "WARN CRLF->LF: $f (no change)";;
      apply) perl -i -pe 's/\r$//' "$f"; echo "FIX  CRLF->LF: $f";;
    esac
  else
    echo "OK   LF     : $f"
  fi
}

ensure_exec() {
  local f="$1"
  if [[ -x "$f" ]]; then
    echo "OK   +x     : $f"
  else
    case "$fix_mode" in
      dry-run|warn) echo "WARN add +x : $f (no change)";;
      apply) chmod +x "$f"; echo "ADD  +x    : $f";;
    esac
  fi
}

echo "Target: $target  shell=${shell_policy}  fix=${fix_mode}"
for f in "${files[@]}"; do
  [[ "${f##*.}" == "py" ]] || fix_shebang "$f"   # .shのみ shebang 調整
  normalize_lf "$f"                               # CRLF->LF（必要時のみ）
  ensure_exec "$f"                                # 実行ビット
done
echo "DONE."
