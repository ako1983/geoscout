#!/bin/bash
# Installs the midterms tracker into ~/midterms-tracker and registers the cron job.
# Safe to re-run: it updates the code and replaces (never duplicates) its cron line.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="${MIDTERMS_HOME:-$HOME/midterms-tracker}"
ENV_FILE="$HOME/.midterms-tracker.env"
# Every Monday at 07:00 local time; run_tracker.sh skips alternate weeks.
CRON_SCHEDULE="0 7 * * 1"
CRON_TAG="# midterms-tracker"
CRON_LINE="$CRON_SCHEDULE $DEST/run_tracker.sh $CRON_TAG"

echo "==> Installing to $DEST"
mkdir -p "$DEST/reports" "$DEST/logs"
cp "$SRC_DIR/tracker.py" "$SRC_DIR/run_tracker.sh" "$SRC_DIR/requirements.txt" "$DEST/"
chmod +x "$DEST/run_tracker.sh" "$DEST/tracker.py"

# The anthropic SDK needs Python >= 3.10 (macOS's /usr/bin/python3 is often 3.9).
PYTHON=""
for cand in python3.13 python3.12 python3.11 python3.10 python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(sys.version_info < (3,10))' 2>/dev/null; then
    PYTHON="$(command -v "$cand")"; break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo "ERROR: need Python >= 3.10. Install with: brew install python@3.12" >&2
  exit 1
fi
echo "==> Using $PYTHON ($("$PYTHON" --version))"
"$PYTHON" -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install -q --upgrade pip
"$DEST/.venv/bin/pip" install -q -r "$DEST/requirements.txt"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "==> Creating $ENV_FILE (chmod 600). Paste your key into it."
  umask 077
  cat > "$ENV_FILE" <<'EOF'
# Read by ~/midterms-tracker/run_tracker.sh. Keep this file chmod 600.
export ANTHROPIC_API_KEY="sk-ant-REPLACE_ME"
EOF
fi
chmod 600 "$ENV_FILE"

echo "==> Registering cron job"
( crontab -l 2>/dev/null | grep -v -F "$CRON_TAG" || true; echo "$CRON_LINE" ) | crontab -
echo
echo "Installed crontab entry:"
crontab -l | grep -F "$CRON_TAG"
echo
if grep -q "REPLACE_ME" "$ENV_FILE"; then
  echo "NEXT: edit $ENV_FILE and replace sk-ant-REPLACE_ME with your real key."
fi
echo "Test run:  $DEST/run_tracker.sh --force && tail -n 40 $DEST/logs/cron.log"
