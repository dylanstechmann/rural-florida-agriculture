"""Model arithmetic tests: same formulas pinned against the committed config."""

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from floridafarm import model  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config", "scenario.json")


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            cls.cfg = json.load(fh)

    def test_canopy_and_footprint(self):
        c = self.cfg["campus"]
        self.assertAlmostEqual(
            model.canopy_area_m2(self.cfg),
            c["zone_count"] * c["lit_area_m2_per_zone"] * c["tiers_per_zone"],
        )
        self.assertAlmostEqual(
            model.zone_footprint_m2(self.cfg),
            c["zone_count"] * c["lit_area_m2_per_zone"],
        )

    def test_water_balance_arithmetic(self):
        c, w, cl = self.cfg["campus"], self.cfg["water"], self.cfg["climate"]
        canopy = model.canopy_area_m2(self.cfg)
        uptake = (
            canopy * w["uptake_l_per_m2_per_day"]
            + c["screenhouse_area_m2"] * w["screenhouse_uptake_l_per_m2_per_day"]
        )
        purge = uptake * (1.0 - w["recirculation_fraction"])
        makeup = max(0.0, purge - w["condensate_recovery_l_per_day"])
        rain = (
            cl["annual_rainfall_mm"] / 1000.0
            * c["roof_harvest_area_m2"]
            * w["rain_harvest_efficiency"]
            * 1000.0
            / 365.0
        )
        wb = model.water_balance(self.cfg)
        self.assertAlmostEqual(wb["uptake_l_per_day"], uptake)
        self.assertAlmostEqual(wb["net_makeup_l_per_day"], makeup)
        self.assertAlmostEqual(wb["rain_harvest_l_per_day"], rain)
        self.assertAlmostEqual(wb["irrigation_tank_l"], makeup * w["irrigation_backup_days"])
        self.assertGreater(wb["rain_harvest_l_per_day"], wb["net_makeup_l_per_day"])

    def test_energy_balance_arithmetic(self):
        c, e = self.cfg["campus"], self.cfg["energy"]
        canopy = model.canopy_area_m2(self.cfg)
        led = canopy * e["led_watts_per_m2_lit"] / 1000.0 * e["lit_hours_per_day"]
        eb = model.energy_balance(self.cfg)
        self.assertAlmostEqual(eb["led_kwh_per_day"], led)
        self.assertLessEqual(eb["solar_fraction"], 1.0)
        critical_kw = eb["total_kwh_per_day"] * c["critical_load_fraction"] / 24.0
        self.assertAlmostEqual(eb["battery_autonomy_hours"], c["battery_kwh"] / critical_kw)
        self.assertEqual(eb["battery_vs_target"], "GAP")

    def test_crop_rows_sum(self):
        rows = model.crop_rows(self.cfg)
        indoor = sum(r["annual_kg"] for r in rows if not r["screenhouse"])
        screen = sum(r["annual_kg"] for r in rows if r["screenhouse"])
        self.assertGreater(indoor, 0)
        self.assertGreater(screen, 0)
        for row in rows:
            self.assertAlmostEqual(
                row["annual_kg"],
                row["kg_per_cycle"] * row["cycles_per_year"],
                places=1,
            )


if __name__ == "__main__":
    unittest.main()