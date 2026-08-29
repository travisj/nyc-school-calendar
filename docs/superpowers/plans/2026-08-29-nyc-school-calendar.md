# NYC School Calendar 2026–27 (ICS + HTML) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate `nyc-school-calendar-2026-27.ics` (36 all-day events, one combined calendar) and `index.html` (browsable month-grid view) from a reviewed, assertion-checked event table of the official NYCPS 2026–27 calendar.

**Architecture:** One stdlib-only Python script (`generate.py`) holds the event table and two pure emitters (`emit_ics`, `emit_html`) plus a `validate()` gate; `main()` validates then writes both artifacts. Tests live in `test_generate.py` (stdlib `unittest`; pytest is NOT installed).

**Tech Stack:** Python 3.13 stdlib only (`dataclasses`, `datetime`, `calendar`, `html`). No third-party deps.

**Spec:** `docs/superpowers/specs/2026-08-29-nyc-school-calendar-design.md` — the event table there is the source of truth; the `EVENTS` list below is that table verbatim.

## Global Constraints

- Python stdlib only; no pip installs, no pytest (`python3 -m unittest`).
- 35 PDF rows → exactly 36 `Event` rows (Regents Jun 15–18 and Jun 21–25 are two events).
- All events all-day: `DTSTART;VALUE=DATE`, `DTEND` exclusive (last day + 1).
- ICS: CRLF line endings, lines folded ≤ 75 octets (UTF-8 aware), RFC 5545 §3.3.11 escaping, stable content-derived UIDs `<slug>@nycps.harness`.
- Categories exactly: `Schools Closed`, `Parent-Teacher Conferences`, `Regents`, `Key Dates`.
- HTML: single file, inline CSS, ~10-line vanilla JS filter, no external assets.
- En dashes (`–`) and em dashes (`—`) are part of the data copy; keep them verbatim.

---

### Task 1: Event data model, event table, validation

**Files:**
- Create: `generate.py`
- Create: `test_generate.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces (later tasks import these exact names):
  - `Event` dataclass: fields `start: date`, `end: date`, `weekdays: tuple[str, str]`, `summary: str`, `category: str`, `description: str = ""`
  - `EVENTS: list[Event]` (36 rows, chronological)
  - `validate(events: list[Event]) -> None` (raises `AssertionError` on any inconsistency)
  - Category constants: `SCHOOLS_CLOSED, PTC, REGENTS, KEY_DATES`, tuple `CATEGORIES`
  - `ICS_PATH: Path = Path("nyc-school-calendar-2026-27.ics")`, `HTML_PATH: Path = Path("index.html")`

- [ ] **Step 1: Write the failing tests**

Create `test_generate.py`:

```python
import unittest
from datetime import date

from generate import CATEGORIES, EVENTS, KEY_DATES, PTC, REGENTS, SCHOOLS_CLOSED, validate


