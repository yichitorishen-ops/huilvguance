import subprocess
import sys
import unittest


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


if __name__ == "__main__":
    unittest.main()
