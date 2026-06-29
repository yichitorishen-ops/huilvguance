import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from static_site import build_static_site


def parse_args():
    parser = argparse.ArgumentParser(description="Build the static GitHub Pages site.")
    parser.add_argument("--output", default="dist")
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument("--target-friday")
    return parser.parse_args()


async def main():
    args = parse_args()
    output = await build_static_site(
        output_dir=args.output,
        weeks=args.weeks,
        target_friday=args.target_friday,
    )
    print(f"output={output}")


if __name__ == "__main__":
    asyncio.run(main())
