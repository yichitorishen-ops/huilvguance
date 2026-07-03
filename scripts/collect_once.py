import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collection import collect_missing_recent_slots, collect_once, is_schedule_stale, latest_cron_datetime


def parse_args():
    parser = argparse.ArgumentParser(description="Collect one scheduled market data slot.")
    parser.add_argument("--scheduled-hour", type=int, choices=[0, 6, 13, 18])
    parser.add_argument("--schedule-cron")
    parser.add_argument("--catch-up", action="store_true")
    parser.add_argument("--max-delay-minutes", type=int, default=120)
    return parser.parse_args()


async def main():
    args = parse_args()
    if args.catch_up:
        results = await collect_missing_recent_slots(max_delay_minutes=args.max_delay_minutes)
        collected = 0
        for item in results:
            window = item.result.window
            prefix = (
                f"scheduled_at={item.scheduled_at.isoformat()} "
                f"record_date={window.record_date:%Y-%m-%d} "
                f"time_point={window.time_point}"
            )
            if item.result.skip_reason:
                print(f"skip={item.result.skip_reason} {prefix}")
                continue

            collected += 1
            print(
                f"collected=true {prefix} "
                f"quotes={item.result.quotes_count} bonds={item.result.bonds_count}"
            )

        print(f"checked={len(results)}")
        print(f"collected={collected}")
        return

    scheduled_at = latest_cron_datetime(args.schedule_cron) if args.schedule_cron else None
    if scheduled_at and is_schedule_stale(scheduled_at):
        print(f"skip=stale_schedule scheduled_at={scheduled_at.isoformat()}")
        return

    result = await collect_once(
        scheduled_hour=args.scheduled_hour,
        scheduled_at=scheduled_at,
        skip_existing=scheduled_at is not None,
    )
    window = result.window
    if not window.should_collect:
        print(f"skip={window.skip_reason}")
        return
    if result.skip_reason:
        print(f"skip={result.skip_reason}")
        print(f"record_date={window.record_date:%Y-%m-%d}")
        print(f"time_point={window.time_point}")
        return

    print(f"record_date={window.record_date:%Y-%m-%d}")
    print(f"time_point={window.time_point}")
    print(f"quotes={result.quotes_count}")
    print(f"bonds={result.bonds_count}")


if __name__ == "__main__":
    asyncio.run(main())
