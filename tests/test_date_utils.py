import unittest
from datetime import date, datetime, timezone

from date_utils import current_app_date, resolve_friday_date


class DateUtilsTest(unittest.TestCase):
    def test_current_app_date_uses_shanghai_timezone(self):
        utc_now = datetime(2026, 6, 26, 16, 30, tzinfo=timezone.utc)

        self.assertEqual(current_app_date(utc_now), date(2026, 6, 27))

    def test_resolve_friday_date_uses_current_market_week(self):
        saturday_in_shanghai = datetime(2026, 6, 27, 8, 0, tzinfo=timezone.utc)

        self.assertEqual(resolve_friday_date(now=saturday_in_shanghai), date(2026, 6, 26))

    def test_resolve_friday_date_keeps_explicit_query_parameter(self):
        self.assertEqual(resolve_friday_date("2026-06-12"), date(2026, 6, 12))


if __name__ == "__main__":
    unittest.main()
