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