class TestData(unittest.TestCase):
    def test_validate_passes(self):
        validate(EVENTS)  # raises on any inconsistency

    def test_exactly_36_events(self):
        self.assertEqual(len(EVENTS), 36)

    def test_all_four_categories_used(self):
        self.assertEqual({e.category for e in EVENTS}, set(CATEGORIES))

    def test_chronological_and_contiguous_weekdays(self):
        self.assertEqual(
            [e.start for e in EVENTS], sorted(e.start for e in EVENTS)
        )
        self.assertEqual(EVENTS[0].summary, "First Day of School")
        self.assertEqual(EVENTS[-1].summary, "Last Day of School for Students")

    def test_known_anchor_dates(self):
        by_summary = {e.summary: e for e in EVENTS}
        self.assertEqual(by_summary["First Day of School"].start, date(2026, 9, 10))
        self.assertEqual(
            by_summary["Winter Recess — Schools Closed"].start, date(2026, 12, 24)
        )
        self.assertEqual(
            by_summary["Winter Recess — Schools Closed"].end, date(2027, 1, 1)
        )
        self.assertEqual(
            by_summary["Eid al-Fitr — Schools Closed"].start, date(2027, 3, 9)
        )
        self.assertEqual(
            by_summary["Last Day of School for Students"].start, date(2027, 6, 28)
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_generate -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate'`

- [ ] **Step 3: Write the implementation**

Create `generate.py` with the module header, constants, `Event`, the full `EVENTS` table, and `validate`:

```python
#!/usr/bin/env python3
"""Generate the NYC Public Schools 2026-27 calendar as .ics + browsable HTML.

Data source (reviewed, see docs/superpowers/specs/):
https://www.schools.nyc.gov/docs/default-source/sections/calendar/2026-27-school-year-calendar.pdf
Run: python3 generate.py
"""

from __future__ import annotations

import calendar as cal_mod
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ICS_PATH = Path("nyc-school-calendar-2026-27.ics")
HTML_PATH = Path("index.html")
SOURCE_PDF = (
    "https://www.schools.nyc.gov/docs/default-source/sections/calendar/"
    "2026-27-school-year-calendar.pdf"
)

SCHOOLS_CLOSED = "Schools Closed"
PTC = "Parent-Teacher Conferences"
REGENTS = "Regents"
KEY_DATES = "Key Dates"
CATEGORIES = (SCHOOLS_CLOSED, PTC, REGENTS, KEY_DATES)

WEEKDAYS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

PTC_NOTE = "Individual schools' conference dates may differ."
EARLY_NOTE = (
    "Students in these schools dismissed three hours early. " + PTC_NOTE
)


@dataclass(frozen=True)
class Event:
    start: date
    end: date  # inclusive last day
    weekdays: tuple[str, str]  # PDF-stated weekday of start and end
    summary: str
    category: str
    description: str = ""


def E(y1, m1, d1, y2, m2, d2, wd, summary, category, description=""):
    return Event(date(y1, m1, d1), date(y2, m2, d2), wd, summary, category, description)


EVENTS = [
    E(2026, 9, 10, 2026, 9, 10, ("Thu", "Thu"), "First Day of School", KEY_DATES),
    E(2026, 9, 21, 2026, 9, 21, ("Mon", "Mon"), "Yom Kippur — Schools Closed", SCHOOLS_CLOSED),
    E(2026, 9, 23, 2026, 9, 23, ("Wed", "Wed"), "Evening Parent-Teacher Conferences: Middle Schools & D75", PTC, PTC_NOTE),
    E(2026, 9, 24, 2026, 9, 24, ("Thu", "Thu"), "Evening Parent-Teacher Conferences: High Schools, K–12, 6–12", PTC, PTC_NOTE),
    E(2026, 9, 30, 2026, 9, 30, ("Wed", "Wed"), "Evening Parent-Teacher Conferences: Elementary Schools & Pre-K Centers", PTC, PTC_NOTE),
    E(2026, 10, 12, 2026, 10, 12, ("Mon", "Mon"), "Italian Heritage/Indigenous Peoples' Day — Schools Closed", SCHOOLS_CLOSED),
    E(2026, 11, 3, 2026, 11, 3, ("Tue", "Tue"), "Election Day — Remote Instruction for All Students", KEY_DATES),
    E(2026, 11, 5, 2026, 11, 5, ("Thu", "Thu"), "Afternoon & Evening Parent-Teacher Conferences: Elementary Schools & Pre-K Centers", PTC, EARLY_NOTE),
    E(2026, 11, 11, 2026, 11, 11, ("Wed", "Wed"), "Veterans Day — Schools Closed", SCHOOLS_CLOSED),
    E(2026, 11, 12, 2026, 11, 12, ("Thu", "Thu"), "Afternoon & Evening Parent-Teacher Conferences: Middle Schools & D75", PTC, EARLY_NOTE),
    E(2026, 11, 19, 2026, 11, 19, ("Thu", "Thu"), "Evening Parent-Teacher Conferences: High Schools, K–12, 6–12", PTC, PTC_NOTE),
    E(2026, 11, 20, 2026, 11, 20, ("Fri", "Fri"), "Afternoon Parent-Teacher Conferences: High Schools, K–12, 6–12", PTC, EARLY_NOTE),
    E(2026, 11, 26, 2026, 11, 27, ("Thu", "Fri"), "Thanksgiving Recess — Schools Closed", SCHOOLS_CLOSED),
    E(2026, 12, 24, 2027, 1, 1, ("Thu", "Fri"), "Winter Recess — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 1, 18, 2027, 1, 18, ("Mon", "Mon"), "Rev. Dr. Martin Luther King Jr. Day — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 1, 26, 2027, 1, 29, ("Tue", "Fri"), "Regents Administration", REGENTS),
    E(2027, 2, 1, 2027, 2, 1, ("Mon", "Mon"), "Professional Development Day", KEY_DATES, "Students that attend high schools and schools that serve only grades 6–12 are not in attendance. All other students attend school."),
    E(2027, 2, 2, 2027, 2, 2, ("Tue", "Tue"), "Spring Semester Begins", KEY_DATES),
    E(2027, 2, 15, 2027, 2, 19, ("Mon", "Fri"), "Midwinter Recess — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 3, 3, 2027, 3, 3, ("Wed", "Wed"), "Afternoon & Evening Parent-Teacher Conferences: Elementary Schools & Pre-K Centers", PTC, EARLY_NOTE),
    E(2027, 3, 4, 2027, 3, 4, ("Thu", "Thu"), "Afternoon & Evening Parent-Teacher Conferences: Middle Schools & D75", PTC, EARLY_NOTE),
    E(2027, 3, 9, 2027, 3, 9, ("Tue", "Tue"), "Eid al-Fitr — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 3, 18, 2027, 3, 18, ("Thu", "Thu"), "Evening Parent-Teacher Conferences: High Schools, K–12, 6–12", PTC, PTC_NOTE),
    E(2027, 3, 19, 2027, 3, 19, ("Fri", "Fri"), "Afternoon Parent-Teacher Conferences: High Schools, K–12, 6–12", PTC, EARLY_NOTE),
    E(2027, 3, 26, 2027, 3, 26, ("Fri", "Fri"), "Good Friday — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 4, 22, 2027, 4, 30, ("Thu", "Fri"), "Spring Recess — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 5, 12, 2027, 5, 12, ("Wed", "Wed"), "Evening Parent-Teacher Conferences: High Schools, K–12, 6–12", PTC, PTC_NOTE),
    E(2027, 5, 13, 2027, 5, 13, ("Thu", "Thu"), "Evening Parent-Teacher Conferences: Middle Schools & D75", PTC, PTC_NOTE),
    E(2027, 5, 17, 2027, 5, 17, ("Mon", "Mon"), "Eid al-Adha — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 5, 26, 2027, 5, 26, ("Wed", "Wed"), "Evening Parent-Teacher Conferences: Elementary Schools & Pre-K Centers", PTC, PTC_NOTE),
    E(2027, 5, 31, 2027, 5, 31, ("Mon", "Mon"), "Memorial Day — Schools Closed", SCHOOLS_CLOSED),
    E(2027, 6, 8, 2027, 6, 8, ("Tue", "Tue"), "Clerical Day", KEY_DATES, "No classes for students attending 3-K, Pre-K, elementary schools, middle schools, K–12 schools, and standalone D75 programs."),
    E(2027, 6, 10, 2027, 6, 10, ("Thu", "Thu"), "Anniversary Day / Chancellor's Conference Day", KEY_DATES, "Students do not attend school."),
    E(2027, 6, 15, 2027, 6, 18, ("Tue", "Fri"), "Regents Administration", REGENTS),
    E(2027, 6, 21, 2027, 6, 25, ("Mon", "Fri"), "Regents Administration", REGENTS),
    E(2027, 6, 28, 2027, 6, 28, ("Mon", "Mon"), "Last Day of School for Students", KEY_DATES),
]


def validate(events: list[Event]) -> None:
    """Cross-check the table against itself and the PDF's stated facts."""
    assert len(events) == 36, f"expected 36 events, got {len(events)}"
    prev_start = None
    for ev in events:
        assert ev.category in CATEGORIES, ev
        assert ev.start <= ev.end, ev
        lo, hi = ev.weekdays
        assert lo in WEEKDAYS and hi in WEEKDAYS, ev
        assert ev.start.weekday() == WEEKDAYS[lo], f"{ev.start} is not {lo}"
        assert ev.end.weekday() == WEEKDAYS[hi], f"{ev.end} is not {hi}"
        if prev_start is not None:
            assert ev.start >= prev_start, f"out of order: {ev}"
        prev_start = ev.start
    by_summary = {ev.summary: ev for ev in events}
    # Semantic anchors from the PDF (catch event<->date misalignment):
    assert by_summary["Good Friday — Schools Closed"].start.weekday() == WEEKDAYS["Fri"]
    assert by_summary["Memorial Day — Schools Closed"].start.weekday() == WEEKDAYS["Mon"]
    assert (
        by_summary["Rev. Dr. Martin Luther King Jr. Day — Schools Closed"]
        .start.weekday()
        == WEEKDAYS["Mon"]
    )
    assert by_summary["Thanksgiving Recess — Schools Closed"].weekdays == ("Thu", "Fri")
    assert events[-1].end == max(ev.end for ev in events)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_generate -v`
Expected: `Ran 5 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add generate.py test_generate.py
git commit -m "feat: event table for NYCPS 2026-27 with validation"
```

---

### Task 2: ICS emitter

**Files:**
- Modify: `generate.py` (append emitter after `validate`)
- Modify: `test_generate.py` (append `TestIcs` class)

**Interfaces:**
- Consumes: `Event`, `EVENTS` from Task 1.
- Produces: `emit_ics(events: list[Event], now: datetime) -> str` — full VCALENDAR text with CRLF endings; internal helpers `_fold(line: str) -> list[str]`, `_escape(text: str) -> str`, `_slug(ev: Event) -> str`.

- [ ] **Step 1: Write the failing tests**

Append to `test_generate.py` (add `datetime` to the datetime import; add `emit_ics` to the generate import):

```python
from datetime import date, datetime
from generate import CATEGORIES, EVENTS, KEY_DATES, PTC, REGENTS, SCHOOLS_CLOSED, emit_ics, validate


class TestIcs(unittest.TestCase):
    def setUp(self):
        self.ics = emit_ics(EVENTS, datetime(2026, 8, 29, 12, 0, 0))

    def test_crlf_endings_and_trailing_break(self):
        self.assertTrue(self.ics.endswith("\r\n"))
        self.assertNotIn("\n", self.ics.replace("\r\n", ""))

    def test_lines_folded_to_75_octets(self):
        for line in self.ics.split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75, line)

    def test_header_properties(self):
        for expected in [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//nyc-school-calendar//NYCPS 2026-27//EN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:NYC Public Schools 2026–27",
            "X-WR-TIMEZONE:America/New_York",
        ]:
            self.assertIn(expected, self.ics)

    def test_36_events_with_required_fields(self):
        self.assertEqual(self.ics.count("BEGIN:VEVENT"), 36)
        self.assertEqual(self.ics.count("END:VEVENT"), 36)
        for line in self.ics.split("\r\n"):
            if line.startswith("UID:"):
                self.assertRegex(line, r"UID:.+@nycps\.harness")
            if line.startswith("DTSTART"):
                self.assertIn("VALUE=DATE:", line)

    def test_dtend_is_exclusive_for_ranges(self):
        self.assertIn("DTSTART;VALUE=DATE:20261224", self.ics)
        self.assertIn("DTEND;VALUE=DATE:20270102", self.ics)  # Jan 1 + 1 day
        self.assertIn("DTSTART;VALUE=DATE:20261126", self.ics)
        self.assertIn("DTEND;VALUE=DATE:20261128", self.ics)  # Nov 27 + 1 day

    def test_commas_and_semicolons_escaped(self):
        self.assertIn(
            "SUMMARY:Evening Parent-Teacher Conferences: High Schools\\, K–12\\, 6–12",
            self.ics,
        )

    def test_uids_stable_and_unique(self):
        uids = [l for l in self.ics.split("\r\n") if l.startswith("UID:")]
        self.assertEqual(len(uids), len(set(uids)))
        self.assertEqual(
            emit_ics(EVENTS, datetime(2026, 8, 29, 12, 0, 0)), self.ics
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_generate.TestIcs -v`
Expected: FAIL — `ImportError: cannot import name 'emit_ics'`

- [ ] **Step 3: Write the implementation**

Append to `generate.py`:

```python
def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> list[str]:
    """RFC 5545 §3.1 folding: content lines are at most 75 octets, UTF-8 aware."""
    folded: list[str] = []
    cur = ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > 75:
            folded.append(cur)
            cur = " " + ch
        else:
            cur += ch
    folded.append(cur)
    return folded


def _slug(ev: Event) -> str:
    text = f"{ev.start:%b%d}-{ev.end:%b%d}-{ev.summary}".lower()
    parts = "".join(c if c.isalnum() else "-" for c in text).split("-")
    return "-".join(p for p in parts if p)


def emit_ics(events: list[Event], now: datetime) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//nyc-school-calendar//NYCPS 2026-27//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:NYC Public Schools 2026–27",
        "X-WR-TIMEZONE:America/New_York",
    ]
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for ev in events:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{_slug(ev)}@nycps.harness",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{ev.start:%Y%m%d}",
            f"DTEND;VALUE=DATE:{ev.end + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{_escape(ev.summary)}",
        ]
        if ev.description:
            lines.append(f"DESCRIPTION:{_escape(ev.description)}")
        lines += [f"CATEGORIES:{_escape(ev.category)}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    out: list[str] = []
    for line in lines:
        out.extend(_fold(line))
    return "\r\n".join(out) + "\r\n"
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `python3 -m unittest test_generate -v`
Expected: `Ran 12 tests ... OK` (5 from Task 1 + 7 new)

- [ ] **Step 5: Commit**

```bash
git add generate.py test_generate.py
git commit -m "feat: RFC 5545 ICS emitter with folding/escaping"
```

---

### Task 3: HTML emitter

**Files:**
- Modify: `generate.py` (append constants + emitter)
- Modify: `test_generate.py` (append `TestHtml` class)

**Interfaces:**
- Consumes: `Event`, `EVENTS`, category constants from Task 1.
- Produces: `emit_html(events: list[Event]) -> str` — complete HTML document; module constants `CAT_SLUGS: dict[str, str]`, `CAT_COLORS: dict[str, str]`, `HTML_HEAD: str`, `HTML_TAIL: str`.

- [ ] **Step 1: Write the failing tests**

Append to `test_generate.py`. Update the top-of-file imports to exactly:

```python
import html as html_mod
from generate import (
    CATEGORIES, CAT_SLUGS, EVENTS, KEY_DATES, PTC, REGENTS, SOURCE_PDF,
    SCHOOLS_CLOSED, emit_ics, emit_html, validate,
)
```

Then append the test class:

```python


class TestHtml(unittest.TestCase):
    def setUp(self):
        self.html = emit_html(EVENTS)

    def test_all_ten_months_rendered(self):
        for label in [
            "September 2026", "October 2026", "November 2026", "December 2026",
            "January 2027", "February 2027", "March 2027", "April 2027",
            "May 2027", "June 2027",
        ]:
            self.assertIn(label, self.html)

    def test_every_event_appears(self):
        for ev in EVENTS:
            self.assertIn(html_mod.escape(ev.summary), self.html)

    def test_legend_lists_all_categories_with_toggles(self):
        for cat in CATEGORIES:
            self.assertIn(cat, self.html)
            slug = CAT_SLUGS[cat]
            self.assertIn(f'value="{slug}"', self.html)
            self.assertIn(f"cat-{slug}", self.html)
        self.assertIn("cat-toggle", self.html)

    def test_download_and_source_links(self):
        self.assertIn('href="nyc-school-calendar-2026-27.ics"', self.html)
        self.assertIn(SOURCE_PDF, self.html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_generate.TestHtml -v`
Expected: FAIL — `ImportError: cannot import name 'emit_html'`

- [ ] **Step 3: Write the implementation**

Append to `generate.py`:

```python
CAT_SLUGS = {
    SCHOOLS_CLOSED: "schools-closed",
    PTC: "ptc",
    REGENTS: "regents",
    KEY_DATES: "key-dates",
}
CAT_COLORS = {
    SCHOOLS_CLOSED: "#b91c1c",
    PTC: "#1d4ed8",
    REGENTS: "#6d28d9",
    KEY_DATES: "#047857",
}
DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

HTML_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NYC Public Schools 2026–27 Calendar</title>
<style>
:root { --closed:#b91c1c; --ptc:#1d4ed8; --regents:#6d28d9; --key:#047857; }
body { font-family:-apple-system,"Segoe UI",sans-serif; margin:1.5rem; color:#111; background:#fafafa; }
header h1 { font-size:1.4rem; margin:0 0 .25rem; }
header p { margin:.1rem 0 .6rem; font-size:.85rem; }
.legend { display:flex; flex-wrap:wrap; gap:1rem; margin:.4rem 0 1.25rem; }
.legend-item { display:flex; align-items:center; gap:.35rem; cursor:pointer; font-size:.85rem; }
.dot { width:.8rem; height:.8rem; border-radius:50%; display:inline-block; }
.months { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:1.25rem; }
.month { background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:.75rem; }
.month h2 { font-size:1rem; margin:.1rem 0 .5rem; }
table { width:100%; border-collapse:collapse; table-layout:fixed; }
th { font-size:.65rem; color:#6b7280; padding:.15rem 0; }
td { height:52px; vertical-align:top; border:1px solid #f3f4f6; padding:1px 2px; }
td.pad { background:#fafafa; }
.daynum { font-size:.62rem; color:#9ca3af; display:block; }
.ev { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
      border-radius:3px; padding:0 2px; margin-top:1px; color:#fff; font-size:.6rem; }
.cat-schools-closed { background:var(--closed); }
.cat-ptc { background:var(--ptc); }
.cat-regents { background:var(--regents); }
.cat-key-dates { background:var(--key); }
.hide-schools-closed .cat-schools-closed, .hide-ptc .cat-ptc,
.hide-regents .cat-regents, .hide-key-dates .cat-key-dates { display:none; }
footer { margin-top:1.5rem; }
footer p { color:#6b7280; font-size:.75rem; }
</style>
</head>
<body>
"""

HTML_TAIL = """</main>
<footer><p>All events all-day per the official NYCPS calendar; individual schools' Parent-Teacher Conference dates may differ.</p></footer>
<script>
document.querySelectorAll('.cat-toggle').forEach(function (cb) {
  cb.addEventListener('change', function () {
    document.body.classList.toggle('hide-' + cb.value, !cb.checked);
  });
});
</script>
</body>
</html>
"""


def emit_html(events: list[Event]) -> str:
    by_date: dict[date, list[Event]] = {}
    for ev in events:
        d = ev.start
        while d <= ev.end:
            by_date.setdefault(d, []).append(ev)
            d += timedelta(days=1)

    months: list[tuple[int, int]] = []
    year, month = 2026, 9
    while (year, month) <= (2027, 6):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)

    parts: list[str] = [HTML_HEAD]
    parts.append(
        "<header><h1>NYC Public Schools — 2026–27 Calendar</h1>"
        f'<p><a href="{ICS_PATH.name}" download>Download .ics</a> · '
        f'<a href="{SOURCE_PDF}">Source PDF (schools.nyc.gov)</a></p>'
        '<div class="legend">'
    )
    for cat in CATEGORIES:
        parts.append(
            f'<label class="legend-item"><input type="checkbox" class="cat-toggle" '
            f'value="{CAT_SLUGS[cat]}" checked> '
            f'<span class="dot" style="background:{CAT_COLORS[cat]}"></span>'
            f"{html_escape(cat)}</label>"
        )
    parts.append("</div></header><main class=\"months\">")
    for year, month in months:
        title = f"{cal_mod.month_name[month]} {year}"
        parts.append(f'<section class="month"><h2>{title}</h2><table><thead><tr>')
        for dn in DAY_NAMES:
            parts.append(f"<th>{dn}</th>")
        parts.append("</tr></thead><tbody>")
        weeks = cal_mod.Calendar(firstweekday=6).monthdayscalendar(year, month)
        for week in weeks:
            parts.append("<tr>")
            for day in week:
                if day == 0:
                    parts.append('<td class="pad"></td>')
                    continue
                evs = by_date.get(date(year, month, day), [])
                badges = "".join(
                    f'<span class="ev cat-{CAT_SLUGS[ev.category]}" '
                    f'title="{html_escape(ev.summary)}">{html_escape(ev.summary)}</span>'
                    for ev in evs
                )
                parts.append(
                    f'<td><span class="daynum">{day}</span>{badges}</td>'
                )
            parts.append("</tr>")
        parts.append("</tbody></table></section>")
    parts.append(HTML_TAIL)
    return "".join(parts)
```

Add the import next to the other stdlib imports at the top of `generate.py`:

```python
from html import escape as html_escape
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `python3 -m unittest test_generate -v`
Expected: `Ran 16 tests ... OK` (12 + 4 new)

- [ ] **Step 5: Commit**

```bash
git add generate.py test_generate.py
git commit -m "feat: static HTML month-grid view with category filter"
```

---

### Task 4: `main()`, artifact generation, end-to-end verification

**Files:**
- Modify: `generate.py` (append `main` + `__main__` guard)
- Create (generated): `nyc-school-calendar-2026-27.ics`, `index.html`

**Interfaces:**
- Consumes: `validate`, `EVENTS`, `emit_ics`, `emit_html`, `ICS_PATH`, `HTML_PATH`.
- Produces: `main() -> None`; both artifact files on disk.

- [ ] **Step 1: Write the failing test**

Append to `test_generate.py` (add `main` to the generate import; the test runs in a temp cwd so artifacts don't dirty the repo — `main` uses module-level `Path` constants, so the test monkeypatches them):

```python
import generate as gen
from pathlib import Path
from tempfile import TemporaryDirectory


class TestMain(unittest.TestCase):
    def test_main_writes_artifacts(self):
        with TemporaryDirectory() as tmp:
            ics_path = Path(tmp) / "out.ics"
            html_path = Path(tmp) / "out.html"
            old_ics, old_html = gen.ICS_PATH, gen.HTML_PATH
            gen.ICS_PATH = ics_path
            gen.HTML_PATH = html_path
            try:
                gen.main()
            finally:
                gen.ICS_PATH, gen.HTML_PATH = old_ics, old_html
            raw = ics_path.read_bytes()
            self.assertTrue(raw.endswith(b"\r\n"))
            self.assertIn(b"BEGIN:VCALENDAR", raw)
            text = html_path.read_text(encoding="utf-8")
            self.assertIn("June 2027", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest test_generate.TestMain -v`
Expected: FAIL — `AttributeError: module 'generate' has no attribute 'main'`

- [ ] **Step 3: Write the implementation**

Append to `generate.py`:

```python
def main() -> None:
    validate(EVENTS)
    now = datetime.now(timezone.utc)
    ICS_PATH.write_bytes(emit_ics(EVENTS, now).encode("utf-8"))
    HTML_PATH.write_text(emit_html(EVENTS), encoding="utf-8")
    print(f"wrote {ICS_PATH} and {HTML_PATH} ({len(EVENTS)} events)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest test_generate -v`
Expected: `Ran 17 tests ... OK`

- [ ] **Step 5: Generate the real artifacts**

Run: `python3 generate.py`
Expected stdout: `wrote nyc-school-calendar-2026-27.ics and index.html (36 events)`

- [ ] **Step 6: Parse-back check on the real file**

Run:
```bash
python3 - <<'EOF'
from generate import ICS_PATH
raw = ICS_PATH.read_bytes()
text = raw.decode("utf-8")
assert raw.endswith(b"\r\n")
assert text.count("BEGIN:VEVENT") == 36
for line in text.split("\r\n"):
    assert len(line.encode("utf-8")) <= 75, line
print("parse-back OK: 36 events, all lines <= 75 octets, CRLF")
EOF
```
Expected: `parse-back OK: 36 events, all lines <= 75 octets, CRLF`

- [ ] **Step 7: Visual verification of the HTML**

Open `index.html` in a real browser (e.g. `open index.html` or via the browser tool on the `file://` URL). Confirm: ten month grids Sep 2026–Jun 2027 render, event badges appear on the right days (Sep 10 first day; Nov 26–27 Thanksgiving; Dec 24–Jan 1 Winter Recess spanning the new year; Jun 28 last day), legend toggles hide/show categories.

- [ ] **Step 8: Commit**

```bash
git add generate.py test_generate.py nyc-school-calendar-2026-27.ics index.html
git commit -m "feat: generate ics + html artifacts for NYCPS 2026-27"
```

---

## Verification checklist (plan level)

- [ ] `python3 -m unittest test_generate -v` → 17 tests OK
- [ ] `python3 generate.py` regenerates both artifacts cleanly
- [ ] ICS: 36 VEVENTs, CRLF, ≤75 octets/line, exclusive DTENDs, escaped punctuation
- [ ] HTML renders in browser with correct badges and working category filter
- [ ] Event table matches the spec table 1:1 (36 rows)
