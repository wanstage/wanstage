#!/usr/bin/env zsh
set -e
echo '--- / ---'
curl -sS -i http://127.0.0.1:3000/ | head -n 20; echo
echo '--- /messages ---'
curl -sS -i http://127.0.0.1:3000/messages | head -n 20; echo
