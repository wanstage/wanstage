#!/usr/bin/env bash
set -Eeuo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cur_tty="$(/usr/bin/tty | sed 's#/dev/##')"
cnt_total=0; cnt_killed=0

while read -r _user tty _rest; do
  [[ -z "${tty:-}" || "$tty" == "$cur_tty" || "$tty" == "console" ]] && continue
  for p in zsh login bash; do
    pkill -t "$tty" "$p" 2>/dev/null && ((cnt_killed+=1)) || true
  done
  ((cnt_total+=1))
done < <(who)

echo "[wan-clean-terminals] kept: ${cur_tty}, cleaned: ${cnt_killed} - ${cnt_total}"
