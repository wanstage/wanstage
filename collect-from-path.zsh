#!/usr/bin/env zsh
set -euo pipefail
# collect-from-path.zsh — PATHから実体収集し、構造維持で tar.gz/zip 作成。
# inventory.csv（形式/shebang/権限/SHA256）と filelist.txt を生成。
# 使い方:
#   ./collect-from-path.zsh [-f commands.txt] [-o OUTNAME] [-D dir1:dir2:...] [-I]
#   ./collect-from-path.zsh ffmpeg ffprobe cwebp dwebp -I

LIST_FILE=""; OUTNAME=""; EXTRA_DIRS=""; INCLUDE_DEPS=0
while getopts "f:o:D:I" opt; do
  case "$opt" in
    f) LIST_FILE="$OPTARG" ;;
    o) OUTNAME="$OPTARG" ;;
    D) EXTRA_DIRS="$OPTARG" ;;
    I) INCLUDE_DEPS=1 ;;
  esac
done
shift $((OPTIND-1))

ts=$(date +"%Y%m%d_%H%M%S")
[[ -z "$OUTNAME" ]] && OUTNAME="pkg_${ts}"

typeset -a CMDNAMES; CMDNAMES=()
normalize_line() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; s="${s%"${s##*[![:space:]]}"}"; s="${s//　/}"; print -- "$s"; }
if [[ -n "$LIST_FILE" ]]; then
  [[ -f "$LIST_FILE" ]] || { echo "List file not found: $LIST_FILE" >&2; exit 1; }
  while IFS= read -r line; do line="$(normalize_line "$line")"; [[ -n "$line" ]] && CMDNAMES+=("$line"); done < "$LIST_FILE"
fi
(( $# > 0 )) && for a in "$@"; do CMDNAMES+=("$(normalize_line "$a")"); done
(( ${#CMDNAMES} )) || { echo "コマンド名が指定されていません。-f または 引数で指定してください。" >&2; exit 1; }

typeset -a SEARCH_DIRS
IFS=':' read -rA path_dirs <<< "$PATH"
SEARCH_DIRS=(${path_dirs} /opt/homebrew/bin /usr/local/bin /usr/bin /bin "$HOME/.local/bin" "$HOME/.cargo/bin" "$HOME/.npm-global/bin" "$HOME/.yarn/bin")
if [[ -n "$EXTRA_DIRS" ]]; then IFS=':' read -rA extra <<< "$EXTRA_DIRS"; SEARCH_DIRS+=(${extra}); fi
typeset -A seen; typeset -a UNIQUE_DIRS; for d in "${SEARCH_DIRS[@]}"; do [[ -d "$d" && -z "${seen[$d]-}" ]] && UNIQUE_DIRS+=("$d") && seen[$d]=1; done
SEARCH_DIRS=("${UNIQUE_DIRS[@]}")

OUTDIR="$OUTNAME"; mkdir -p "$OUTDIR"
INV="$OUTDIR/inventory.csv"; LISTTXT="$OUTDIR/filelist.txt"
print "abs_path,format,shebang,is_executable,mode_octal,size_bytes,sha256" > "$INV"; : > "$LISTTXT"

detect_format(){ local f="$1"; local magic; magic=$(dd if="$f" bs=4 count=1 2>/dev/null | hexdump -v -e '1/1 "%02X"')
  case "$magic" in
    7F454C46*) echo "ELF binary" ;;
    FEEDFACE*|CEFAEDFE*|FEEDFACF*|CFFAEDFE*) echo "Mach-O binary" ;;
    *) if LC_ALL=C awk 'NR==1,NR==4096{for(i=1;i<=length($0);i++){c=substr($0,i,1);if(c ~ /[^\t\r\n\040-\176]/)bad=1}}END{exit bad}' "$f" 2>/dev/null; then echo "text"; else echo "binary"; fi ;;
  esac
}
get_shebang(){ local f="$1"; local line; line=$(LC_ALL=C head -n1 "$f" 2>/dev/null || true); [[ "$line" == \#!* ]] && echo "$line" || echo ""; }

typeset -A DEPS_SEEN
resolve_deps(){ local bin="$1"; command -v otool >/dev/null 2>&1 || return 0
  [[ "$(detect_format "$bin")" != "Mach-O binary" ]] && return 0
  while IFS= read -r lib; do
    [[ "$lib" == /* && -f "$lib" && -z "${DEPS_SEEN[$lib]-}" ]] && DEPS_SEEN[$lib]=1 && print -- "$lib" >> "$LISTTXT"
  done < <(otool -L "$bin" 2>/dev/null | awk 'NR>1{print $1}' | sed 's/^(//;s/)$//')
}

typeset -A FILES_SEEN
for cmd in "${CMDNAMES[@]}"; do
  if real=$(command -v -- "$cmd" 2>/dev/null); then
    [[ -f "$real" && -z "${FILES_SEEN[$real]-}" ]] && FILES_SEEN[$real]=1 && print -- "$real" >> "$LISTTXT" && ((INCLUDE_DEPS)) && resolve_deps "$real"
    continue
  fi
  for d in "${SEARCH_DIRS[@]}"; do f="$d/$cmd"; [[ -f "$f" && -z "${FILES_SEEN[$f]-}" ]] && FILES_SEEN[$f]=1 && print -- "$f" >> "$LISTTXT" && ((INCLUDE_DEPS)) && resolve_deps "$f"; done
done

typeset -a FILES; IFS=$'\n' FILES=($(sort -u "$LISTTXT")); printf "%s\n" "${FILES[@]}" > "$LISTTXT"

for f in "${FILES[@]}"; do
  [[ -f "$f" ]] || continue
  fmt=$(detect_format "$f"); sb=$(get_shebang "$f")
  mode=$(stat -f %p "$f" 2>/dev/null | tail -n1 || echo ""); mode_oct=""; [[ -n "$mode" ]] && mode_oct=$(printf "%#o" "$(( 8#${mode#?} & 0777 ))")
  size=$(stat -f %z "$f" 2>/dev/null || wc -c < "$f"); execflag="no"; [[ -x "$f" ]] && execflag="yes"
  sha=$(shasum -a 256 "$f" | awk '{print $1}')
  print "\"$f\",$fmt,\"$sb\",$execflag,$mode_oct,$size,$sha" >> "$INV"
done

TAR="${OUTNAME}.tar.gz"; ZIP="${OUTNAME}.zip"; TMPLIST="$OUTDIR/relpaths.txt"; : > "$TMPLIST"
for f in "${FILES[@]}"; do rp="${f#/}"; print -- "$rp" >> "$TMPLIST"; done
tar -C / -czf "$TAR" -T "$TMPLIST"
rm -f "$ZIP"; while IFS= read -r rp; do dir="/${rp%/*}"; base="${rp##*/}"; (cd "$dir" && zip -q -r --symlinks "${OLDPWD}/${ZIP}" "$base"); done < "$TMPLIST"
echo "DONE: ${OUTDIR}, ${TAR}, ${ZIP}"
