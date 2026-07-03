from pathlib import Path
from collections import Counter
import re
import unittest


BACKSTOP_CRON = "8,18,28,38,48,58 * * * *"


class WorkflowScheduleTest(unittest.TestCase):
    def test_scheduled_crons_avoid_top_of_hour(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)

        self.assertGreater(len(crons), 0)
        self.assertTrue(all(not cron.startswith("0 ") for cron in crons), crons)

    def test_each_data_slot_has_retry_schedule(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)
        slot_crons = [cron for cron in crons if cron != BACKSTOP_CRON]
        hours = [cron.split()[1] for cron in slot_crons]

        self.assertEqual(Counter(hours), Counter({"16": 6, "22": 6, "5": 6, "10": 6}))

    def test_hourly_backstop_schedule_exists(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)

        self.assertIn(BACKSTOP_CRON, crons)

    def test_backstop_schedule_is_routed_to_catch_up(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")

        self.assertIn(f'backstop_cron="{BACKSTOP_CRON}"', workflow)
        self.assertIn('== "$backstop_cron"', workflow)
        self.assertIn('run_catch_up="true"', workflow)


if __name__ == "__main__":
    unittest.main()
