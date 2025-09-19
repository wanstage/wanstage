#!/usr/bin/env bash
set -euo pipefail
ENV_NAME="${1:-stg}"
case "$ENV_NAME" in
  dev) export WAN_ENV=dev ;;
  stg) export WAN_ENV=stg ;;
  prod) export WAN_ENV=prod ;;
  *) echo "NG: env(dev|stg|prod)"; exit 1 ;;
esac
export WAN_DATA_DIR="$HOME/WANSTAGE/data/$WAN_ENV"
export WAN_OUT_DIR="$HOME/WANSTAGE/out/$WAN_ENV"
printenv | grep -E '^WAN_' || true
