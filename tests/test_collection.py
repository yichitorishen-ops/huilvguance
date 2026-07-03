import unittest
from datetime import date, datetime, timezone
import os
import tempfile

import aiosqlite
import db
from collection import (
    collection_window,
    has_complete_slot,
    is_schedule_stale,
    latest_cron_datetime,
    recent_collection_windows,
)


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

    def test_recent_collection_windows_waits_until_capture_minute(self):
        now = datetime(2026, 7, 2, 10, 6, tzinfo=timezone.utc)

        windows = recent_collection_windows(now=now)

        self.assertEqual(windows, [])

    def test_recent_collection_windows_includes_missing_18_slot_for_backstop(self):
        now = datetime(2026, 7, 2, 11, 8, tzinfo=timezone.utc)

        windows = recent_collection_windows(now=now)

        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].window.record_date, date(2026, 7, 2))
        self.assertEqual(windows[0].window.time_point, "18:00")

    def test_recent_collection_windows_uses_late_retry_minutes_for_backstop(self):
        now = datetime(2026, 7, 3, 0, 32, tzinfo=timezone.utc)

        windows = recent_collection_windows(now=now)

        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].scheduled_at.hour, 6)
        self.assertEqual(windows[0].scheduled_at.minute, 57)
        self.assertEqual(windows[0].window.record_date, date(2026, 7, 3))
        self.assertEqual(windows[0].window.time_point, "06:00")


class SlotDataTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "sqlite.db")
        await db.init_db()

    async def asyncTearDown(self):
        db.DB_PATH = self.old_db_path
        self.tmp.cleanup()

    async def insert_price(self, table):
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute(
                f"INSERT INTO {table} (date_str, time_point, symbol, price) VALUES (?, ?, ?, ?)",
                ("2026-07-02", "13:00", "USD/CNY", 7.0),
            )
            await conn.commit()

    async def test_has_complete_slot_requires_quotes_and_bonds(self):
        await self.insert_price("mcn_quotes")

        self.assertFalse(await has_complete_slot("2026-07-02", "13:00"))

        await self.insert_price("wallstreet_bonds")

        self.assertTrue(await has_complete_slot("2026-07-02", "13:00"))


if __name__ == "__main__":
    unittest.main()
