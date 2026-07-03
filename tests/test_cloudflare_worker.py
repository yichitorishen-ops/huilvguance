from pathlib import Path
import unittest


WORKER_DIR = Path("cloudflare/huilvguance-watchdog")


class CloudflareWorkerTest(unittest.TestCase):
    def test_wrangler_config_uses_off_hour_ten_minute_cron(self):
        config = (WORKER_DIR / "wrangler.toml").read_text(encoding="utf-8")

        self.assertIn('name = "huilvguance-watchdog"', config)
        self.assertIn('account_id = "da5447a259dab3a8964ef0b06c91f2c3"', config)
        self.assertIn('crons = ["7,17,27,37,47,57 * * * *"]', config)

    def test_worker_dispatches_existing_github_workflow(self):
        source = (WORKER_DIR / "src/index.js").read_text(encoding="utf-8")

        self.assertIn("repos/yichitorishen-ops/huilvguance/actions/workflows/pages.yml/dispatches", source)
        self.assertIn('collect: "true"', source)
        self.assertIn("scheduled_hour", source)
        self.assertIn("GITHUB_TOKEN", source)

    def test_worker_files_do_not_embed_tokens(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                WORKER_DIR / "wrangler.toml",
                WORKER_DIR / "src/index.js",
            ]
        )

        self.assertNotIn("ghp_", combined)
        self.assertNotIn("cfut_", combined)


if __name__ == "__main__":
    unittest.main()
