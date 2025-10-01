#!/usr/bin/env zsh
set -euo pipefail
[[ $# -eq 2 ]] || { echo "Usage: $0 file.tar.gz file.zip"; exit 1; }
tarfile="$1"; zipfile="$2"
tar -tzf "$tarfile" | sort > /tmp/tarlist.$$
unzip -l "$zipfile" | awk 'NR>3 && $0!~/----/ && NF{ $1=""; $2=""; $3=""; sub(/^[[:space:]]+/, ""); print }' | sort > /tmp/ziplist.$$
echo "---- only in tar ----"; comm -23 /tmp/tarlist.$$ /tmp/ziplist.$$
echo "---- only in zip ----"; comm -13 /tmp/tarlist.$$ /tmp/ziplist.$$
rm -f /tmp/tarlist.$$ /tmp/ziplist.$$
