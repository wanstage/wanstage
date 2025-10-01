#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"
INTERVAL="${INTERVAL:-10}"
MAX_RETRY="${MAX_RETRY:-5}"
RUN_LABEL="${RUN_LABEL:-ztow_cycle}"
LOG_DIR="logs"; mkdir -p "$LOG_DIR"
MAIN_LOG="$LOG_DIR/agent_loop.log"
RUN_LOG="$LOG_DIR/run_$(/bin/date +%Y%m%d).log"
ERR_LOG="$LOG_DIR/agent_loop.err.log"
ts(){ /bin/date "+%Y-%m-%d %H:%M:%S"; }
rotate(){ for f in "$MAIN_LOG" "$RUN_LOG" "$ERR_LOG"; do [ -f "$f" ] || continue; sz=$(/usr/bin/wc -c <"$f"); if [ "$sz" -gt 1048576 ]; then /bin/mv "$f" "${f%.log}.log.$(/bin/date +%H%M%S)"; fi; done; }
notify(){ [ -n "${SLACK_WEBHOOK_URL:-}" ] || return 0; /usr/bin/curl -s -X POST -H "Content-type: application/json" --data "{\"text\":\"$1\"}" "$SLACK_WEBHOOK_URL" >/dev/null || true; }
run_once(){ n=0; delay=2; while :; do echo "[$(ts)] start $RUN_LABEL" | /usr/bin/tee -a "$RUN_LOG" >>"$MAIN_LOG"; if /bin/bash agent/agent_run.sh "$RUN_LABEL" >>"$RUN_LOG" 2>&1; then echo "[$(ts)] success $RUN_LABEL" | /usr/bin/tee -a "$RUN_LOG" >>"$MAIN_LOG"; return 0; else n=$((n+1)); echo "[$(ts)] fail $RUN_LABEL retry=$n" | /usr/bin/tee -a "$RUN_LOG" >>"$MAIN_LOG"; [ -n "${SLACK_WEBHOOK_URL:-}" ] && notify ":warning: $RUN_LABEL failed (retry $n/$MAX_RETRY)"; if [ "$n" -ge "$MAX_RETRY" ]; then echo "[$(ts)] giveup $RUN_LABEL after $n retries" | /usr/bin/tee -a "$RUN_LOG" >>"$MAIN_LOG"; [ -n "${SLACK_WEBHOOK_URL:-}" ] && notify ":red_circle: $RUN_LABEL give up after $n retries"; return 1; fi; /bin/sleep "$delay"; delay=$((delay*2)); [ "$delay" -gt 60 ] && delay=60; fi; done; }
echo "[$(ts)] agent_loop start label=$RUN_LABEL interval=${INTERVAL}s max_retry=${MAX_RETRY}" | /usr/bin/tee -a "$MAIN_LOG"
while :; do rotate; { run_once || true; } 2>>"$ERR_LOG"; /bin/sleep "$INTERVAL"; done
