#!/usr/bin/env python3
"""Bi-weekly 2026 midterm election tracker.

Uses Claude with the server-side web_search tool to pull the latest forecasts
and polls, then writes a dated markdown report that is diffed against the
previous run.

Outputs (under $MIDTERMS_HOME, default ~/midterms-tracker):
  reports/YYYY-MM-DD.md    human-readable report
  reports/YYYY-MM-DD.json  structured snapshot, used for the next diff
  log.md                   one line per run

The API key is read from the ANTHROPIC_API_KEY environment variable only.
It is never written to disk by this script.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

MODEL = "claude-opus-5"
MAX_CONTINUATIONS = 6  # pause_turn resumptions for long web-search loops

HOME = Path(os.environ.get("MIDTERMS_HOME", Path.home() / "midterms-tracker")).expanduser()
REPORTS = HOME / "reports"
RUN_LOG = HOME / "log.md"

# Race keys -> display info. "margin" is always Dem minus Rep, in points.
RACES = {
    "GA": {"name": "Georgia Senate", "dem": "Jon Ossoff (D-inc)", "rep": "Mike Collins (R)", "priority": 1},
    "TX": {"name": "Texas Senate", "dem": "James Talarico (D)", "rep": "Ken Paxton (R)", "priority": 1},
    "MI": {"name": "Michigan Senate (open)", "dem": "Abdul El-Sayed (D)", "rep": "Mike Rogers (R)", "priority": 2},
    "NC": {"name": "North Carolina Senate", "dem": "Roy Cooper (D)", "rep": "Michael Whatley (R)", "priority": 3},
    "ME": {"name": "Maine Senate", "dem": "Troy Jackson (D)", "rep": "Susan Collins (R-inc)", "priority": 3},
    "OH": {"name": "Ohio Senate (special)", "dem": "Sherrod Brown (D)", "rep": "Jon Husted (R-inc)", "priority": 3},
    "AK": {"name": "Alaska Senate", "dem": "Mary Peltola (D)", "rep": "Dan Sullivan (R-inc)", "priority": 3},
}

# Starting point from mid-September 2026, used as "previous" on the very first run.
BASELINE = {
    "as_of": "2026-09-15",
    "headline": {
        "house_dem_control_pct": 87.0,
        "senate_dem_control_pct": 53.5,  # midpoint of the ~50-57% range
        "generic_ballot_dem_margin": None,
    },
    "races": {},
    "new_polls": [],
}

SOURCES = (
    "Silver Bulletin, Cook Political Report, Sabato's Crystal Ball, Split Ticket, "
    "Decision Desk HQ, RealClearPolitics/RealClearPolling, 270toWin, Polymarket, Kalshi, "
    "plus pollster releases (e.g. Emerson, Quinnipiac, Marist, NYT/Siena, AJC, UT/Texas Politics Project)"
)

SYSTEM_PROMPT = """You are a careful, nonpartisan election data analyst. You track the 2026 U.S. \
midterm elections for a single reader and produce a concise, factual bi-weekly briefing.

Rules:
- Use web search to find the most recent numbers. Prefer primary sources (the forecaster's or \
pollster's own page) over news write-ups. Note each figure's source and date.
- Never invent numbers. If you cannot find a figure, use null in the JSON and say "not found" in the text.
- Distinguish model forecasts (Silver Bulletin, Split Ticket, DDHQ), expert ratings (Cook, Sabato), \
polling averages (RCP, DDHQ), and prediction markets (Polymarket, Kalshi); they are not interchangeable.
- Margins are always expressed as Democrat minus Republican in points (D+3 = 3.0, R+2 = -2.0).
- Probabilities are the Democratic side's chance, in percent (0-100).
- Only list a poll under new_polls if its field dates end after the previous report's date."""


