import os
import tempfile
import unittest

import aiosqlite

import db
from service import query_weekly_bond_combo, query_weekly_combo


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


if __name__ == "__main__":
    unittest.main()
