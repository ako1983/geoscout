# Midterms tracker (2026)

Bi-weekly research job: Claude (`claude-opus-5` + server-side `web_search`) pulls the latest
House/Senate control odds, generic ballot, and polls for GA (Ossoff), TX (Talarico), MI (El-Sayed),
NC, ME, OH, AK, then writes a dated markdown report that is diffed against the previous one.

```
~/midterms-tracker/
├── reports/2026-09-28.md     # the report you read
├── reports/2026-09-28.json   # structured snapshot used for the next diff
├── log.md                    # one line per run (running summary)
├── logs/cron.log             # every cron firing, skips, errors, tracebacks
├── tracker.py  run_tracker.sh  requirements.txt  .venv/
~/.midterms-tracker.env       # export ANTHROPIC_API_KEY=... (chmod 600, never committed)
```

## Install (macOS)

```bash
git clone -b claude/midterm-election-tracker-eb5qro https://github.com/ako1983/geoscout.git
cd geoscout/midterms-tracker && ./install.sh
open -e ~/.midterms-tracker.env        # replace sk-ant-REPLACE_ME with your key, save
crontab -l                             # confirm the entry below is present
```

Installed cron line (every Monday 07:00 local time; the wrapper skips alternate weeks):

```
0 7 * * 1 /Users/<you>/midterms-tracker/run_tracker.sh # midterms-tracker
```

Why weekly-plus-gate instead of a true "every 2 weeks" cron expression: cron has no biweekly
syntax. `run_tracker.sh` skips if the newest report is under 13 days old, so a Monday missed
while the Mac was asleep is picked up the next Monday rather than lost.

## Manual run / testing

```bash
~/midterms-tracker/run_tracker.sh --force          # full real run now (≈3-6 min, ~$0.50-1.50)
~/midterms-tracker/.venv/bin/python ~/midterms-tracker/tracker.py --dry-run   # show prompt, no API call
```

`--force` bypasses the 2-week gate. Re-running on the same day overwrites that day's report.

## Did cron fire?

```bash
tail -n 50 ~/midterms-tracker/logs/cron.log   # "run started" / "skip: ... Off-week" / "run finished rc=0"
cat ~/midterms-tracker/log.md                 # one line per successful report
ls -lt ~/midterms-tracker/reports | head
log show --last 1d --predicate 'process == "cron"'   # macOS system log of cron launching jobs
```

Every firing writes a `run started` line, including off-weeks, so an empty log on a Monday means
cron itself didn't run (Mac asleep or off).

## macOS caveats

- **Sleep:** cron does not run while the Mac is asleep and does not catch up afterwards. To
  wake the machine for it: `sudo pmset repeat wakeorpoweron M 06:55:00`.
- **Full Disk Access:** not needed, because everything lives in `~/midterms-tracker`. If you move it
  under `~/Documents` or `~/Desktop`, grant `/usr/sbin/cron` Full Disk Access in System Settings →
  Privacy & Security.
- **Python:** needs 3.10+. `install.sh` looks for one; if it can't find one, run `brew install python@3.12`.

## Uninstall

```bash
crontab -l | grep -v '# midterms-tracker' | crontab -
rm -rf ~/midterms-tracker ~/.midterms-tracker.env
```
