#!/usr/bin/env zsh
set -euo pipefail

# collect-from-path.zsh  (feature/flags version)
# -f FILE : コマンド名リスト (改行区切り)
# -o OUT  : 出力ベース名 (デフォルト: pkg_YYYYmmdd_HHMMSS)
# -D DIRS : 追加探索ディレクトリ (":" 区切り)
# -I      : Mach-O の依存 .dylib も収集 (otool -L)
# -h      : ヘルプ
# 出力: OUT/, OUT.tar.gz, OUT.zip（inventory.csv に codesign 情報も出力）

usage() {
  cat <<'H'
Usage:
  collect-from-path.zsh [-f commands.txt] [-o OUTNAME] [-D dir1:dir2:...] [-I] [cmd1 cmd2 ...]
Options:
  -f FILE   command list file (newline separated)
  -o OUT    output basename (default: pkg_YYYYmmdd_HHMMSS)
  -D DIRS   extra search dirs (colon-separated)
  -I        include dependent .dylib for Mach-O binaries
  -h        show this help
H
}

LIST_FILE=""; OUTNAME=""; EXTRA_DIRS=""; INCLUDE_DEPS=0
while getopts "f:o:D:Ih" opt; do
  case "$opt" in
    f) LIST_FILE="$OPTARG" ;;
    o) OUTNAME="$OPTARG" ;;
    D) EXTRA_DIRS="$OPTARG" ;;
    I) INCLUDE_DEPS=1 ;;
    h) usage; exit 0 ;;
    *) usage; exit 1 ;;
  esac
done
shift $((OPTIND-1))

ts=$(date +"%Y%m%d_%H%M%S")
[[ -z "$OUTNAME" ]] && OUTNAME="wanstage_bins_${ts}"

