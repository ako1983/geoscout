#!/bin/bash
# Cron entry point for the midterms tracker.
#
# cron fires this every Monday; the script itself enforces the 2-week cadence
# by skipping if the last report is less than MIN_DAYS old. That way a missed
# Monday (laptop asleep) is picked up the following Monday instead of
# silently drifting off-schedule.
#
# Usage:
#   run_tracker.sh           scheduled run (respects the 2-week gate)
#   run_tracker.sh --force   run now regardless of the gate
set -uo pipefail

MIDTERMS_HOME="${MIDTERMS_HOME:-$HOME/midterms-tracker}"
ENV_FILE="${MIDTERMS_ENV_FILE:-$HOME/.midterms-tracker.env}"
MIN_DAYS=13
LOG_DIR="$MIDTERMS_HOME/logs"
CRON_LOG="$LOG_DIR/cron.log"
mkdir -p "$LOG_DIR" "$MIDTERMS_HOME/reports"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*" >> "$CRON_LOG"; }

# cron runs with a near-empty environment: no shell profile, minimal PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export MIDTERMS_HOME

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1 && shift

log "---- run started (pid $$, force=$FORCE, user=$(id -un)) ----"

# Load the API key from the private env file (never from the script).
if [[ -f "$ENV_FILE" ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then perms=$(stat -f '%Lp' "$ENV_FILE"); else perms=$(stat -c '%a' "$ENV_FILE"); fi
  if [[ "$perms" != "600" && "$perms" != "400" ]]; then
    log "WARNING: $ENV_FILE has permissions $perms; run: chmod 600 $ENV_FILE"
  fi
  # shellcheck disable=SC1090
  set -a; source "$ENV_FILE"; set +a
fi
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  log "ERROR: ANTHROPIC_API_KEY not set (expected in $ENV_FILE). Aborting."
  exit 1
fi

# Two-week gate based on the newest dated report.
if [[ $FORCE -eq 0 ]]; then
  last=$(ls "$MIDTERMS_HOME/reports/" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.json$' | sort | tail -1)
  if [[ -n "$last" ]]; then
    last_date="${last%.json}"
    last_epoch=$(date -j -f '%Y-%m-%d' "$last_date" '+%s' 2>/dev/null || date -d "$last_date" '+%s')
    age_days=$(( ( $(date '+%s') - last_epoch ) / 86400 ))
    if (( age_days < MIN_DAYS )); then
      log "skip: last report $last_date is $age_days days old (< $MIN_DAYS). Off-week."
      exit 0
    fi
  fi
fi

PY="$MIDTERMS_HOME/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3)"

start=$(date '+%s')
"$PY" "$MIDTERMS_HOME/tracker.py" "$@" >> "$CRON_LOG" 2>&1
rc=$?
log "---- run finished rc=$rc in $(( $(date '+%s') - start ))s ----"

# Optional macOS notification so you know it fired.
if command -v osascript >/dev/null 2>&1; then
  if [[ $rc -eq 0 ]]; then
    osascript -e "display notification \"New report in $MIDTERMS_HOME/reports\" with title \"Midterms tracker\"" >/dev/null 2>&1 || true
  else
    osascript -e "display notification \"Run failed (rc=$rc). See logs/cron.log\" with title \"Midterms tracker\"" >/dev/null 2>&1 || true
  fi
fi
exit $rc
