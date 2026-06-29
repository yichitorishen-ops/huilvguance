from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collection import collect_once


class StockDataScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.scheduler.add_job(self.collect_data, "cron", hour="0,6,13,18", minute=0)

    async def collect_data(self):
        result = await collect_once()
        window = result.window
        if not window.should_collect:
            logger.info(f"skip collection: {window.skip_reason}")
            return

        logger.info(
            "collection complete: date={}, time={}, quotes={}, bonds={}",
            window.record_date.strftime("%Y-%m-%d"),
            window.time_point,
            result.quotes_count,
            result.bonds_count,
        )

    def start(self):
        self.scheduler.start()
        logger.info("scheduler started: 00:00, 06:00, 13:00, 18:00 Asia/Shanghai")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("scheduler stopped")
