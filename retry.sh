#!/usr/bin/env bash
set -euo pipefail
i=0; max=3
until "$@"; do
  i=$((i+1))
  [ $i -ge $max ] && echo "FAILED after $i tries" && exit 1
  sleep $((2**i))
done
