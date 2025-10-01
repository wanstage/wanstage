#!/usr/bin/env zsh
set -euo pipefail
inv="${1:-inventory.csv}"
outdir="${2:-NOTICES}"
mkdir -p "$outdir"
# Cellarパスからformula名を抽出
awk -F, 'NR>1{gsub(/^"|"$/,"",$1); path=$1; if (path ~ /\/Cellar\//){split(path,a,"/"); for(i=1;i<=NF;i++){} print a[5]}}' "$inv" | \
  sort -u | while read -r formula; do
  [[ -n "$formula" ]] || continue
  brew info --json=v2 "$formula" > "$outdir/$formula.json" 2>/dev/null || true
  # 簡易ライセンス抽出
  jq -r '.formulae[0] | "\(.name)\t\(.license // "unknown")\t\(.homepage // "")"' "$outdir/$formula.json" 2>/dev/null \
     >> "$outdir/OVERVIEW.tsv" || true
done
echo "NOTICES collected into $outdir"
