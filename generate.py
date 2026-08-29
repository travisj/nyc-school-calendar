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
from html import escape as html_escape
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
