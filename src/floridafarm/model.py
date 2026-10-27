"""Transparent placeholder arithmetic for the rural-Florida scenario.

Every function here is arithmetic on the labeled assumptions in
config/scenario.json. Outputs are sizing proxies for a concept, never
measurements or performance claims.
"""

SCREENHOUSE = "screenhouse + protected enclosure"


def canopy_area_m2(cfg):
    c = cfg["campus"]
    return float(c["zone_count"] * c["lit_area_m2_per_zone"] * c["tiers_per_zone"])


def zone_footprint_m2(cfg):
    c = cfg["campus"]
    return float(c["zone_count"] * c["lit_area_m2_per_zone"])


def crop_rows(cfg):
    rows = []
    for crop in cfg["crops"]:
        area = float(crop["area_m2"])
        cycles = float(crop["cycles_per_year"])
        kg_per_m2 = float(crop["kg_per_m2_per_cycle"])
        per_cycle = area * kg_per_m2
        rows.append({
            "name": crop["name"],
            "system": crop["system"],
            "area_m2": area,
            "cycles_per_year": cycles,
            "kg_per_cycle": round(per_cycle, 1),
            "annual_kg": round(per_cycle * cycles, 1),
            "screenhouse": crop["system"] == SCREENHOUSE,
        })
    return rows


def water_balance(cfg):
    c, w, cl = cfg["campus"], cfg["water"], cfg["climate"]
    canopy = canopy_area_m2(cfg)
    uptake_indoor = canopy * float(w["uptake_l_per_m2_per_day"])
    uptake_screen = float(c["screenhouse_area_m2"]) * float(w["screenhouse_uptake_l_per_m2_per_day"])
    uptake = uptake_indoor + uptake_screen
    recirc = float(w["recirculation_fraction"])
    purge = uptake * (1.0 - recirc)
    condensate = float(w["condensate_recovery_l_per_day"])
    net_makeup = max(0.0, purge - condensate)
    rain = (
        float(cl["annual_rainfall_mm"]) / 1000.0
        * float(c["roof_harvest_area_m2"])
        * float(w["rain_harvest_efficiency"])
        * 1000.0
        / 365.0
    )
    tank_l = net_makeup * float(w["irrigation_backup_days"])
    return {
        "canopy_m2": canopy,
        "uptake_l_per_day": uptake,
        "uptake_indoor_l_per_day": uptake_indoor,
        "uptake_screenhouse_l_per_day": uptake_screen,
        "recirculated_l_per_day": uptake * recirc,
        "purge_l_per_day": purge,
        "condensate_l_per_day": condensate,
        "net_makeup_l_per_day": net_makeup,
        "rain_harvest_l_per_day": rain,
        "irrigation_tank_l": tank_l,
        "tank_days_of_full_uptake": (tank_l / uptake) if uptake else 0.0,
    }


def energy_balance(cfg):
    c, e, cl = cfg["campus"], cfg["energy"], cfg["climate"]
    canopy = canopy_area_m2(cfg)
    led = canopy * float(e["led_watts_per_m2_lit"]) / 1000.0 * float(e["lit_hours_per_day"])
    controlled_area = zone_footprint_m2(cfg) + float(c["packhouse_area_m2"])
    hvac = float(e["hvac_kwh_per_m2_per_day"]) * controlled_area
    pumps = float(e["pumps_kwh_per_day"])
    refrigeration = float(e["packhouse_refrigeration_kwh_per_day"])
    controls = float(e["controls_kwh_per_day"])
    total = led + hvac + pumps + refrigeration + controls
    yield_per_kwp_day = float(cl["peak_sun_hours_per_day"]) * float(e["solar_performance_ratio"])
    solar = float(c["solar_array_kwp"]) * yield_per_kwp_day
    solar_fraction = min(1.0, solar / total) if total else 0.0
    critical = total * float(c["critical_load_fraction"])
    critical_kw = critical / 24.0
    battery_hours = float(c["battery_kwh"]) / critical_kw if critical_kw else float("inf")
    return {
        "canopy_m2": canopy,
        "controlled_area_m2": controlled_area,
        "led_kwh_per_day": led,
        "hvac_kwh_per_day": hvac,
        "pumps_kwh_per_day": pumps,
        "refrigeration_kwh_per_day": refrigeration,
        "controls_kwh_per_day": controls,
        "total_kwh_per_day": total,
        "solar_kwh_per_day": solar,
        "solar_fraction": solar_fraction,
        "kwh_per_kwp_per_day": yield_per_kwp_day,
        "critical_load_kwh_per_day": critical,
        "critical_load_kw_avg": critical_kw,
        "battery_autonomy_hours": battery_hours,
        "battery_vs_target": (
            "PASS" if battery_hours >= float(c["design_backup_autonomy_hours"]) else "GAP"
        ),
        "kwp_for_50pct_fraction": (total * 0.5 / yield_per_kwp_day) if yield_per_kwp_day else float("inf"),
    }