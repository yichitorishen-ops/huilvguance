import unittest
from datetime import date, datetime, timezone

from collection import collection_window


class CollectionWindowTest(unittest.TestCase):
    def test_scheduled_hour_overrides_delayed_action_runtime(self):
        delayed_runtime = datetime(2026, 6, 29, 23, 20, tzinfo=timezone.utc)

        window = collection_window(now=delayed_runtime, scheduled_hour=6)

        self.assertTrue(window.should_collect)
        self.assertEqual(window.record_date, date(2026, 6, 30))
        self.assertEqual(window.time_point, "06:00")

    def test_monday_zero_is_skipped(self):
        window = collection_window(now=datetime(2026, 6, 28, 16, 5, tzinfo=timezone.utc), scheduled_hour=0)

        self.assertFalse(window.should_collect)
        self.assertEqual(window.skip_reason, "monday_00")

    def test_saturday_zero_collects_friday_close(self):
        window = collection_window(now=datetime(2026, 6, 26, 16, 10, tzinfo=timezone.utc), scheduled_hour=0)

        self.assertTrue(window.should_collect)
        self.assertEqual(window.record_date, date(2026, 6, 26))
        self.assertEqual(window.time_point, "00:00")

    def test_saturday_daytime_is_skipped(self):
        window = collection_window(now=datetime(2026, 6, 27, 6, 0, tzinfo=timezone.utc), scheduled_hour=13)

        self.assertFalse(window.should_collect)
        self.assertEqual(window.skip_reason, "saturday_daytime")

    def test_sunday_is_skipped(self):
        window = collection_window(now=datetime(2026, 6, 28, 6, 0, tzinfo=timezone.utc), scheduled_hour=13)

        self.assertFalse(window.should_collect)
        self.assertEqual(window.skip_reason, "sunday")


if __name__ == "__main__":
    unittest.main()
