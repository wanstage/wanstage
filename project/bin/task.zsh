#!/usr/bin/env zsh
emulate -LR zsh
set -euo pipefail
setopt ERR_RETURN PIPE_FAIL NO_NOMATCH

SCRIPT_DIR=${0:A:h}
ROOT_DIR=${SCRIPT_DIR:h}
LOG_DIR="${ROOT_DIR}/var/log"
LIB_DIR="${ROOT_DIR}/lib"
CONF_FILE="${ROOT_DIR}/etc/task.env"
mkdir -p "${LOG_DIR}"

source "${LIB_DIR}/logging.zsh"
[[ -f "${CONF_FILE}" ]] && source "${CONF_FILE}"

_tmpdir=
cleanup(){ local code=$?; [[ -n "${_tmpdir:-}" && -d "${_tmpdir}" ]] && rm -rf -- "${_tmpdir}"; ((code==0)) || error "aborted with exit ${code}"; }
trap cleanup EXIT INT TERM
_tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/task.XXXXXXXX") || { error "cannot create tempdir"; exit 1; }

usage(){ cat <<'USAGE'
Usage:
  task.zsh --input PATH [--dry-run] [--verbose]
USAGE
}

# --- 引数パース（重複定義ナシ版） ---
zmodload zsh/zutil
typeset -a help dry verbose in
zparseopts -D -E \
  {h,-help,--help}=help \
  -dry-run=dry --dry-run=dry \
  -verbose=verbose --verbose=verbose \
  -input:=in --input:=in || { usage; exit 2; }

(( ${#help} )) && { usage; exit 0; }
INPUT="${in[2]:-}"
[[ -n "$INPUT" ]] || { usage; exit 2; }
DRY_RUN=$(( ${#dry} > 0 ? 1 : 0 ))
VERBOSE=$(( ${#verbose} > 0 ? 1 : 0 ))

LOG_FILE="${LOG_DIR}/task.$(date -u +%F).log"
{ info "start task input=${INPUT} dry_run=${DRY_RUN} verbose=${VERBOSE}"; } >> "${LOG_FILE}"

main(){
  [[ -r "${INPUT}" ]] || die "input not readable: ${INPUT}"
  (( DRY_RUN )) && { info "dry-run: would process ${INPUT}"; return 0; }
  local lines; lines=$(wc -l < "${INPUT}") || die "wc failed"
  info "processed lines=${lines}"
  print -r -- "lines=${lines}" > "${_tmpdir}/result.txt"
  info "artifact: ${_tmpdir}/result.txt"
}

if (( VERBOSE )); then
  main |& tee -a "${LOG_FILE}"
else
  main >> "${LOG_FILE}" 2>&1
fi
info "done" >> "${LOG_FILE}"
