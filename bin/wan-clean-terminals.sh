#!/usr/bin/env bash
set -Eeuo pipefail
CUR="$(tty | sed 's#/dev/##' 2>/dev/null || echo '')"
[ -n "$CUR" ] || { echo "[wan-clean-terminals] no TTY"; exit 0; }
while read -r T; do
  [ "$T" = "$CUR" ] && continue
  pkill -t "$T" zsh  2>/dev/null || true
  pkill -t "$T" bash 2>/dev/null || true
  pkill -t "$T" login 2>/dev/null || true
done < <(who | awk '{print $2}')
echo "[wan-clean-terminals] kept: $CUR, cleaned: $(who | awk '{print $2}' | grep -v "$CUR" | wc -l | tr -d ' ')"
