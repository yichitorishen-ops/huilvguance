import os
from contextlib import asynccontextmanager
import aiosqlite
from loguru import logger

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "sqlite.db")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

@asynccontextmanager
async def get_conn():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    try:
        yield conn
    finally:
        await conn.close()


async def init_db():
    async with get_conn() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mcn_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_str VARCHAR(64),
                time_point VARCHAR(64),
                symbol VARCHAR(64),
                price REAL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS wallstreet_bonds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_str VARCHAR(64),
                time_point VARCHAR(64),
                symbol VARCHAR(64),
                price REAL
            )
        """)
        await conn.commit()

async def save_mcn_quotes(data: list, date_str: str, time_point: str):
    if not data:
        return
    async with get_conn() as conn:
        values = [
            {
                "date_str": date_str,
                "time_point": time_point,
                "symbol": item["symbol"],
                "price": item.get("price", 0.0)
            }
            for item in data
        ]
        await conn.executemany(
            "INSERT INTO mcn_quotes (date_str, time_point, symbol, price) VALUES (:date_str, :time_point, :symbol, :price)",
            values
        )
        await conn.commit()

async def save_wallstreet_bonds(data: list, date_str: str, time_point: str):
    if not data:
        return
    async with get_conn() as conn:
        values = [
            {
                "date_str": date_str,
                "time_point": time_point,
                "symbol": item["symbol"],
                "price": item.get("price", 0.0)
            }
            for item in data
        ]
        await conn.executemany(
            "INSERT INTO wallstreet_bonds (date_str, time_point, symbol, price) VALUES (:date_str, :time_point, :symbol, :price)",
            values
        )
        await conn.commit()


async def replace_mcn_quotes(data: list, date_str: str, time_point: str):
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM mcn_quotes WHERE date_str = ? AND time_point = ?",
            (date_str, time_point),
        )
        if data:
            values = [
                {
                    "date_str": date_str,
                    "time_point": time_point,
                    "symbol": item["symbol"],
                    "price": item.get("price", 0.0),
                }
                for item in data
            ]
            await conn.executemany(
                "INSERT INTO mcn_quotes (date_str, time_point, symbol, price) VALUES (:date_str, :time_point, :symbol, :price)",
                values,
            )
        await conn.commit()


async def replace_wallstreet_bonds(data: list, date_str: str, time_point: str):
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM wallstreet_bonds WHERE date_str = ? AND time_point = ?",
            (date_str, time_point),
        )
        if data:
            values = [
                {
                    "date_str": date_str,
                    "time_point": time_point,
                    "symbol": item["symbol"],
                    "price": item.get("price", 0.0),
                }
                for item in data
            ]
            await conn.executemany(
                "INSERT INTO wallstreet_bonds (date_str, time_point, symbol, price) VALUES (:date_str, :time_point, :symbol, :price)",
                values,
            )
        await conn.commit()
