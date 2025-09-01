#!/usr/bin/env bash
set -euo pipefail
WF="${1:-post_and_notify}"
case "$WF" in
  post_and_notify)
    if [ -x scripts/WANSTAGE_ONE_BUTTON.sh ]; then bash scripts/WANSTAGE_ONE_BUTTON.sh; else echo "scripts/WANSTAGE_ONE_BUTTON.sh missing"; fi
    if [ -x scripts/log_monitor.sh ]; then bash scripts/log_monitor.sh; else echo "scripts/log_monitor.sh missing"; fi
    ;;
  ztow_cycle)
    if [ -f ztow/runner.py ]; then /usr/bin/env python3 ztow/runner.py; else echo "ztow/runner.py missing"; fi
    ;;
  *) echo "Unknown workflow: $WF"; exit 2;;
esac
echo "[Agent] done."
