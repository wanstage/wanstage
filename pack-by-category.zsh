#!/usr/bin/env zsh
set -euo pipefail
usage(){ echo "Usage: $0 -c categories.csv -o OUT_PREFIX [-f \"media,image,...\"]" >&2; exit 1; }

typeset -A OPT
while getopts c:o:f: h; do
  case "$h" in
    c) OPT[csv]="$OPTARG" ;;
    o) OPT[out]="$OPTARG" ;;
    f) OPT[filters]="$OPTARG" ;;
    *) usage ;;
  esac
done
[[ -n "${OPT[csv]-}" && -n "${OPT[out]-}" ]] || usage

OUTDIR="release_all_${OPT[out]}"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

# フィルタ（未指定ならCSVの全カテゴリ）
FILTERS=()
if [[ -n "${OPT[filters]-}" ]]; then
  IFS=',' read -rA FILTERS <<< "${OPT[filters]}"
fi

# CSV: 1列目=カテゴリ名（例: media,image,094057）
# 行頭#はコメント
CATS=()
while IFS=, read -r cat _; do
  [[ -z "$cat" || "$cat" == \#* ]] && continue
  CATS+="$cat"
done < "${OPT[csv]}"

sel=("${CATS[@]}")
if (( ${#FILTERS[@]} )); then
  sel=()
  for c in "${CATS[@]}"; do
    for f in "${FILTERS[@]}"; do
      [[ "$c" == "$f" ]] && sel+="$c"
    done
  done
fi

# 各カテゴリ名と同名のパス（ディレクトリ/ファイル）があればコピー
for c in "${sel[@]}"; do
  if [[ -e "$c" ]]; then
    echo "[pack] add $c -> $OUTDIR/$c"
    if [[ -d "$c" ]]; then
      rsync -a --delete "$c"/ "$OUTDIR/$c"/
    else
      mkdir -p "$OUTDIR"
      cp -a "$c" "$OUTDIR/"
    fi
  else
    echo "[pack] skip (not found): $c"
  fi
done

# 付随ファイル（任意）
[[ -f minisign_pubkey.txt ]] && cp -a minisign_pubkey.txt "$OUTDIR/"
[[ -d NOTICES ]] && rsync -a NOTICES/ "$OUTDIR/NOTICES/"

# 最低限のREADME
cat > "$OUTDIR/README_${OPT[out]}.txt" <<EOF
WANSTAGE release bundle for ${OPT[out]}
Categories: ${sel[*]:-"(none included)"}
EOF

echo "[pack] done -> $OUTDIR"
