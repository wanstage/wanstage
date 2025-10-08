#!/usr/bin/env bash
set -euo pipefail
set -x
trap 'echo "[ERROR] line:$LINENO"; exit 1' ERR

log_file="trace_log_$(date +%Y%m%d-%H%M%S).log"
echo "[DEBUG] log_file=$log_file"
exec > >(tee -a "$log_file") 2>&1

echo "[TRACE] start: $(date)"
echo "[TRACE] user: $(whoami)"
echo "[TRACE] pwd: $(pwd)"
echo "[TRACE] args: $*"
echo "[TRACE] PATH: $PATH"
echo "[TRACE] shell: $SHELL"
echo "[DEBUG] uname: $(uname -a)"
echo "[DEBUG] pid: $$"

echo "[TRACE] git status"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status -s || echo "[WARN] git status failed"
  git log --oneline -n 3 || echo "[WARN] git log failed"
else
  echo "[WARN] not a git repo"
fi

echo "[TRACE] pre-commit"
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit run --all-files || echo "[WARN] pre-commit returned nonzero"
else
  echo "[WARN] pre-commit missing"
fi

echo "[TRACE] npm scripts"
if command -v npm >/dev/null 2>&1; then
  npm run || echo "[WARN] npm run failed"
else
  echo "[WARN] npm missing"
fi

echo "[TRACE] git-lfs"
if command -v git-lfs >/dev/null 2>&1; then
  git lfs ls-files || echo "[WARN] no LFS files or not configured"
else
  echo "[INFO] git-lfs missing"
fi

echo "[DEBUG] ps_count=$(ps | wc -l | tr -d ' ')"
echo "[DEBUG] disk=$(df -h . | tail -1)"
if command -v vm_stat >/dev/null 2>&1; then
  echo "[DEBUG] mem: $(vm_stat | grep 'Pages active' || true)"
else
  echo "[DEBUG] mem: N/A"
fi
if uptime 2>/dev/null | grep -q 'load averages:'; then
  echo "[DEBUG] load: $(uptime | awk -F'load averages:' '{print $2}' | xargs)"
else
  echo "[DEBUG] load: $(uptime 2>/dev/null || echo N/A)"
fi

echo "[TRACE] end: $(date)"
echo "[TRACE] saved: $log_file"
set +x
