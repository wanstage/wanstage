#!/bin/zsh
set -euo pipefail
BASE_DIR="${BASE_DIR:-$HOME/WANSTAGE}"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

export PYTHONPATH="$BASE_DIR/python_src:$PYTHONPATH"
ts="$(date +%Y%m%d_%H%M%S)"
log="$LOG_DIR/agent_py_${ts}.log"

echo "[INFO] start python scheduler_main.py" | tee -a "$log"
python3 "$BASE_DIR/python_src/scheduler_main.py" 2>&1 | tee -a "$log"
echo "[INFO] end" | tee -a "$log"
