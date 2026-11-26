"""Committed indoor JSON and Markdown must match fresh deterministic renders."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.indoor import load_indoor_scenario, simulate_day  # noqa: E402
from floridafarm.indoor_report import render_indoor_json, render_indoor_markdown  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "indoor-simulation.json")
JSON_PATH = os.path.join(ROOT, "docs", "indoor-simulation.json")
MARKDOWN_PATH = os.path.join(ROOT, "docs", "indoor-simulation-report.md")


class IndoorReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = simulate_day(load_indoor_scenario(CONFIG_PATH))

    def test_committed_json_matches_simulation(self):
        with open(JSON_PATH, encoding="utf-8") as fh:
            committed = fh.read()
        self.assertEqual(committed, render_indoor_json(self.result))

    def test_committed_markdown_matches_simulation(self):
        with open(MARKDOWN_PATH, encoding="utf-8") as fh:
            committed = fh.read()
        self.assertEqual(committed, render_indoor_markdown(self.result))

    def test_report_contains_scope_and_honest_negative(self):
        text = render_indoor_markdown(self.result)
        for content in (
            "NON-OPERATIONAL",
            "no measured Iran site data",
            "DLI (mol/m2/day)",
            "Timer gaps, overlaps and midnight boundaries",
            "Honest negative: the synthetic outage leaves 18.000 kWh",
            "Chemical/nutrient inventory metadata only",
            "No food-safety claim, storm-resilience certification",
            "not an environmental-control substitute",
        ):
            self.assertIn(content, text)


if __name__ == "__main__":
    unittest.main()
