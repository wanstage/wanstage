#!/usr/bin/env zsh
emulate -LR zsh
: "${NO_COLOR:=0}"
_should_color(){ [[ -t 1 && $NO_COLOR -eq 0 ]] }
C_RESET=$'\e[0m'; C_GREEN=$'\e[32m'; C_YELLOW=$'\e[33m'; C_RED=$'\e[31m'
_ts(){ date -u "+%Y-%m-%dT%H:%M:%SZ"; }
_log(){ local lvl="$1"; shift; local ts="$(_ts)"; local msg="${ts} ${lvl} $*"
  if _should_color; then
    case "$lvl" in
      INFO)  print -u1 -- "${C_GREEN}${msg}${C_RESET}" ;;
      WARN)  print -u2 -- "${C_YELLOW}${msg}${C_RESET}" ;;
      ERROR) print -u2 -- "${C_RED}${msg}${C_RESET}" ;;
      *)     print -u1 -- "$msg" ;;
    esac
  else
    case "$lvl" in
      INFO)  print -u1 -- "$msg" ;;
      WARN)  print -u2 -- "$msg" ;;
      ERROR) print -u2 -- "$msg" ;;
      *)     print -u1 -- "$msg" ;;
    esac
  fi
}
info(){ _log INFO "$@" }
warn(){ _log WARN "$@" }
error(){ _log ERROR "$@" }
die(){ error "$@"; [[ "${DIE_MODE:-exit}" == "return" ]] && return 1 || exit 1; }
