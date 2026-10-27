"""The committed report must match a fresh render from the committed config."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.config import load_scenario  # noqa: E402
from floridafarm.report import render_report  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "scenario.json")
REPORT_PATH = os.path.join(ROOT, "docs", "scenario-report.md")


class ReportTests(unittest.TestCase):
    def test_committed_report_matches_model(self):
        cfg = load_scenario(CONFIG_PATH)
        fresh = render_report(cfg)
        self.assertTrue(
            os.path.exists(REPORT_PATH),
            "docs/scenario-report.md is missing; run the report command",
        )
        with open(REPORT_PATH, encoding="utf-8") as fh:
            committed = fh.read()
        self.assertEqual(committed, fresh)

    def test_report_contains_key_sections(self):
        cfg = load_scenario(CONFIG_PATH)
        text = render_report(cfg)
        for heading in (
            "## 1. Scenario summary",
            "## 2. Crop matrix",
            "## 3. Water balance",
            "## 4. Energy balance",
            "## 5. Resilience and automation checklist",
            "## 6. Assumptions",
        ):
            self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()