def build_user_prompt(today: dt.date, previous: dict, prev_label: str) -> str:
    race_lines = "\n".join(
        f"- {k}: {v['name']} - {v['dem']} vs. {v['rep']}"
        + (" [TOP PRIORITY]" if v["priority"] == 1 else " [HIGH PRIORITY - new polls]" if v["priority"] == 2 else "")
        for k, v in RACES.items()
    )
    return f"""Today is {today.isoformat()}. Research the current state of the 2026 midterms.

Collect:
1. Probability Democrats win the House (model forecasts and prediction markets).
2. Probability Democrats win the Senate (model forecasts and prediction markets).
3. Generic congressional ballot average (Dem minus Rep).
4. For each race below: latest polling average margin, forecast win probability for the Democrat \
(if a model publishes one), Cook/Sabato rating, and any polls released since {previous.get('as_of', prev_label)}.
{race_lines}

Spend most of your searching on Georgia (Ossoff) and Texas (Talarico), then Michigan (El-Sayed).
Preferred sources: {SOURCES}.

The previous snapshot ({prev_label}) was:
```json
{json.dumps(previous, indent=2)}
```

Write your answer in exactly two parts.

PART 1 - a markdown briefing (no top-level title; start at "##") with these sections:
## Bottom line
(2-4 sentences: where House and Senate control stand and the single most important change.)
## What moved since {prev_label}
(Bullets. Only real changes: forecast shifts, rating changes, new polls that moved averages. \
Say "No meaningful change" for anything flat. Explain *why* it moved if a source says.)
## Georgia: Ossoff vs. Collins
## Texas: Talarico vs. Paxton
## New polls: Ossoff / Talarico / El-Sayed
(Table: race | pollster | field dates | sample (LV/RV, n) | D % | R % | margin. Only polls newer than the previous snapshot.)
## Other Senate races
(One or two lines each for NC, ME, OH, AK, MI.)
## Sources
(Bulleted links you actually used, each with the date of the figure.)

PART 2 - a single fenced ```json block with this exact shape (numbers or null):
{{
  "as_of": "{today.isoformat()}",
  "headline": {{
    "house_dem_control_pct": number|null,
    "house_sources": {{"<source name>": number}},
    "senate_dem_control_pct": number|null,
    "senate_sources": {{"<source name>": number}},
    "generic_ballot_dem_margin": number|null,
    "generic_ballot_source": string|null
  }},
  "races": {{
    "<GA|TX|MI|NC|ME|OH|AK>": {{
      "poll_avg_margin": number|null,
      "poll_avg_source": string|null,
      "dem_win_pct": number|null,
      "dem_win_source": string|null,
      "cook_rating": string|null,
      "sabato_rating": string|null
    }}
  }},
  "new_polls": [
    {{"race": "GA", "pollster": string, "end_date": "YYYY-MM-DD", "population": "LV|RV|A",
      "n": number|null, "dem_pct": number|null, "rep_pct": number|null, "margin": number|null, "url": string|null}}
  ],
  "one_line_summary": "<= 200 chars, e.g. 'House D 85% (-2), Senate D 51% (-3); Ossoff +4, Talarico -3; 2 new GA polls'"
}}
For house_dem_control_pct / senate_dem_control_pct use your best consensus figure (a simple \
average of the model forecasts you found; state which in house_sources/senate_sources)."""


# ---------------------------------------------------------------- API call


def call_claude(user_prompt: str) -> tuple[str, dict]:
    """Run the web-search research loop and return (final text, usage summary)."""
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY is not set. Put `export ANTHROPIC_API_KEY=...` in "
            "~/.midterms-tracker.env (chmod 600) or export it in your shell."
        )

    client = anthropic.Anthropic(max_retries=4, timeout=900.0)
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 25}]
    messages: list[dict] = [{"role": "user", "content": user_prompt}]
    usage = {"input_tokens": 0, "output_tokens": 0, "web_searches": 0}

    for attempt in range(MAX_CONTINUATIONS + 1):
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=32000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            tools=tools,
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # re-run on a fallback model if a safety classifier declines
        ) as stream:
            response = stream.get_final_message()

        usage["input_tokens"] += response.usage.input_tokens
        usage["output_tokens"] += response.usage.output_tokens
        stu = getattr(response.usage, "server_tool_use", None)
        if stu is not None:
            usage["web_searches"] += getattr(stu, "web_search_requests", 0) or 0

        if response.stop_reason == "pause_turn":
            # Server-side search loop hit its iteration cap; resend to resume.
            # Consecutive assistant turns are merged by the API.
            messages.append({"role": "assistant", "content": response.content})
            continue
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Model declined the request: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            print("warning: hit max_tokens; report may be truncated", file=sys.stderr)
        break
    else:
        raise RuntimeError("Exceeded pause_turn continuations without finishing")

    # Collect text from every turn (paused turns can contain early prose).
    text_parts = []
    for msg in messages[1:]:
        text_parts += [b.text for b in msg["content"] if getattr(b, "type", None) == "text"]
    text_parts += [b.text for b in response.content if b.type == "text"]
    usage["request_id"] = getattr(response, "_request_id", None)
    return "".join(text_parts), usage


