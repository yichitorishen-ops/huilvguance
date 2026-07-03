import os
import tempfile
import unittest

import aiosqlite

from config import compose_list
import db
from service import (
    compute_combo_lines,
    query_weekly_amplitude,
    query_weekly_bond_combo,
    query_weekly_bonds,
    query_weekly_combo,
)


class ServiceHistoryBaselineTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "sqlite.db")
        await db.init_db()

    async def asyncTearDown(self):
        db.DB_PATH = self.old_db_path
        self.tmp.cleanup()

    async def insert_price(self, table, date_str, time_point, symbol, price):
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute(
                f"INSERT INTO {table} (date_str, time_point, symbol, price) VALUES (?, ?, ?, ?)",
                (date_str, time_point, symbol, price),
            )
            await conn.commit()

    async def test_currency_combo_uses_latest_history_when_week_baseline_is_missing(self):
        for symbol, old_price, new_price in [
            ("USD/CNY", 7.0, 7.1),
            ("CNY/JPY", 20.0, 19.8),
            ("USD/JPY", 140.0, 142.0),
        ]:
            await self.insert_price("mcn_quotes", "2026-06-12", "00:00", symbol, old_price)
            await self.insert_price("mcn_quotes", "2026-06-29", "00:00", symbol, new_price)

        combos = await query_weekly_combo("2026-06-26")
        first_combo = combos[0]
        monday_close = first_combo["days"][1]["points"][3]["lines"]

        self.assertNotEqual(monday_close, ["-", "-", "-"])

    async def test_bond_logic_combo_uses_latest_history_when_week_baseline_is_missing(self):
        for symbol, old_price, new_price in [
            ("US10YR", 4.0, 4.1),
            ("CN10YR", 2.0, 2.05),
            ("JP10YR", 1.0, 0.99),
        ]:
            await self.insert_price("wallstreet_bonds", "2026-06-12", "00:00", symbol, old_price)
            await self.insert_price("wallstreet_bonds", "2026-06-29", "00:00", symbol, new_price)

        combos = await query_weekly_bond_combo("2026-06-26")
        logic_rows = [row for row in combos if row["type"] == "logic"]
        monday_close = logic_rows[0]["days"][1]["points"][3]["lines"]

        self.assertNotEqual(monday_close, ["-", "-", "-"])

    async def test_currency_daily_change_uses_today_same_time_as_latest_baseline(self):
        await self.insert_price("mcn_quotes", "2026-07-02", "13:00", "USD/CNY", 100.0)
        await self.insert_price("mcn_quotes", "2026-07-03", "13:00", "USD/CNY", 110.0)
        await self.insert_price("mcn_quotes", "2026-07-03", "00:00", "USD/CNY", 150.0)

        rows = await query_weekly_amplitude("2026-07-03")
        usd_cny = next(row for row in rows if row["symbol"] == "USD/CNY")
        friday = usd_cny["days"][0]

        self.assertEqual(friday["daily_price"], 110.0)
        self.assertEqual(friday["daily_amplitude"], 0.1)
        self.assertEqual(friday["daily_diff"], 10.0)

    async def test_currency_daily_change_uses_latest_today_time_when_today_close_is_missing(self):
        await self.insert_price("mcn_quotes", "2026-07-01", "13:00", "USD/CNY", 100.0)
        await self.insert_price("mcn_quotes", "2026-07-01", "00:00", "USD/CNY", 200.0)
        await self.insert_price("mcn_quotes", "2026-07-02", "13:00", "USD/CNY", 110.0)

        rows = await query_weekly_amplitude("2026-06-26")
        usd_cny = next(row for row in rows if row["symbol"] == "USD/CNY")
        thursday = usd_cny["days"][4]

        self.assertEqual(thursday["daily_price"], 110.0)
        self.assertEqual(thursday["daily_amplitude"], 0.1)
        self.assertEqual(thursday["daily_diff"], 10.0)

    async def test_bond_daily_change_uses_today_same_time_as_latest_baseline(self):
        await self.insert_price("wallstreet_bonds", "2026-07-02", "13:00", "US10YR", 4.0)
        await self.insert_price("wallstreet_bonds", "2026-07-03", "13:00", "US10YR", 4.2)
        await self.insert_price("wallstreet_bonds", "2026-07-03", "00:00", "US10YR", 4.8)

        rows = await query_weekly_bonds("2026-07-03")
        us10 = next(row for row in rows if row["symbol"] == "US10YR")
        friday = us10["days"][0]

        self.assertEqual(friday["daily_price"], 4.2)
        self.assertEqual(friday["daily_amplitude"], 0.05)
        self.assertEqual(friday["daily_diff"], 0.2)

    async def test_bond_daily_change_uses_latest_today_time_when_today_close_is_missing(self):
        await self.insert_price("wallstreet_bonds", "2026-07-01", "13:00", "US10YR", 4.0)
        await self.insert_price("wallstreet_bonds", "2026-07-01", "00:00", "US10YR", 5.0)
        await self.insert_price("wallstreet_bonds", "2026-07-02", "13:00", "US10YR", 4.2)

        rows = await query_weekly_bonds("2026-06-26")
        us10 = next(row for row in rows if row["symbol"] == "US10YR")
        thursday = us10["days"][4]

        self.assertEqual(thursday["daily_price"], 4.2)
        self.assertEqual(thursday["daily_amplitude"], 0.05)
        self.assertEqual(thursday["daily_diff"], 0.2)

    async def test_currency_combo_daily_change_uses_today_same_time_as_latest_baseline(self):
        for symbol, old_price, new_price, close_price in [
            ("USD/CNY", 100.0, 110.0, 150.0),
            ("CNY/JPY", 200.0, 220.0, 260.0),
            ("USD/JPY", 300.0, 300.0, 360.0),
        ]:
            await self.insert_price("mcn_quotes", "2026-07-02", "13:00", symbol, old_price)
            await self.insert_price("mcn_quotes", "2026-07-03", "13:00", symbol, new_price)
            await self.insert_price("mcn_quotes", "2026-07-03", "00:00", symbol, close_price)

        combos = await query_weekly_combo("2026-07-03")
        first_combo = combos[0]
        friday_daily = first_combo["days"][0]["daily_lines"]
        meta_a, meta_b, meta_c, _ = compose_list[0]

        self.assertEqual(
            friday_daily,
            compute_combo_lines(0.1, 0.1, 0.0, meta_a["name"], meta_b["name"], meta_c["name"]),
        )


if __name__ == "__main__":
    unittest.main()
