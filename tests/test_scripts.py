import subprocess
import sys
import unittest
from datetime import date
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import scripts.collect_once as collect_script


class ScriptEntrypointTest(unittest.TestCase):
    def test_build_script_help_runs_from_project_root(self):
        result = subprocess.run(
            [sys.executable, "scripts/build_static_site.py", "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_collect_script_help_runs_from_project_root(self):
        result = subprocess.run(
            [sys.executable, "scripts/collect_once.py", "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_collect_script_help_includes_catch_up_options(self):
        result = subprocess.run(
            [sys.executable, "scripts/collect_once.py", "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--catch-up", result.stdout)
        self.assertIn("--max-delay-minutes", result.stdout)


class CollectScriptBehaviorTest(unittest.IsolatedAsyncioTestCase):
    async def test_scheduled_hour_dispatch_skips_existing_slot(self):
        result = SimpleNamespace(
            window=SimpleNamespace(
                should_collect=True,
                record_date=date(2026, 7, 3),
                time_point="13:00",
            ),
            skip_reason="existing_slot",
            quotes_count=0,
            bonds_count=0,
        )

        with (
            patch.object(sys, "argv", ["collect_once.py", "--scheduled-hour", "13"]),
            patch("sys.stdout", new_callable=StringIO),
            patch.object(collect_script, "collect_once", AsyncMock(return_value=result)) as mocked_collect,
        ):
            await collect_script.main()

        mocked_collect.assert_awaited_once()
        self.assertTrue(mocked_collect.await_args.kwargs["skip_existing"])


if __name__ == "__main__":
    unittest.main()
