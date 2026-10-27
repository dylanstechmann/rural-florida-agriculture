"""Load and validate the rural-Florida scenario file.

Every value in the scenario file is a labeled placeholder assumption for
sizing a concept. Nothing here is a measurement of any real site, crop,
machine, weather station or market. Change the scenario file and
regenerate; the tests fail if the committed report no longer matches.
"""

import json
import math

ALLOWED_SYSTEMS = (
    "NFT multi-tier",
    "indoor stacked",
    "drip substrate",
    "ebb-and-flow",
    "screenhouse + protected enclosure",
)

REQUIRED_TOP = (
    "scenario",
    "climate",
    "campus",
    "crops",
    "water",
    "energy",
    "automation",
)


class ScenarioError(ValueError):
    """A scenario value is missing, mis-typed or out of range."""


def _num(section, key, path, lo=None, hi=None):
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScenarioError(f"{path}.{key} must be a number (got {value!r})")
    if not math.isfinite(value):
        raise ScenarioError(f"{path}.{key} must be finite (got {value!r})")
    if lo is not None and value < lo:
        raise ScenarioError(f"{path}.{key} must be >= {lo} (got {value!r})")
    if hi is not None and value > hi:
        raise ScenarioError(f"{path}.{key} must be <= {hi} (got {value!r})")
    return float(value)


def _int(section, key, path, lo=1):
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScenarioError(f"{path}.{key} must be an integer (got {value!r})")
    if value < lo:
        raise ScenarioError(f"{path}.{key} must be >= {lo} (got {value!r})")
    return value


def _str(section, key, path):
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioError(f"{path}.{key} must be a non-empty string (got {value!r})")
    return value


def _str_list(section, key, path):
    value = section.get(key)
    if not isinstance(value, list) or not value:
        raise ScenarioError(f"{path}.{key} must be a non-empty list (got {value!r})")
    for i, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ScenarioError(f"{path}.{key}[{i}] must be a non-empty string")
    return list(value)


def _bool(section, key, path):
    value = section.get(key)
    if not isinstance(value, bool):
        raise ScenarioError(f"{path}.{key} must be true or false (got {value!r})")
    return value


def validate_scenario(cfg):
    if not isinstance(cfg, dict):
        raise ScenarioError("scenario file must contain a JSON object")
    missing = [k for k in REQUIRED_TOP if k not in cfg]
    if missing:
        raise ScenarioError("missing required section(s): " + ", ".join(missing))
    unknown = [k for k in cfg if k not in REQUIRED_TOP]
    if unknown:
        raise ScenarioError("unknown section(s): " + ", ".join(unknown))

    _str(cfg["scenario"], "name", "scenario")
    _str(cfg["scenario"], "status", "scenario")
    _str(cfg["scenario"], "location_placeholder", "scenario")

    _num(cfg["climate"], "peak_sun_hours_per_day", "climate", lo=0.1, hi=24)
    _num(cfg["climate"], "annual_rainfall_mm", "climate", lo=0)
    _num(cfg["climate"], "design_hurricane_category_placeholder", "climate", lo=1, hi=5)
    _num(cfg["climate"], "freeze_events_per_year", "climate", lo=0)
    _num(cfg["climate"], "humid_season_months", "climate", lo=0, hi=12)

    campus = cfg["campus"]
    _int(campus, "zone_count", "campus")
    _int(campus, "tiers_per_zone", "campus")
    _num(campus, "lit_area_m2_per_zone", "campus", lo=1)
    _num(campus, "packhouse_area_m2", "campus", lo=1)
    _num(campus, "screenhouse_area_m2", "campus", lo=1)
    _num(campus, "roof_harvest_area_m2", "campus", lo=0)
    _num(campus, "solar_array_kwp", "campus", lo=0)
    _num(campus, "battery_kwh", "campus", lo=0.1)
    _num(campus, "critical_load_fraction", "campus", lo=0.01, hi=1)
    _num(campus, "raised_floor_height_m", "campus", lo=0)
    _num(campus, "design_backup_autonomy_hours", "campus", lo=0.1)

    water = cfg["water"]
    _num(water, "uptake_l_per_m2_per_day", "water", lo=0.1)
    _num(water, "screenhouse_uptake_l_per_m2_per_day", "water", lo=0)
    _num(water, "recirculation_fraction", "water", lo=0, hi=0.999)
    _num(water, "condensate_recovery_l_per_day", "water", lo=0)
    _num(water, "rain_harvest_efficiency", "water", lo=0, hi=1)
    _num(water, "irrigation_backup_days", "water", lo=1)
    _str(water, "disinfection_stage", "water")
    _str(water, "purge_handling", "water")

    energy = cfg["energy"]
    _num(energy, "led_watts_per_m2_lit", "energy", lo=1)
    _num(energy, "lit_hours_per_day", "energy", lo=0.1, hi=24)
    _num(energy, "hvac_kwh_per_m2_per_day", "energy", lo=0)
    _num(energy, "pumps_kwh_per_day", "energy", lo=0)
    _num(energy, "packhouse_refrigeration_kwh_per_day", "energy", lo=0)
    _num(energy, "controls_kwh_per_day", "energy", lo=0)
    _num(energy, "solar_performance_ratio", "energy", lo=0.01, hi=1)

    crops = cfg["crops"]
    if not isinstance(crops, list) or not crops:
        raise ScenarioError("crops must be a non-empty list")
    indoor_area = 0.0
    screen_area = 0.0
    for i, crop in enumerate(crops):
        path = f"crops[{i}]"
        if not isinstance(crop, dict):
            raise ScenarioError(f"{path} must be an object")
        _str(crop, "name", path)
        system = _str(crop, "system", path)
        if system not in ALLOWED_SYSTEMS:
            raise ScenarioError(
                f"{path}.system must be one of {sorted(ALLOWED_SYSTEMS)} (got {system!r})"
            )
        area = _num(crop, "area_m2", path, lo=0.1)
        _num(crop, "cycles_per_year", path, lo=0.1)
        _num(crop, "kg_per_m2_per_cycle", path, lo=0.05)
        if system == "screenhouse + protected enclosure":
            screen_area += area
        else:
            indoor_area += area

    canopy = (
        campus["zone_count"] * campus["lit_area_m2_per_zone"] * campus["tiers_per_zone"]
    )
    if indoor_area > canopy + 1e-9:
        raise ScenarioError(
            f"indoor crop area {indoor_area:.1f} m2 exceeds canopy area {canopy:.1f} m2"
        )
    if screen_area > campus["screenhouse_area_m2"] + 1e-9:
        raise ScenarioError(
            f"screenhouse crop area {screen_area:.1f} m2 exceeds screenhouse "
            f"{campus['screenhouse_area_m2']:.1f} m2"
        )

    automation = cfg["automation"]
    _bool(automation, "local_first_control", "automation")
    _str_list(automation, "n_plus_1", "automation")
    _str_list(automation, "storm_mode_checklist", "automation")
    _str_list(automation, "qualification_ladder", "automation")
    return cfg


def load_scenario(path):
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    validate_scenario(cfg)
    return cfg