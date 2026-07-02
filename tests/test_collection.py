import unittest
from datetime import date, datetime, timezone

from collection import collection_window, is_schedule_stale, latest_cron_datetime


class CollectionWindowTest(unittest.TestCase):
    def test_scheduled_hour_overrides_delayed_action_runtime(self):
        delayed_runtime = datetime(2026, 6, 29, 23, 20, tzinfo=timezone.utc)

        window = collection_window(now=delayed_runtime, scheduled_hour=6)

        self.assertTrue(window.should_collect)
        self.assertEqual(window.record_date, date(2026, 6, 30))
        self.assertEqual(window.time_point, "06:00")

    def test_scheduled_at_preserves_original_date_when_action_is_delayed_cross_day(self):
        original_schedule = datetime(2026, 7, 1, 10, 17, tzinfo=timezone.utc)

        window = collection_window(scheduled_at=original_schedule)

        self.assertTrue(window.should_collect)
        self.assertEqual(window.record_date, date(2026, 7, 1))
        self.assertEqual(window.time_point, "18:00")

    def test_latest_cron_datetime_finds_original_schedule_before_delayed_runtime(self):
        delayed_runtime = datetime(2026, 7, 1, 21, 13, tzinfo=timezone.utc)

        scheduled_at = latest_cron_datetime("17 10 * * 1-5", now=delayed_runtime)

        self.assertEqual(scheduled_at, datetime(2026, 7, 1, 10, 17, tzinfo=timezone.utc))

    def test_schedule_delayed_many_hours_is_stale(self):
        scheduled_at = datetime(2026, 7, 1, 10, 17, tzinfo=timezone.utc)
        delayed_runtime = datetime(2026, 7, 1, 21, 13, tzinfo=timezone.utc)

        self.assertTrue(is_schedule_stale(scheduled_at, now=delayed_runtime))

    def test_schedule_delayed_less_than_two_hours_is_not_stale(self):
        scheduled_at = datetime(2026, 7, 1, 16, 17, tzinfo=timezone.utc)
        delayed_runtime = datetime(2026, 7, 1, 17, 32, tzinfo=timezone.utc)

        self.assertFalse(is_schedule_stale(scheduled_at, now=delayed_runtime))

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
