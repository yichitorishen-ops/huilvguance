from pathlib import Path
import re
import unittest


class WorkflowScheduleTest(unittest.TestCase):
    def test_scheduled_crons_avoid_top_of_hour(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)

        self.assertGreater(len(crons), 0)
        self.assertTrue(all(not cron.startswith("0 ") for cron in crons), crons)


if __name__ == "__main__":
    unittest.main()