# ---------------------------------------------------------------- parsing & diff

JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def split_response(text: str) -> tuple[str, dict]:
    """Return (markdown briefing, parsed JSON snapshot) from the model's answer."""
    matches = list(JSON_BLOCK.finditer(text))
    if not matches:
        raise ValueError("No ```json block found in model output")
    last = matches[-1]
    data = json.loads(last.group(1))
    briefing = text[: last.start()]
    briefing = re.sub(r"(?im)^\s*PART\s*[12].*$", "", briefing).strip()
    return briefing, data


def _num(x):
    return x if isinstance(x, (int, float)) else None


def fmt_pct(v):
    return "n/a" if v is None else f"{v:.0f}%"


def fmt_margin(v):
    if v is None:
        return "n/a"
    if abs(v) < 0.05:
        return "Tied"
    return f"D+{v:.1f}" if v > 0 else f"R+{-v:.1f}"


def fmt_delta(new, old, unit="pt", threshold=0.5):
    if new is None or old is None:
        return "new" if new is not None and old is None else "-"
    d = new - old
    if abs(d) < threshold:
        return "flat"
    arrow = "▲" if d > 0 else "▼"
    return f"{arrow} {abs(d):.1f}{unit} {'toward D' if d > 0 else 'toward R'}"


def diff_snapshots(new: dict, old: dict) -> tuple[str, list[str]]:
    """Deterministic change table (does not rely on the model) + short change notes."""
    nh, oh = new.get("headline", {}), old.get("headline", {})
    rows = [
        "| Metric | Now | Previous | Change |",
        "|---|---|---|---|",
    ]
    notes: list[str] = []

    for label, key, fmt, unit in [
        ("House: P(Dem control)", "house_dem_control_pct", fmt_pct, "pt"),
        ("Senate: P(Dem control)", "senate_dem_control_pct", fmt_pct, "pt"),
        ("Generic ballot", "generic_ballot_dem_margin", fmt_margin, "pt"),
    ]:
        n, o = _num(nh.get(key)), _num(oh.get(key))
        delta = fmt_delta(n, o, unit, threshold=1.0 if unit == "pt" and "pct" in key else 0.5)
        rows.append(f"| {label} | {fmt(n)} | {fmt(o)} | {delta} |")
        if delta not in ("flat", "-", "new"):
            notes.append(f"{label.split(':')[0]} {delta.split(' toward')[0]}")

    rows += ["", "| Race | Poll avg | Prev | Change | P(Dem win) | Prev | Ratings (Cook / Sabato) |", "|---|---|---|---|---|---|---|"]
    nr, orc = new.get("races", {}), old.get("races", {})
    for key, info in sorted(RACES.items(), key=lambda kv: kv[1]["priority"]):
        r, p = nr.get(key, {}) or {}, orc.get(key, {}) or {}
        m, pm = _num(r.get("poll_avg_margin")), _num(p.get("poll_avg_margin"))
        w, pw = _num(r.get("dem_win_pct")), _num(p.get("dem_win_pct"))
        ratings = f"{r.get('cook_rating') or 'n/a'} / {r.get('sabato_rating') or 'n/a'}"
        for rk in ("cook_rating", "sabato_rating"):
            if p.get(rk) and r.get(rk) and p[rk] != r[rk]:
                ratings += f" ({rk.split('_')[0].title()} was {p[rk]})"
                notes.append(f"{key} {rk.split('_')[0].title()} {p[rk]}→{r[rk]}")
        name = f"**{info['name']}**" if info["priority"] == 1 else info["name"]
        d = fmt_delta(m, pm)
        rows.append(f"| {name} | {fmt_margin(m)} | {fmt_margin(pm)} | {d} | {fmt_pct(w)} | {fmt_pct(pw)} | {ratings} |")
        if d not in ("flat", "-", "new") and info["priority"] <= 2:
            notes.append(f"{key} {d.split(' toward')[0]}")

    return "\n".join(rows), notes


def new_polls_only(new: dict, old: dict) -> list[dict]:
    """Drop polls that already appeared in the previous snapshot."""
    seen = {(p.get("race"), p.get("pollster"), p.get("end_date")) for p in old.get("new_polls", [])}
    return [p for p in new.get("new_polls", []) if (p.get("race"), p.get("pollster"), p.get("end_date")) not in seen]


