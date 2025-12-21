import unittest
from datetime import datetime
import sys
import os
import json

# Add scripts to path
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
from event_flags import get_event_context

class TestEventFlags(unittest.TestCase):

    def test_opex_detection(self):
        # Dec 19, 2025 is the 3rd Friday
        context = get_event_context("2025-12-19")
        self.assertIn("MONTHLY_OPEX", context["flags_today"])
        self.assertIn("TRIPLE_WITCHING", context["flags_today"])

    def test_month_end_detection(self):
        # Dec 31, 2025 is Wednesday (Last weekday of month)
        context = get_event_context("2025-12-31")
        self.assertIn("MONTH_END", context["flags_today"])
        self.assertIn("QUARTER_END", context["flags_today"])

    def test_lookback_7days(self):
        # Mon Dec 22, 2025. Lookback should find OPEX from Friday Dec 19.
        context = get_event_context("2025-12-22", lookback_days=7)
        self.assertIn("MONTHLY_OPEX", context["flags_recent"])
        self.assertIn("TRIPLE_WITCHING", context["flags_recent"])

    def test_normalization(self):
        # We know 2025-12-17 is FOMC in our mock calendar
        context = get_event_context("2025-12-17")
        self.assertIn("FOMC", context["flags_today"])
        
        # Test Recent FOMC
        context = get_event_context("2025-12-18")
        self.assertIn("FOMC", context["flags_recent"])

if __name__ == '__main__':
    unittest.main()
