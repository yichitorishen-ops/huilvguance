from pathlib import Path
import re
import unittest


BACKSTOP_CRON = "8,18,28,38,48,58 * * * *"
CAPTURE_CRONS = {
    "7,17,27,37,47,57 14,15,16,17 * * 1-5",
    "7,17,27,37,47,57 20,21,22,23 * * 0-4",
    "7,17,27,37,47,57 3,4,5,6 * * 1-5",
    "7,17,27,37,47,57 8,9,10,11 * * 1-5",
}


class WorkflowScheduleTest(unittest.TestCase):
    def test_scheduled_crons_avoid_top_of_hour(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)

        self.assertGreater(len(crons), 0)
        self.assertTrue(all(not cron.startswith("0 ") for cron in crons), crons)

    def test_each_data_slot_has_early_capture_schedule(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)
        slot_crons = [cron for cron in crons if cron != BACKSTOP_CRON]

        self.assertEqual(set(slot_crons), CAPTURE_CRONS)
        self.assertEqual(len(slot_crons), 4)

    def test_hourly_backstop_schedule_exists(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        crons = re.findall(r'cron: "([^"]+)"', workflow)

        self.assertIn(BACKSTOP_CRON, crons)

    def test_backstop_schedule_is_routed_to_catch_up(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")

        self.assertIn(f'backstop_cron="{BACKSTOP_CRON}"', workflow)
        self.assertIn('== "$backstop_cron"', workflow)
        self.assertIn('run_catch_up="true"', workflow)

    def test_data_commit_triggers_build_only_refresh(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")

        self.assertIn("DATA_COMMITTED=true", workflow)
        self.assertIn("actions: write", workflow)
        self.assertIn("Trigger Pages rebuild from data commit", workflow)
        self.assertIn("curl -fsS -X POST", workflow)
        self.assertIn("/actions/workflows/pages.yml/dispatches", workflow)
        self.assertIn('"collect":"false"', workflow)


if __name__ == "__main__":
    unittest.main()
