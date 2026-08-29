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
