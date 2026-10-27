"""CLI smoke tests (the report command writes only to a temp directory)."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.cli import main  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "scenario.json")


class CliTests(unittest.TestCase):
    def test_validate_command(self):
        self.assertEqual(main(["validate", "--config", CONFIG_PATH]), 0)

    def test_report_writes_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "report.md")
            self.assertEqual(main(["report", "--config", CONFIG_PATH, "--out", out]), 0)
            self.assertTrue(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()