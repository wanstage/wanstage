#!/usr/bin/env bash
set -euo pipefail
categories_csv=""; out_prefix=""; filters=""
while getopts "c:o:f:" opt; do
  case "$opt" in
    c) categories_csv="$OPTARG" ;; o) out_prefix="$OPTARG" ;; f) filters="$OPTARG" ;;
  esac
done
if [[ -z "$categories_csv" || -z "$out_prefix" || ! -f "$categories_csv" ]]; then
  echo 'Usage: ./pack-by-category.sh -c categories.csv -o OUT_PREFIX [-f "media,image,..."]' >&2; exit 1; fi
declare -A use_cat=()
if [[ -n "${filters}" ]]; then IFS=',' read -r -a arr <<< "$filters"; for c in "${arr[@]}"; do use_cat["$c"]=1; done; fi

tmpdir="$(mktemp -d /tmp/packcat.XXXXXX)"; trap 'rm -rf "$tmpdir"' EXIT

# CSV: name,category,path（CRLF対応）
tail -n +2 "$categories_csv" | while IFS=, read -r name category path; do
  name="${name%$'\r'}"; category="${category%$'\r'}"; path="${path%$'\r'}"
  name="${name%\"}"; name="${name#\"}"
  category="${category%\"}"; category="${category#\"}"
  path="${path%\"}"; path="${path#\"}"
  [[ -n "$category" && -n "$path" ]] || continue
  if [[ ${#use_cat[@]} -gt 0 && -z "${use_cat[$category]:-}" ]]; then continue; fi
  rel="${path#/}"
  printf '%s\n' "${rel%$'\r'}" >> "$tmpdir/$category.relpaths"
done

detect_format() {
  local f="$1" magic
  magic="$(dd if="$f" bs=4 count=1 2>/dev/null | hexdump -v -e '1/1 "%02X"')"
  if [[ "$magic" == 7F454C46* ]]; then echo "ELF binary"
  elif [[ "$magic" == FEEDFACE* || "$magic" == CEFAEDFE* || "$magic" == FEEDFACF* || "$magic" == CFFAEDFE* ]]; then echo "Mach-O binary"
  elif head -c 4096 "$f" | awk 'BEGIN{b=0}{for(i=1;i<=length($0);i++){c=substr($0,i,1);if(c !~ /[\t\r\n\040-\176]/){b=1;break}}}END{exit b}'; then echo "text"
  else echo "binary"; fi
}

sh_quote_csv() { local s="$1"; s="${s//\"/\"\"}"; printf '"%s"' "$s"; }

shopt -s nullglob
for rp in "$tmpdir"/*.relpaths; do
  [[ -f "$rp" ]] || continue
  catname="$(basename "$rp" .relpaths)"
  outbase="${out_prefix}_${catname}"; outdir="${outbase}"; mkdir -p "$outdir"
  # tar: symlinkを実体に追従
  tar -C / -chzf "${outbase}.tar.gz" -T "$rp"
  # zip: / から -@ で相対パスを読み込む
  (cd / && zip -q -r "$OLDPWD/${outbase}.zip" -@) < "$rp"
  # inventory
  inv="${outdir}/inventory.csv"
  echo 'abs_path,format,shebang,is_executable,mode_octal,size_bytes,sha256' > "$inv"
  while IFS= read -r rel; do
    rel="${rel%$'\r'}"; [[ -n "$rel" ]] || continue
    f="/$rel"; [[ -e "$f" ]] || { echo "WARN: missing $f" >&2; continue; }
    fmt="$(detect_format "$f")"
    sb=""; if IFS= read -r firstline < "$f"; then case "$firstline" in '#!'*) sb="$firstline" ;; esac; fi
    mode="$(perl -e '($m)=(stat(shift))[2]; printf "%#o",$m & 0777;' "$f")"
    size="$(perl -e '($s)=(stat(shift))[7]; print $s;' "$f")"
    ex="no"; [[ -x "$f" ]] && ex="yes"
    sha="$(shasum -a 256 "$f" | awk '{print $1}')"
    printf '%s,%s,%s,%s,%s,%s,%s\n' \
      "$(sh_quote_csv "$f")" "$fmt" "$(sh_quote_csv "$sb")" "$ex" "$mode" "$size" "$sha" >> "$inv"
  done < "$rp"
  echo "DONE: ${outbase}.tar.gz  ${outbase}.zip  (inventory: ${inv})"
done
echo "All categories processed."
