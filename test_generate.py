import unittest
import html as html_mod
from datetime import date, datetime

from generate import (
    CATEGORIES, CAT_SLUGS, EVENTS, KEY_DATES, PTC, REGENTS, SOURCE_PDF,
    SCHOOLS_CLOSED, emit_ics, emit_html, main, validate,
)


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




class TestIcs(unittest.TestCase):
    def setUp(self):
        self.ics = emit_ics(EVENTS, datetime(2026, 8, 29, 12, 0, 0))
        # Logical lines (RFC 5545 §3.1 folds joined; used by tests that assert
        # on content lines like UID: whose tail would otherwise be on a
        # continuation physical line starting with " ").
        text = self.ics.replace("\r\n", "\n")
        out: list[str] = []
        for line in text.split("\n"):
            if line.startswith(" ") and out:
                out[-1] += line[1:]
            else:
                out.append(line)
        self.unfolded = "\n".join(out)

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
        for line in self.unfolded.split("\n"):
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
        full_uids = [
            line[len("UID:"):]
            for line in self.unfolded.split("\n")
            if line.startswith("UID:")
        ]
        self.assertEqual(len(full_uids), 36)
        self.assertEqual(len(full_uids), len(set(full_uids)))
        # Determinism — same now gives same full ICS
        self.assertEqual(
            emit_ics(EVENTS, datetime(2026, 8, 29, 12, 0, 0)), self.ics
        )
        # UID is independent of `now`
        other = emit_ics(EVENTS, datetime(2027, 1, 1))
        other_lines: list[str] = []
        for line in other.replace("\r\n", "\n").split("\n"):
            if line.startswith(" ") and other_lines:
                other_lines[-1] += line[1:]
            else:
                other_lines.append(line)
        other_uids = [
            line[len("UID:"):]
            for line in other_lines
            if line.startswith("UID:")
        ]
        self.assertEqual(set(other_uids), set(full_uids))


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


class TestMain(unittest.TestCase):
    def test_main_writes_artifacts(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        import generate as gen
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
if __name__ == "__main__":
     unittest.main()
