import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collection import collect_once


def parse_args():
    parser = argparse.ArgumentParser(description="Collect one scheduled market data slot.")
    parser.add_argument("--scheduled-hour", type=int, choices=[0, 6, 13, 18])
    return parser.parse_args()


async def main():
    args = parse_args()
    result = await collect_once(scheduled_hour=args.scheduled_hour)
    window = result.window
    if not window.should_collect:
        print(f"skip={window.skip_reason}")
        return

    print(f"record_date={window.record_date:%Y-%m-%d}")
    print(f"time_point={window.time_point}")
    print(f"quotes={result.quotes_count}")
    print(f"bonds={result.bonds_count}")


if __name__ == "__main__":
    asyncio.run(main())
