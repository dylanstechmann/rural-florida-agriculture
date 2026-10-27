"""Config validation tests for the rural-Florida scenario."""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.config import ScenarioError, load_scenario  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "scenario.json")


class ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            cls.base = json.load(fh)

    def test_committed_scenario_valid(self):
        cfg = load_scenario(CONFIG_PATH)
        self.assertEqual(cfg["scenario"]["name"], "Rural Florida pilot campus")

    def _assert_bad(self, mutate):
        cfg = json.loads(json.dumps(self.base))
        mutate(cfg)
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "scenario.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(cfg, fh)
            with self.assertRaises(ScenarioError):
                load_scenario(path)

    def test_missing_section(self):
        self._assert_bad(lambda cfg: cfg.pop("water"))

    def test_unknown_section(self):
        self._assert_bad(lambda cfg: cfg.update({"extra": 1}))

    def test_recirculation_one_rejected(self):
        self._assert_bad(lambda cfg: cfg["water"].update({"recirculation_fraction": 1.0}))

    def test_negative_recirculation_rejected(self):
        self._assert_bad(lambda cfg: cfg["water"].update({"recirculation_fraction": -0.1}))

    def test_bad_system_rejected(self):
        self._assert_bad(lambda cfg: cfg["crops"][0].update({"system": "open field"}))

    def test_empty_crops_rejected(self):
        self._assert_bad(lambda cfg: cfg.update({"crops": []}))

    def test_indoor_area_exceeding_canopy_rejected(self):
        self._assert_bad(lambda cfg: cfg["crops"][0].update({"area_m2": 40000.0}))

    def test_screenhouse_area_exceeded_rejected(self):
        def mutate(cfg):
            cfg["crops"][5].update({"area_m2": cfg["campus"]["screenhouse_area_m2"] + 1.0})
        self._assert_bad(mutate)

    def test_string_for_number_rejected(self):
        self._assert_bad(lambda cfg: cfg["campus"].update({"battery_kwh": "two hundred"}))

    def test_lit_hours_over_24_rejected(self):
        self._assert_bad(lambda cfg: cfg["energy"].update({"lit_hours_per_day": 25}))

    def test_empty_n_plus_1_rejected(self):
        self._assert_bad(lambda cfg: cfg["automation"].update({"n_plus_1": []}))


if __name__ == "__main__":
    unittest.main()