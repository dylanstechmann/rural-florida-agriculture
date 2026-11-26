"""Validation and arithmetic tests for the NON-OPERATIONAL indoor simulator."""

import copy
import json
import math
import os
import socket
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm.indoor import (  # noqa: E402
    IndoorScenarioError,
    load_indoor_scenario,
    simulate_day,
    validate_indoor_scenario,
)
from floridafarm.indoor_report import render_indoor_json, render_indoor_markdown  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "indoor-simulation.json")


class IndoorSimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            cls.base = json.load(fh)
        cls.result = simulate_day(cls.base)

    def cfg(self):
        return copy.deepcopy(self.base)

    def assert_invalid(self, cfg):
        with self.assertRaises(IndoorScenarioError):
            validate_indoor_scenario(cfg)

    def test_committed_fixture_is_bounded_and_source_labelled(self):
        cfg = load_indoor_scenario(CONFIG_PATH)
        self.assertEqual(cfg["intervals"]["count"], 24)
        self.assertEqual(self.result["interval_minutes"], 60)
        self.assertEqual(len(self.result["intervals"]), 24)
        self.assertIn("NON-OPERATIONAL", self.result["scenario"]["status"])
        self.assertIn("no measured Iran site data", self.result["scenario"]["location_placeholder"])
        for profile in self.result["lighting_profiles"]:
            self.assertIn("synthetic", profile["source_label"])

    def test_photoperiod_dli_and_lighting_power_arithmetic(self):
        leafy, basil = self.result["lighting_profiles"]
        self.assertEqual(leafy["photoperiod_hours"], 12.0)
        self.assertEqual(leafy["dli_mol_m2_day"], 200.0 * 12.0 * 3600.0 / 1_000_000.0)
        self.assertEqual(leafy["lighting_power_kw"], 120.0 * 200.0 / 2.5 / 1000.0)
        self.assertEqual(basil["scheduled_window_hours"], 14.0)
        self.assertEqual(basil["photoperiod_hours"], 13.0)
        self.assertEqual(basil["overlap_hours"], 1.0)
        self.assertEqual(basil["dli_mol_m2_day"], 180.0 * 13.0 * 3600.0 / 1_000_000.0)
        self.assertEqual(basil["requested_kwh"], 78.0)

    def test_timer_gaps_overlaps_and_midnight_wrap(self):
        timer = self.result["timer_audits"][0]
        self.assertEqual(timer["active_hours"], 9.0)
        self.assertEqual(timer["overlap_hours"], 2.0)
        self.assertEqual(timer["gaps"], [{"start_minute": 300, "end_minute": 1200}])
        self.assertEqual(timer["overlap_windows"], [
            {"start_minute": 0, "end_minute": 60},
            {"start_minute": 180, "end_minute": 240},
        ])
        self.assertEqual(timer["union_windows"], [
            {"start_minute": 0, "end_minute": 300},
            {"start_minute": 1200, "end_minute": 1440},
        ])
        self.assertEqual(timer["requested_kwh"], 18.0)

    def test_half_open_interval_boundary_does_not_double_count(self):
        cfg = self.cfg()
        cfg["timers"][0]["schedule"] = [{"start_minute": 60, "end_minute": 120}]
        result = simulate_day(cfg)
        name = f"timer: {cfg['timers'][0]['name']}"
        active = []
        requested = []
        for interval in result["intervals"][:3]:
            row = next(load for load in interval["loads"] if load["name"] == name)
            active.append(row["active_minutes"])
            requested.append(row["requested_kwh"])
        self.assertEqual(active, [0, 60, 0])
        self.assertEqual(requested, [0.0, 2.0, 0.0])

    def test_energy_conservation_and_battery_bounds_every_interval(self):
        cfg = self.base["battery"]
        for row in self.result["intervals"]:
            requested = row["requested_critical_kwh"] + row["requested_noncritical_kwh"]
            served = row["served_critical_kwh"] + row["served_noncritical_kwh"]
            shed = row["shed_critical_kwh"] + row["shed_noncritical_kwh"]
            sources = row["solar_to_loads_kwh"] + row["grid_to_loads_kwh"] + row["battery_to_loads_kwh"]
            self.assertAlmostEqual(requested, served + shed, places=8)
            self.assertAlmostEqual(sources, served, places=8)
            self.assertAlmostEqual(
                row["solar_available_kwh"],
                row["solar_to_loads_kwh"] + row["solar_to_battery_kwh"] + row["solar_curtailed_kwh"],
                places=8,
            )
            expected_charge = (
                row["battery_charge_start_kwh"]
                + (row["solar_to_battery_kwh"] + row["grid_to_battery_kwh"])
                * cfg["charge_efficiency"]
                - row["battery_to_loads_kwh"] / cfg["discharge_efficiency"]
            )
            self.assertAlmostEqual(row["battery_charge_end_kwh"], expected_charge, places=8)
            self.assertGreaterEqual(row["battery_charge_end_kwh"], cfg["minimum_charge_kwh"] - 1e-9)
            self.assertLessEqual(row["battery_charge_end_kwh"], cfg["capacity_kwh"] + 1e-9)
            if not row["grid_available"]:
                self.assertEqual(row["grid_to_loads_kwh"], 0.0)
                self.assertEqual(row["grid_to_battery_kwh"], 0.0)
                self.assertEqual(row["served_noncritical_kwh"], 0.0)
        self.assertLessEqual(self.result["energy_summary"]["energy_balance_max_residual_kwh"], 1e-9)

    def test_outage_sheds_load_and_preserves_honest_shortfall(self):
        energy = self.result["energy_summary"]
        self.assertEqual(energy["outage_intervals"], 3)
        self.assertEqual(energy["battery_to_loads_kwh"], 27.0)
        self.assertEqual(energy["shed_critical_kwh"], 18.0)
        self.assertEqual(energy["shed_noncritical_kwh"], 33.0)
        first, second, third = self.result["intervals"][:3]
        self.assertEqual(first["served_critical_kwh"], 15.0)
        self.assertEqual(second["served_critical_kwh"], 12.0)
        self.assertEqual(second["shed_critical_kwh"], 3.0)
        self.assertEqual(third["served_critical_kwh"], 0.0)
        self.assertEqual(third["shed_critical_kwh"], 15.0)

    def test_battery_recovers_from_solar_and_bounded_grid_input(self):
        energy = self.result["energy_summary"]
        self.assertEqual(energy["battery_final_charge_kwh"], 100.0)
        self.assertTrue(energy["battery_recovery_target_met"])
        self.assertGreater(energy["solar_to_battery_kwh"], 0.0)
        self.assertGreater(energy["grid_to_battery_kwh"], 0.0)
        for row in self.result["intervals"]:
            self.assertLessEqual(row["grid_to_battery_kwh"], self.base["battery"]["grid_recovery_power_kw"])
            self.assertLessEqual(
                row["solar_to_battery_kwh"] + row["grid_to_battery_kwh"],
                self.base["battery"]["maximum_charge_power_kw"] + 1e-9,
            )

    def test_water_stock_recovery_makeup_and_reserve_ledger(self):
        water = self.result["water_summary"]
        self.assertEqual(water["initial_stock_l"], 300.0)
        self.assertEqual(water["minimum_end_stock_l"], 240.0)
        self.assertEqual(water["final_stock_l"], 345.0)
        self.assertEqual(water["recovered_l"], 315.0)
        self.assertEqual(water["makeup_l"], 210.0)
        self.assertEqual(water["shortfall_l"], 0.0)
        self.assertEqual(water["below_reserve_intervals"], 0)
        for row in self.result["intervals"]:
            self.assertGreaterEqual(row["water_stock_end_l"], 0.0)
            self.assertLessEqual(row["water_stock_end_l"], self.base["water"]["capacity_l"])
            self.assertAlmostEqual(
                row["water_stock_end_l"],
                row["water_stock_start_l"] + row["water_recovered_l"] + row["water_makeup_l"]
                - row["water_served_withdrawal_l"] - row["water_overflow_l"],
                places=8,
            )

    def test_water_shortfall_never_creates_negative_stock(self):
        cfg = self.cfg()
        cfg["water"].update({
            "initial_stock_l": 50.0,
            "reserve_l": 20.0,
            "withdrawal_l_per_hour": 100.0,
            "recovery_l_per_hour_by_interval": [0.0] * 24,
            "makeup_l_per_hour_by_interval": [0.0] * 24,
        })
        result = simulate_day(cfg)
        self.assertEqual(result["intervals"][0]["water_served_withdrawal_l"], 50.0)
        self.assertEqual(result["intervals"][0]["water_shortfall_l"], 50.0)
        self.assertEqual(result["intervals"][0]["water_stock_end_l"], 0.0)
        self.assertTrue(all(row["water_stock_end_l"] >= 0 for row in result["intervals"]))
        self.assertEqual(result["water_summary"]["below_reserve_intervals"], 24)

    def test_water_overflow_is_accounted_at_capacity(self):
        cfg = self.cfg()
        cfg["water"].update({
            "initial_stock_l": 1000.0,
            "withdrawal_l_per_hour": 0.0,
            "recovery_l_per_hour_by_interval": [100.0] * 24,
            "makeup_l_per_hour_by_interval": [0.0] * 24,
        })
        result = simulate_day(cfg)
        self.assertEqual(result["water_summary"]["final_stock_l"], 1000.0)
        self.assertEqual(result["water_summary"]["overflow_l"], 2400.0)

    def test_chemical_records_are_metadata_with_reserve_status(self):
        first, second = self.result["chemical_inventory"]
        self.assertEqual(first["reserve_status"], "AT_OR_ABOVE_RESERVE")
        self.assertEqual(first["stock_minus_reserve"], 15.0)
        self.assertEqual(second["reserve_status"], "BELOW_RESERVE")
        self.assertEqual(second["stock_minus_reserve"], -4.0)
        allowed = {
            "name", "stock_amount", "reserve_amount", "unit", "stock_minus_reserve",
            "reserve_status", "provenance", "source_label",
        }
        self.assertEqual(set(second), allowed)

    def test_negative_chemical_stock_and_reserve_rejected(self):
        for field in ("stock_amount", "reserve_amount"):
            with self.subTest(field=field):
                cfg = self.cfg()
                cfg["chemical_inventory"][0][field] = -0.01
                self.assert_invalid(cfg)

    def test_ambiguous_chemical_units_rejected(self):
        for unit in ("litres", "kg/day", "KG", "", None):
            with self.subTest(unit=unit):
                cfg = self.cfg()
                cfg["chemical_inventory"][0]["unit"] = unit
                self.assert_invalid(cfg)

    def test_inventory_instruction_fields_rejected(self):
        for field in ("dose", "mixing_instructions", "application_rate"):
            with self.subTest(field=field):
                cfg = self.cfg()
                cfg["chemical_inventory"][0][field] = "not permitted metadata"
                self.assert_invalid(cfg)

    def test_malformed_nonfinite_and_wrong_typed_inputs_rejected(self):
        mutations = []
        def add(label, mutate):
            mutations.append((label, mutate))
        add("NaN battery", lambda c: c["battery"].update(capacity_kwh=math.nan))
        add("infinite solar", lambda c: c["solar"]["power_kw_by_interval"].__setitem__(0, math.inf))
        add("NaN water", lambda c: c["water"].update(withdrawal_l_per_hour=math.nan))
        add("string PPFD", lambda c: c["lighting_profiles"][0].update(ppfd_umol_m2_s="200"))
        add("boolean power", lambda c: c["timers"][0].update(power_kw=True))
        add("integer grid flag", lambda c: c["grid"]["available_by_interval"].__setitem__(0, 1))
        add("zero efficiency", lambda c: c["battery"].update(charge_efficiency=0.0))
        add("negative initial water", lambda c: c["water"].update(initial_stock_l=-1.0))
        add("short solar series", lambda c: c["solar"]["power_kw_by_interval"].pop())
        add("short grid series", lambda c: c["grid"]["available_by_interval"].pop())
        add("zero interval count", lambda c: c["intervals"].update(count=0))
        add("excess interval count", lambda c: c["intervals"].update(count=97))
        add("non-divisor interval count", lambda c: c["intervals"].update(count=7))
        add("zero-length schedule", lambda c: c["timers"][0].update(schedule=[]))
        add("ambiguous zero window", lambda c: c["timers"][0].update(
            schedule=[{"start_minute": 0, "end_minute": 0}]
        ))
        add("boolean schedule boundary", lambda c: c["timers"][0].update(
            schedule=[{"start_minute": False, "end_minute": 60}]
        ))
        add("unknown schedule key", lambda c: c["timers"][0]["schedule"][0].update(enabled=True))
        add("negative lighting area", lambda c: c["lighting_profiles"][0].update(area_m2=-1.0))
        add("zero lighting efficacy", lambda c: c["lighting_profiles"][0].update(efficacy_umol_j=0.0))
        for label, mutate in mutations:
            with self.subTest(label=label):
                cfg = self.cfg()
                mutate(cfg)
                self.assert_invalid(cfg)

    def test_battery_relationship_validation(self):
        cfg = self.cfg()
        cfg["battery"]["initial_charge_kwh"] = 5.0
        self.assert_invalid(cfg)
        cfg = self.cfg()
        cfg["battery"]["recovery_target_charge_kwh"] = 121.0
        self.assert_invalid(cfg)
        cfg = self.cfg()
        cfg["battery"]["discharge_efficiency"] = 1.1
        self.assert_invalid(cfg)

    def test_configurable_48_interval_run_preserves_daily_arithmetic(self):
        cfg = self.cfg()
        cfg["intervals"]["count"] = 48
        cfg["grid"]["available_by_interval"] = [
            value for value in self.base["grid"]["available_by_interval"] for _ in range(2)
        ]
        cfg["solar"]["power_kw_by_interval"] = [
            value for value in self.base["solar"]["power_kw_by_interval"] for _ in range(2)
        ]
        for key in ("recovery_l_per_hour_by_interval", "makeup_l_per_hour_by_interval"):
            cfg["water"][key] = [value for value in self.base["water"][key] for _ in range(2)]
        result = simulate_day(cfg)
        self.assertEqual(len(result["intervals"]), 48)
        self.assertEqual(result["interval_minutes"], 30)
        self.assertEqual(result["lighting_profiles"], self.result["lighting_profiles"])
        self.assertAlmostEqual(
            result["energy_summary"]["requested_critical_kwh"],
            self.result["energy_summary"]["requested_critical_kwh"],
        )

    def test_determinism_and_input_immutability(self):
        cfg = self.cfg()
        original = copy.deepcopy(cfg)
        first = simulate_day(cfg)
        second = simulate_day(cfg)
        self.assertEqual(cfg, original)
        self.assertEqual(first, second)
        self.assertEqual(render_indoor_json(first), render_indoor_json(second))
        self.assertEqual(render_indoor_markdown(first), render_indoor_markdown(second))
        self.assertNotIn("NaN", render_indoor_json(first))
        self.assertNotIn("Infinity", render_indoor_json(first))

    def test_simulation_has_no_file_network_or_actuator_side_effects(self):
        cfg = self.cfg()
        with mock.patch("builtins.open", side_effect=AssertionError("unexpected file I/O")), \
             mock.patch.object(socket, "socket", side_effect=AssertionError("unexpected network I/O")):
            result = simulate_day(cfg)
        self.assertEqual(result, self.result)


if __name__ == "__main__":
    unittest.main()