typeset -a CMDNAMES
CMDNAMES=()
if [[ -n "$LIST_FILE" ]]; then
  [[ -f "$LIST_FILE" ]] || { echo "List file not found: $LIST_FILE" >&2; exit 1; }
  while IFS= read -r line; do
    line="${line#"${line%%[![:space:]]*}"}"; line="${line%"${line##*[![:space:]]}"}"
    line="${line//　/}"
    [[ -n "$line" ]] && CMDNAMES+=("$line")
  done < "$LIST_FILE"
fi
(( $# > 0 )) && CMDNAMES+=("$@")
(( ${#CMDNAMES} > 0 )) || { echo "コマンド名がありません。-f または引数で指定してください。"; exit 1; }

# 検索パス
typeset -a SEARCH_DIRS
IFS=':' read -rA path_dirs <<< "$PATH"
SEARCH_DIRS=(
  ${path_dirs}
  /opt/homebrew/bin /usr/local/bin /usr/bin /bin
  ${HOME}/.local/bin ${HOME}/.cargo/bin ${HOME}/.npm-global/bin ${HOME}/.yarn/bin
)
if [[ -n "$EXTRA_DIRS" ]]; then
  IFS=':' read -rA extra <<< "$EXTRA_DIRS"
  SEARCH_DIRS+=(${extra})
fi
typeset -A seen; typeset -a UNIQUE_DIRS
for d in "${SEARCH_DIRS[@]}"; do
  [[ -n "$d" && -d "$d" && -z "${seen[$d]-}" ]] && { UNIQUE_DIRS+=("$d"); seen[$d]=1; }
done
SEARCH_DIRS=("${UNIQUE_DIRS[@]}")

OUTDIR="$OUTNAME"
mkdir -p "$OUTDIR"
INV="$OUTDIR/inventory.csv"
LISTTXT="$OUTDIR/filelist.txt"
TMPLIST="$OUTDIR/relpaths.txt"
: > "$INV"; : > "$LISTTXT"; : > "$TMPLIST"

print "abs_path,format,shebang,is_executable,mode_octal,size_bytes,sha256,codesign,team_id,bundle_id,notarized" >> "$INV"

detect_format() {
  local f="$1"
  local magic; magic=$(dd if="$f" bs=4 count=1 2>/dev/null | hexdump -v -e '1/1 "%02X"')
  case "$magic" in
    7F454C46*) echo "ELF binary" ;;
    FEEDFACE*|CEFAEDFE*|FEEDFACF*|CFFAEDFE*) echo "Mach-O binary" ;;
    *)
      if LC_ALL=C awk 'NR==1,NR==4096{for(i=1;i<=length($0);i++){c=substr($0,i,1); if (c ~ /[^\t\r\n\040-\176]/) bad=1}} END{exit bad}' "$f" 2>/dev/null
      then echo "text"; else echo "binary"; fi ;;
  esac
}

get_shebang() { local l; l=$(LC_ALL=C head -n1 "$1" 2>/dev/null || true); [[ "$l" == \#!* ]] && echo "$l" || echo ""; }

typeset -A DEPS_SEEN
resolve_deps() {
  local bin="$1"
  command -v otool >/dev/null 2>&1 || return 0
  [[ "$(detect_format "$bin")" != "Mach-O binary" ]] && return 0
  otool -L "$bin" 2>/dev/null | awk 'NR>1 {print $1}' | sed 's/^(//;s/)$//' | while IFS= read -r lib; do
    if [[ "$lib" == /* && -f "$lib" && -z "${DEPS_SEEN[$lib]-}" ]]; then
      DEPS_SEEN[$lib]=1
      print -- "$lib" >> "$LISTTXT"
    fi
  done
}

typeset -A FILES_SEEN
for cmd in "${CMDNAMES[@]}"; do
  if real=$(command -v -- "$cmd" 2>/dev/null); then
    [[ -f "$real" && -z "${FILES_SEEN[$real]-}" ]] && { FILES_SEEN[$real]=1; print -- "$real" >> "$LISTTXT"; ((INCLUDE_DEPS)) && resolve_deps "$real"; }
    continue
  fi
  for d in "${SEARCH_DIRS[@]}"; do
    f="$d/$cmd"
    [[ -f "$f" && -z "${FILES_SEEN[$f]-}" ]] && { FILES_SEEN[$f]=1; print -- "$f" >> "$LISTTXT"; ((INCLUDE_DEPS)) && resolve_deps "$f"; }
  done
done

typeset -a FILES
IFS=$'\n' FILES=($(sort -u "$LISTTXT"))
printf "%s\n" "${FILES[@]}" > "$LISTTXT"

codesign_info() {
  local f="$1"; local line team="" id="" bn="" nota="unknown"
  if /usr/bin/codesign -dv "$f" 2>"/tmp/cs.$$" ; then :; fi
  if grep -q "Authority=" "/tmp/cs.$$"; then
    line="signed"
  elif grep -q "not signed" "/tmp/cs.$$"; then
    line="unsigned"
  else
    line="unknown"
  fi
  team=$(grep -Eo 'TeamIdentifier=[A-Za-z0-9]+' "/tmp/cs.$$" | sed 's/TeamIdentifier=//;q' || true)
  id=$(grep -Eo 'Identifier=[^ ]+' "/tmp/cs.$$" | sed 's/Identifier=//;q' || true)
  # notarization は spctl で近似判定
  if command -v spctl >/dev/null 2>&1; then
    if spctl --assess --type execute "$f" >/dev/null 2>&1; then
      nota="accepted"
    else
      nota="rejected"
    fi
  fi
  rm -f "/tmp/cs.$$"
  echo "$line" "$team" "$id" "$nota"
}

for f in "${FILES[@]}"; do
  [[ -f "$f" ]] || continue
  fmt=$(detect_format "$f"); sb=$(get_shebang "$f")
  mode=$(stat -f %p "$f" 2>/dev/null | tail -n1 || echo "")
  mode_oct=""; [[ -n "$mode" ]] && mode_oct=$(printf "%#o" "$(( 8#${mode#?} & 0777 ))")
  size=$(stat -f %z "$f" 2>/dev/null || wc -c < "$f")
  execflag="no"; [[ -x "$f" ]] && execflag="yes"
  sha=$(shasum -a 256 "$f" | awk '{print $1}')
  cs team id nota=$(codesign_info "$f")
  print "\"$f\",$fmt,\"$sb\",$execflag,$mode_oct,$size,$sha,$cs,$team,$id,$nota" >> "$INV"
  rp="${f#/}"; print -- "$rp" >> "$TMPLIST"
done

# archives
tar -C / -czf "${OUTNAME}.tar.gz" -T "$TMPLIST"
rm -f "${OUTNAME}.zip"
while IFS= read -r rp; do
  dir="/${rp%/*}"; base="${rp##*/}"
  (cd "$dir" && zip -q -r --symlinks "${OLDPWD}/${OUTNAME}.zip" "$base")
done < "$TMPLIST"

echo "DONE: ${OUTDIR}  ${OUTNAME}.tar.gz  ${OUTNAME}.zip"
