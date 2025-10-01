#!/usr/bin/env zsh
set -euo pipefail
inv=""; out=""
while getopts "i:o:" opt; do
  case "$opt" in
    i) inv="$OPTARG" ;;
    o) out="$OPTARG" ;;
  esac
done
[[ -n "$inv" && -f "$inv" ]] || { echo "Usage: $0 -i inventory.csv [-o report.csv]"; exit 1; }
[[ -n "$out" ]] && echo 'abs_path,field,expected,actual' > "$out"
miss=0; total=0
tail -n +2 "$inv" | while IFS=, read -r path fmt sb ex mode size sha; do
  (( total++ ))
  path="${path%\"}"; path="${path#\"}"; sb="${sb%\"}"; sb="${sb#\"}"
  if [[ ! -e "$path" ]]; then
    echo "MISSING: $path"; [[ -n "$out" ]] && echo "\"$path\",exists,yes,no" >> "$out"; (( miss++ )); continue
  fi
  magic=$(dd if="$path" bs=4 count=1 2>/dev/null | hexdump -v -e '1/1 "%02X"')
  if [[ "$magic" == 7F454C46* ]]; then realfmt="ELF binary"
  elif [[ "$magic" == FEEDFACE* || "$magic" == CEFAEDFE* || "$magic" == FEEDFACF* || "$magic" == CFFAEDFE* ]]; then realfmt="Mach-O binary"
  elif LC_ALL=C head -c 4096 "$path" | LC_ALL=C awk 'BEGIN{b=0}{for(i=1;i<=length($0);i++){c=substr($0,i,1);if(c !~ /[\t\r\n\040-\176]/){b=1;break}}}END{exit b}'; then realfmt="text"
  else realfmt="binary"; fi
  realsb=""; if IFS= read -r firstline < "$path"; then case "$firstline" in '#!'*) realsb="$firstline";; esac; fi
  realm=$(perl -e '($m)=(stat(shift))[2]; printf "%#o",$m & 0777;' "$path")
  reals=$(perl -e '($s)=(stat(shift))[7]; print $s;' "$path")
  realx="no"; [[ -x "$path" ]] && realx="yes"
  realsha=$(shasum -a 256 "$path" | awk '{print $1}')
  ok=1
  [[ "$fmt"  != "$realfmt" ]] && ok=0 && echo "FMT  : $path  csv=$fmt  real=$realfmt"  && [[ -n "$out" ]] && echo "\"$path\",format,$fmt,$realfmt" >> "$out"
  [[ "$sb"   != "$realsb" ]] && ok=0 && [[ -n "$sb$realsb" ]] && echo "SB   : $path  csv=$sb  real=$realsb" && [[ -n "$out" ]] && echo "\"$path\",shebang,$sb,$realsb" >> "$out"
  [[ "$ex"   != "$realx" ]] && ok=0 && echo "EXEC : $path  csv=$ex   real=$realx"   && [[ -n "$out" ]] && echo "\"$path\",is_executable,$ex,$realx" >> "$out"
  [[ "$mode" != "$realm" ]] && ok=0 && echo "MODE : $path  csv=$mode real=$realm"   && [[ -n "$out" ]] && echo "\"$path\",mode_octal,$mode,$realm" >> "$out"
  [[ "$size" != "$reals" ]] && ok=0 && echo "SIZE : $path  csv=$size real=$reals"   && [[ -n "$out" ]] && echo "\"$path\",size_bytes,$size,$reals" >> "$out"
  [[ "$sha"  != "$realsha" ]]&& ok=0 && echo "SHA  : $path  csv=$sha  real=$realsha"&& [[ -n "$out" ]] && echo "\"$path\",sha256,$sha,$realsha" >> "$out"
  (( ok==1 )) || (( miss++ ))
done
echo "----"; echo "Verified: $total rows; mismatches: $miss"; [[ -n "$out" ]] && echo "Report: $out"
