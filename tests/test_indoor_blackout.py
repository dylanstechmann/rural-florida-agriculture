"""Regression for the studied schema-v1 complete-blackout farm artifact."""

import copy
import hashlib
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.indoor import load_indoor_scenario, simulate_day  # noqa: E402
from floridafarm.indoor_report import render_indoor_json  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "indoor-simulation.json")
BASELINE_JSON_PATH = os.path.join(ROOT, "docs", "indoor-simulation.json")
BASELINE_SHA256 = "82981f9df5227450aa41d4b4620494564cc56c90f05fe6198d4ba0d3ffc78ba5"
BLACKOUT_SHA256 = "3996c10f0ccb3944bee2e6c53bdf84c8cc544d7f3d47d45dda654692e79bf3bf"


class IndoorBlackoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline_config = load_indoor_scenario(CONFIG_PATH)
        cls.baseline_result = simulate_day(cls.baseline_config)
        cls.blackout_config = copy.deepcopy(cls.baseline_config)
        count = cls.blackout_config["intervals"]["count"]
        cls.blackout_config["grid"]["available_by_interval"] = [False] * count
        cls.blackout_config["solar"]["power_kw_by_interval"] = [0.0] * count
        cls.blackout_config["battery"]["initial_charge_kwh"] = (
            cls.blackout_config["battery"]["minimum_charge_kwh"]
        )
        cls.blackout_result = simulate_day(cls.blackout_config)

    def test_blackout_derivation_preserves_version_and_other_assumptions(self):
        baseline = self.baseline_config
        blackout = self.blackout_config
        self.assertEqual(baseline["scenario"]["version"], "2026-11-26")
        self.assertEqual(blackout["scenario"], baseline["scenario"])
        self.assertEqual(self.blackout_result["scenario"]["version"], "2026-11-26")
        self.assertEqual(self.blackout_result["schema_version"], 1)
        self.assertEqual(blackout["water"], baseline["water"])
        self.assertEqual(blackout["lighting_profiles"], baseline["lighting_profiles"])
        self.assertEqual(blackout["timers"], baseline["timers"])
        self.assertEqual(blackout["continuous_loads"], baseline["continuous_loads"])
        self.assertEqual(blackout["chemical_inventory"], baseline["chemical_inventory"])
        self.assertEqual(blackout["grid"]["available_by_interval"], [False] * 24)
        self.assertEqual(blackout["solar"]["power_kw_by_interval"], [0.0] * 24)
        self.assertEqual(blackout["battery"]["initial_charge_kwh"], 10.0)
        self.assertEqual(
            blackout["battery"]["initial_charge_kwh"],
            blackout["battery"]["minimum_charge_kwh"],
        )
        expected_battery = copy.deepcopy(baseline["battery"])
        expected_battery["initial_charge_kwh"] = expected_battery["minimum_charge_kwh"]
        self.assertEqual(blackout["battery"], expected_battery)

    def test_exact_producer_artifact_pins(self):
        with open(BASELINE_JSON_PATH, "rb") as fh:
            committed_baseline = fh.read()
        baseline_json = render_indoor_json(self.baseline_result).encode("utf-8")
        blackout_json = render_indoor_json(self.blackout_result).encode("utf-8")
        self.assertEqual(committed_baseline, baseline_json)
        self.assertEqual(hashlib.sha256(baseline_json).hexdigest(), BASELINE_SHA256)
        self.assertEqual(hashlib.sha256(blackout_json).hexdigest(), BLACKOUT_SHA256)

    def test_complete_blackout_sheds_all_demand_without_changing_water(self):
        energy = self.blackout_result["energy_summary"]
        for flow in ("requested", "served", "shed"):
            total = energy[f"{flow}_critical_kwh"] + energy[f"{flow}_noncritical_kwh"]
            self.assertEqual(total, {"requested": 643.2, "served": 0.0, "shed": 643.2}[flow])
        self.assertEqual(energy["shed_critical_kwh"], 360.0)
        self.assertEqual(energy["shed_noncritical_kwh"], 283.2)
        self.assertEqual(energy["outage_intervals"], 24)
        self.assertEqual(energy["battery_initial_charge_kwh"], 10.0)
        self.assertEqual(energy["battery_final_charge_kwh"], 10.0)
        self.assertEqual(energy["battery_to_loads_kwh"], 0.0)

        water = self.blackout_result["water_summary"]
        self.assertEqual(water["requested_withdrawal_l"], 480.0)
        self.assertEqual(water["served_withdrawal_l"], 480.0)
        self.assertEqual(water["recovered_l"], 315.0)
        self.assertEqual(water["shortfall_l"], 0.0)
        self.assertEqual(water, self.baseline_result["water_summary"])
        for baseline_row, blackout_row in zip(
            self.baseline_result["intervals"], self.blackout_result["intervals"]
        ):
            baseline_water = {
                key: value for key, value in baseline_row.items() if key.startswith("water_")
            }
            blackout_water = {
                key: value for key, value in blackout_row.items() if key.startswith("water_")
            }
            self.assertEqual(blackout_water, baseline_water)

    def test_producer_exposes_recovery_after_shed_intervals(self):
        # This pins producer facts only; the habitat importer owns the consumer
        # power-coupling interpretation and calls these observed conflicts.
        indices = []
        rows = self.blackout_result["intervals"]
        for previous, current in zip(rows, rows[1:]):
            previous_shed = previous["shed_critical_kwh"] + previous["shed_noncritical_kwh"]
            if previous_shed > 0 and current["water_recovered_l"] > 0:
                indices.append(current["index"])
        self.assertEqual(indices, list(range(3, 24)))
        self.assertEqual(len(indices), 21)


if __name__ == "__main__":
    unittest.main()
