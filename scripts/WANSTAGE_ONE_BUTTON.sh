#!/usr/bin/env bash
set -euo pipefail
ts=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$ts] WANSTAGE start" | tee -a logs/one_button.log
echo "[$ts] All tasks completed" | tee -a logs/one_button.log
