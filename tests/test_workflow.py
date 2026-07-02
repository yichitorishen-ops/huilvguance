from pathlib import Path
from collections import Counter
import re
import unittest


class WorkflowScheduleTest(unittest.TestCase):
    def test_scheduled_crons_avoid_top_of_hour(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)

        self.assertGreater(len(crons), 0)
        self.assertTrue(all(not cron.startswith("0 ") for cron in crons), crons)

    def test_each_data_slot_has_retry_schedule(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)
        hours = [cron.split()[1] for cron in crons]

        self.assertEqual(Counter(hours), Counter({"16": 2, "22": 2, "5": 2, "10": 2}))


if __name__ == "__main__":
    unittest.main()
