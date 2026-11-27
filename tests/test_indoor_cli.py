"""CLI smoke test for the isolated indoor simulate-day command."""

import json
import hashlib
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.cli import main  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "indoor-simulation.json")


class IndoorCliTests(unittest.TestCase):
    def test_water_handoff_pins_the_report_and_reads_configured_capacity(self):
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = json.loads(Path(CONFIG_PATH).read_bytes())
            config["water"]["capacity_l"] = 1250
            (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
            argv = ["simulate-day", "--config", str(root / "config.json"),
                    "--json-out", str(root / "day.json"), "--markdown-out", str(root / "day.md"),
                    "--water-handoff-out", str(root / "handoff.json")]
            self.assertEqual(main(argv), 0)
            self.assertEqual(json.loads((root / "handoff.json").read_bytes()), {
                "schema": "synthetic-farm-water-handoff/1",
                "report_sha256": hashlib.sha256((root / "day.json").read_bytes()).hexdigest(),
                "reservoir_capacity_l": 1250,
            })
            with self.assertRaises(SystemExit):
                main(argv[:-1] + [str(root / "config.json")])
            self.assertEqual(json.loads((root / "config.json").read_bytes()), config)

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