# ---------------------------------------------------------------- files


def latest_previous(today: dt.date) -> tuple[dict, str, Path | None]:
    """Most recent snapshot strictly before today, else the built-in baseline."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    snaps = sorted(p for p in REPORTS.glob("????-??-??.json") if p.stem < today.isoformat())
    if snaps:
        return json.loads(snaps[-1].read_text()), snaps[-1].stem, snaps[-1]
    return BASELINE, f"mid-Sept baseline ({BASELINE['as_of']})", None


def render_report(today: dt.date, briefing: str, data: dict, previous: dict, prev_label: str, prev_path, usage: dict) -> str:
    table, _ = diff_snapshots(data, previous)
    h = data.get("headline", {})
    polls = new_polls_only(data, previous)
    focus = [p for p in polls if p.get("race") in ("GA", "TX", "MI")]
    prev_link = f"[{prev_label}]({prev_path.name.replace('.json', '.md')})" if prev_path else prev_label

    lines = [
        f"# Midterms tracker: {today:%A, %B %-d, %Y}",
        "",
        f"**House D:** {fmt_pct(_num(h.get('house_dem_control_pct')))} · "
        f"**Senate D:** {fmt_pct(_num(h.get('senate_dem_control_pct')))} · "
        f"**Generic ballot:** {fmt_margin(_num(h.get('generic_ballot_dem_margin')))} · "
        f"New GA/TX/MI polls: {len(focus)}",
        "",
        f"> {data.get('one_line_summary', '').strip()}",
        "",
        f"## Change table (vs. {prev_link})",
        "",
        table,
        "",
        "_Margins are Dem minus Rep. Computed by the script from the JSON snapshots, not by the model._",
        "",
        briefing,
        "",
        "---",
        f"<sub>Generated {dt.datetime.now():%Y-%m-%d %H:%M} · model {MODEL} · "
        f"{usage.get('web_searches', '?')} web searches · "
        f"{usage.get('input_tokens', 0):,} in / {usage.get('output_tokens', 0):,} out tokens · "
        f"request {usage.get('request_id') or 'n/a'}</sub>",
        "",
    ]
    return "\n".join(lines)


def log_line(today: dt.date, data: dict, previous: dict) -> str:
    _, notes = diff_snapshots(data, previous)
    h = data.get("headline", {})
    summary = (data.get("one_line_summary") or "").replace("\n", " ").strip()
    changes = "; ".join(notes) if notes else "no major moves"
    return (
        f"- {today.isoformat()} | House D {fmt_pct(_num(h.get('house_dem_control_pct')))} | "
        f"Senate D {fmt_pct(_num(h.get('senate_dem_control_pct')))} | "
        f"GB {fmt_margin(_num(h.get('generic_ballot_dem_margin')))} | {changes} | {summary}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", help="Override report date (YYYY-MM-DD); default today")
    ap.add_argument("--dry-run", action="store_true", help="Print the prompt and exit without calling the API")
    ap.add_argument("--from-file", help="Skip the API and parse a saved model response (for testing)")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    previous, prev_label, prev_path = latest_previous(today)
    prompt = build_user_prompt(today, previous, prev_label)

    if args.dry_run:
        print(SYSTEM_PROMPT, "\n\n", prompt)
        return 0

    if args.from_file:
        text, usage = Path(args.from_file).read_text(), {"web_searches": 0}
    else:
        print(f"[{dt.datetime.now():%H:%M:%S}] Researching (comparing against {prev_label})...", flush=True)
        text, usage = call_claude(prompt)

    stem = today.isoformat()
    try:
        briefing, data = split_response(text)
    except (ValueError, json.JSONDecodeError) as e:
        raw = REPORTS / f"{stem}.raw.txt"
        raw.write_text(text)
        print(f"error: could not parse model output ({e}); raw text saved to {raw}", file=sys.stderr)
        return 2

    data.setdefault("as_of", stem)
    (REPORTS / f"{stem}.json").write_text(json.dumps(data, indent=2) + "\n")
    md_path = REPORTS / f"{stem}.md"
    md_path.write_text(render_report(today, briefing, data, previous, prev_label, prev_path, usage))

    line = log_line(today, data, previous)
    if not RUN_LOG.exists():
        RUN_LOG.write_text("# Midterms tracker run log\n\n")
    with RUN_LOG.open("a") as f:
        f.write(line + "\n")

    print(f"Report: {md_path}")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
