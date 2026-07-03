from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collection import collect_missing_recent_slots, collect_once


class StockDataScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.scheduler.add_job(
            self.collect_data,
            "cron",
            hour="0,1,4,5,6,7,11,12,13,14,16,17,18,19,22,23",
            minute="7,17,27,37,47,57",
        )
        self.scheduler.add_job(self.catch_up_missing_data, "cron", minute="8,18,28,38,48,58")

    async def collect_data(self):
        result = await collect_once(skip_existing=True)
        window = result.window
        if not window.should_collect:
            logger.info(f"skip collection: {window.skip_reason}")
            return
        if result.skip_reason:
            logger.info(
                "skip collection: date={}, time={}, reason={}",
                window.record_date.strftime("%Y-%m-%d"),
                window.time_point,
                result.skip_reason,
            )
            return

        logger.info(
            "collection complete: date={}, time={}, quotes={}, bonds={}",
            window.record_date.strftime("%Y-%m-%d"),
            window.time_point,
            result.quotes_count,
            result.bonds_count,
        )

    async def catch_up_missing_data(self):
        results = await collect_missing_recent_slots()
        if not results:
            logger.info("catch-up complete: no due slots")
            return

        for item in results:
            window = item.result.window
            if item.result.skip_reason:
                logger.info(
                    "catch-up skip: scheduled_at={}, date={}, time={}, reason={}",
                    item.scheduled_at.isoformat(),
                    window.record_date.strftime("%Y-%m-%d"),
                    window.time_point,
                    item.result.skip_reason,
                )
                continue

            logger.info(
                "catch-up collected: scheduled_at={}, date={}, time={}, quotes={}, bonds={}",
                item.scheduled_at.isoformat(),
                window.record_date.strftime("%Y-%m-%d"),
                window.time_point,
                item.result.quotes_count,
                item.result.bonds_count,
            )

    def start(self):
        self.scheduler.start()
        logger.info(
            "scheduler started: slots at 00:00, 06:00, 13:00, 18:00; "
            "capture windows open two hours early; catch-up every 10 minutes"
        )

    def stop(self):
        self.scheduler.shutdown()
        logger.info("scheduler stopped")
