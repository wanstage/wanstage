#!/usr/bin/env zsh
set -euo pipefail
list=""; out=""
while getopts "l:o:" opt; do
  case "$opt" in
    l) list="$OPTARG" ;;
    o) out="$OPTARG" ;;
  esac
done
[[ -n "$list" && -f "$list" && -n "$out" ]] || { echo "Usage: $0 -l relpaths.txt -o OUT_BASENAME"; exit 1; }
outdir="${out}"; mkdir -p "$outdir"
tarname="${out}.tar.gz"; zipname="${out}.zip"
tar -C / -chzf "$tarname" -T "$list"
rm -f "$zipname"
while IFS= read -r rp; do dir="/${rp%/*}"; base="${rp##*/}"; (cd "$dir" && zip -q -r "${OLDPWD}/${zipname}" "$base"); done < "$list"
inv="${outdir}/inventory.csv"; echo 'abs_path,format,shebang,is_executable,mode_octal,size_bytes,sha256' > "$inv"
while IFS= read -r rp; do
  f="/$rp"; [[ -e "$f" ]] || { echo "WARN: missing $f" >&2; continue; }
  magic=$(dd if="$f" bs=4 count=1 2>/dev/null | hexdump -v -e '1/1 "%02X"')
  if [[ "$magic" == 7F454C46* ]]; then fmt="ELF binary"
  elif [[ "$magic" == FEEDFACE* || "$magic" == CEFAEDFE* || "$magic" == FEEDFACF* || "$magic" == CFFAEDFE* ]]; then fmt="Mach-O binary"
  elif LC_ALL=C head -c 4096 "$f" | LC_ALL=C awk 'BEGIN{b=0}{for(i=1;i<=length($0);i++){c=substr($0,i,1);if(c !~ /[\t\r\n\040-\176]/){b=1;break}}}END{exit b}'; then fmt="text"
  else fmt="binary"; fi
  sb=""; if IFS= read -r firstline < "$f"; then case "$firstline" in '#!'*) sb="$firstline";; esac; fi
  mode=$(perl -e '($m)=(stat(shift))[2]; printf "%#o",$m & 0777;' "$f")
  size=$(perl -e '($s)=(stat(shift))[7]; print $s;' "$f")
  ex="no"; [[ -x "$f" ]] && ex="yes"
  sha=$(shasum -a 256 "$f" | awk '{print $1}')
  printf '"%s",%s,"%s",%s,%s,%s,%s\n' "$f" "$fmt" "$sb" "$ex" "$mode" "$size" "$sha" >> "$inv"
done < "$list"
echo "DONE: $tarname  $zipname  (inventory: $inv)"
