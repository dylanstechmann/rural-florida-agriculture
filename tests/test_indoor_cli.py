"""CLI smoke test for the isolated indoor simulate-day command."""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.cli import main  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "indoor-simulation.json")


class IndoorCliTests(unittest.TestCase):
    def test_simulate_day_writes_deterministic_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            json_out = os.path.join(td, "day.json")
            markdown_out = os.path.join(td, "day.md")
            argv = [
                "simulate-day", "--config", CONFIG_PATH,
                "--json-out", json_out, "--markdown-out", markdown_out,
            ]
            self.assertEqual(main(argv), 0)
            with open(json_out, encoding="utf-8") as fh:
                first_json = fh.read()
            with open(markdown_out, encoding="utf-8") as fh:
                first_markdown = fh.read()
            self.assertEqual(json.loads(first_json)["interval_count"], 24)
            self.assertIn("NON-OPERATIONAL", first_markdown)
            self.assertEqual(main(argv), 0)
            with open(json_out, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), first_json)
            with open(markdown_out, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), first_markdown)


if __name__ == "__main__":
    unittest.main()
