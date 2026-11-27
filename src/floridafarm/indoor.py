"""Bounded, deterministic indoor-grow interval bookkeeping.

This module is a NON-OPERATIONAL simulation. It performs arithmetic on a
synthetic fixture only: it has no actuator, hardware, network or clock
interface. Lighting values are not crop recommendations, and chemical
inventory records contain stock/provenance metadata only, never dosing or
mixing instructions.
"""

import json
import math

MINUTES_PER_DAY = 24 * 60
MAX_INTERVALS = 96
ALLOWED_UNITS = ("kg", "g", "L", "mL")
CRITICALITIES = ("critical", "noncritical")

LIMITATIONS = [
    "NON-OPERATIONAL synthetic arithmetic; no actuator, hardware, network or real-time clock interface.",
    "No crop-specific nutrient dosing or mixing recommendation and no measured crop-response claim.",
    "No food-safety claim, storm-resilience certification, engineering design or site validation.",
    "The arid location is a generic concept, not measured Iran site data.",
    "Plant base editing is a separate trait-evidence topic, not modeled here and not an environmental-control substitute.",
]


class IndoorScenarioError(ValueError):
    """An indoor simulation value is missing, ambiguous or out of range."""


def _object(value, path):
    if not isinstance(value, dict):
        raise IndoorScenarioError(f"{path} must be an object")
    return value


def _keys(section, required, path):
    _object(section, path)
    required = set(required)
    missing = sorted(required - set(section))
    unknown = sorted(set(section) - required)
    if missing:
        raise IndoorScenarioError(f"{path} missing key(s): {', '.join(missing)}")
    if unknown:
        raise IndoorScenarioError(f"{path} unknown key(s): {', '.join(unknown)}")


def _string(section, key, path):
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise IndoorScenarioError(f"{path}.{key} must be a non-empty string")
    return value


def _number(section, key, path, lo=None, hi=None, lo_open=False):
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IndoorScenarioError(f"{path}.{key} must be a number (got {value!r})")
    if not math.isfinite(value):
        raise IndoorScenarioError(f"{path}.{key} must be finite (got {value!r})")
    if lo is not None and (value <= lo if lo_open else value < lo):
        operator = ">" if lo_open else ">="
        raise IndoorScenarioError(f"{path}.{key} must be {operator} {lo} (got {value!r})")
    if hi is not None and value > hi:
        raise IndoorScenarioError(f"{path}.{key} must be <= {hi} (got {value!r})")
    return float(value)


def _integer(section, key, path, lo=1, hi=None):
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise IndoorScenarioError(f"{path}.{key} must be an integer (got {value!r})")
    if value < lo or (hi is not None and value > hi):
        upper = f" and <= {hi}" if hi is not None else ""
        raise IndoorScenarioError(f"{path}.{key} must be >= {lo}{upper} (got {value!r})")
    return value


def _criticality(section, path):
    value = _string(section, "criticality", path)
    if value not in CRITICALITIES:
        raise IndoorScenarioError(f"{path}.criticality must be one of {CRITICALITIES}")
    return value


def _schedule(section, path):
    windows = section.get("schedule")
    if not isinstance(windows, list) or not windows:
        raise IndoorScenarioError(f"{path}.schedule must be a non-empty list")
    normalized = []
    for i, window in enumerate(windows):
        wpath = f"{path}.schedule[{i}]"
        _keys(window, ("start_minute", "end_minute"), wpath)
        start = _integer(window, "start_minute", wpath, lo=0, hi=MINUTES_PER_DAY - 1)
        end = _integer(window, "end_minute", wpath, lo=0, hi=MINUTES_PER_DAY)
        if start == end:
            raise IndoorScenarioError(
                f"{wpath} has ambiguous zero/full-day bounds; use 0 and 1440 for a full day"
            )
        normalized.append({"start_minute": start, "end_minute": end})
    return normalized


def _series(section, key, path, count, lo=0.0):
    values = section.get(key)
    if not isinstance(values, list) or len(values) != count:
        raise IndoorScenarioError(f"{path}.{key} must contain exactly {count} numbers")
    output = []
    for i, value in enumerate(values):
        item = {key: value}
        output.append(_number(item, key, f"{path}[{i}]", lo=lo))
    return output


def _grid_series(section, count):
    values = section.get("available_by_interval")
    if not isinstance(values, list) or len(values) != count:
        raise IndoorScenarioError(
            f"grid.available_by_interval must contain exactly {count} booleans"
        )
    for i, value in enumerate(values):
        if not isinstance(value, bool):
            raise IndoorScenarioError(f"grid.available_by_interval[{i}] must be true or false")
    return list(values)


def validate_indoor_scenario(cfg):
    """Validate strict units, bounded intervals and all synthetic inputs."""
    _object(cfg, "indoor scenario")
    top = (
        "scenario", "intervals", "lighting_profiles", "timers",
        "continuous_loads", "grid", "solar", "battery", "water",
        "chemical_inventory",
    )
    _keys(cfg, top, "indoor scenario")
    _keys(
        cfg["scenario"],
        ("name", "version", "status", "location_placeholder", "source_label"),
        "scenario",
    )
    for key in ("name", "version", "status", "location_placeholder", "source_label"):
        _string(cfg["scenario"], key, "scenario")

    _keys(cfg["intervals"], ("count",), "intervals")
    count = _integer(cfg["intervals"], "count", "intervals", lo=1, hi=MAX_INTERVALS)
    if MINUTES_PER_DAY % count:
        raise IndoorScenarioError("intervals.count must divide 1440 into equal whole-minute intervals")

    profiles = cfg["lighting_profiles"]
    if not isinstance(profiles, list) or not profiles:
        raise IndoorScenarioError("lighting_profiles must be a non-empty list")
    crop_names = set()
    for i, profile in enumerate(profiles):
        path = f"lighting_profiles[{i}]"
        _keys(
            profile,
            ("crop", "area_m2", "ppfd_umol_m2_s", "efficacy_umol_j",
             "criticality", "source_label", "schedule"),
            path,
        )
        crop = _string(profile, "crop", path)
        if crop in crop_names:
            raise IndoorScenarioError(f"duplicate lighting crop name: {crop!r}")
        crop_names.add(crop)
        _number(profile, "area_m2", path, lo=0, lo_open=True)
        _number(profile, "ppfd_umol_m2_s", path, lo=0)
        _number(profile, "efficacy_umol_j", path, lo=0, lo_open=True)
        _string(profile, "source_label", path)
        _criticality(profile, path)
        _schedule(profile, path)

    timers = cfg["timers"]
    if not isinstance(timers, list):
        raise IndoorScenarioError("timers must be a list")
    for i, timer in enumerate(timers):
        path = f"timers[{i}]"
        _keys(timer, ("name", "power_kw", "criticality", "source_label", "schedule"), path)
        _string(timer, "name", path)
        _number(timer, "power_kw", path, lo=0)
        _criticality(timer, path)
        _string(timer, "source_label", path)
        _schedule(timer, path)

    continuous = cfg["continuous_loads"]
    if not isinstance(continuous, list):
        raise IndoorScenarioError("continuous_loads must be a list")
    for i, load in enumerate(continuous):
        path = f"continuous_loads[{i}]"
        _keys(load, ("name", "power_kw", "criticality", "source_label"), path)
        _string(load, "name", path)
        _number(load, "power_kw", path, lo=0)
        _criticality(load, path)
        _string(load, "source_label", path)

    _keys(cfg["grid"], ("available_by_interval",), "grid")
    _grid_series(cfg["grid"], count)
    _keys(cfg["solar"], ("power_kw_by_interval",), "solar")
    _series(cfg["solar"], "power_kw_by_interval", "solar", count)

    battery = cfg["battery"]
    battery_fields = (
        "capacity_kwh", "initial_charge_kwh", "minimum_charge_kwh",
        "recovery_target_charge_kwh", "maximum_charge_power_kw",
        "maximum_discharge_power_kw", "charge_efficiency",
        "discharge_efficiency", "grid_recovery_power_kw",
    )
    _keys(battery, battery_fields, "battery")
    capacity = _number(battery, "capacity_kwh", "battery", lo=0, lo_open=True)
    minimum = _number(battery, "minimum_charge_kwh", "battery", lo=0, hi=capacity)
    initial = _number(battery, "initial_charge_kwh", "battery", lo=0, hi=capacity)
    target = _number(battery, "recovery_target_charge_kwh", "battery", lo=0, hi=capacity)
    if initial < minimum:
        raise IndoorScenarioError("battery.initial_charge_kwh must be >= minimum_charge_kwh")
    if target < minimum:
        raise IndoorScenarioError("battery.recovery_target_charge_kwh must be >= minimum_charge_kwh")
    _number(battery, "maximum_charge_power_kw", "battery", lo=0)
    _number(battery, "maximum_discharge_power_kw", "battery", lo=0)
    _number(battery, "charge_efficiency", "battery", lo=0, hi=1, lo_open=True)
    _number(battery, "discharge_efficiency", "battery", lo=0, hi=1, lo_open=True)
    _number(battery, "grid_recovery_power_kw", "battery", lo=0)

    water = cfg["water"]
    water_fields = (
        "capacity_l", "initial_stock_l", "reserve_l", "withdrawal_l_per_hour",
        "recovery_l_per_hour_by_interval", "makeup_l_per_hour_by_interval",
    )
    _keys(water, water_fields, "water")
    water_capacity = _number(water, "capacity_l", "water", lo=0, lo_open=True)
    _number(water, "initial_stock_l", "water", lo=0, hi=water_capacity)
    _number(water, "reserve_l", "water", lo=0, hi=water_capacity)
    _number(water, "withdrawal_l_per_hour", "water", lo=0)
    _series(water, "recovery_l_per_hour_by_interval", "water", count)
    _series(water, "makeup_l_per_hour_by_interval", "water", count)

    inventory = cfg["chemical_inventory"]
    if not isinstance(inventory, list):
        raise IndoorScenarioError("chemical_inventory must be a list")
    inventory_names = set()
    for i, record in enumerate(inventory):
        path = f"chemical_inventory[{i}]"
        _keys(
            record,
            ("name", "stock_amount", "reserve_amount", "unit", "provenance", "source_label"),
            path,
        )
        name = _string(record, "name", path)
        if name in inventory_names:
            raise IndoorScenarioError(f"duplicate chemical inventory name: {name!r}")
        inventory_names.add(name)
        _number(record, "stock_amount", path, lo=0)
        _number(record, "reserve_amount", path, lo=0)
        unit = _string(record, "unit", path)
        if unit not in ALLOWED_UNITS:
            raise IndoorScenarioError(
                f"{path}.unit is ambiguous or unsupported; use one of {ALLOWED_UNITS}"
            )
        _string(record, "provenance", path)
        _string(record, "source_label", path)
    return cfg


def load_indoor_scenario(path):
    """Load a UTF-8 JSON fixture without consulting any external state."""
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    validate_indoor_scenario(cfg)
    return cfg


def _split_window(window):
    start, end = window["start_minute"], window["end_minute"]
    if start < end:
        return [(start, end)]
    return [(start, MINUTES_PER_DAY), (0, end)]


def _merge(intervals):
    merged = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _window_dicts(intervals):
    return [{"start_minute": start, "end_minute": end} for start, end in intervals]


def _timer_audit(schedule):
    split = [part for window in schedule for part in _split_window(window)]
    union = _merge(split)
    union_minutes = sum(end - start for start, end in union)
    scheduled_minutes = sum(end - start for start, end in split)
    gaps = []
    cursor = 0
    for start, end in union:
        if start > cursor:
            gaps.append((cursor, start))
        cursor = end
    if cursor < MINUTES_PER_DAY:
        gaps.append((cursor, MINUTES_PER_DAY))
    pairwise_overlaps = []
    for i, (a_start, a_end) in enumerate(split):
        for b_start, b_end in split[i + 1:]:
            start, end = max(a_start, b_start), min(a_end, b_end)
            if start < end:
                pairwise_overlaps.append((start, end))
    return {
        "scheduled_window_hours": scheduled_minutes / 60.0,
        "active_hours": union_minutes / 60.0,
        "overlap_hours": (scheduled_minutes - union_minutes) / 60.0,
        "gaps": _window_dicts(gaps),
        "overlap_windows": _window_dicts(_merge(pairwise_overlaps)),
        "union_windows": _window_dicts(union),
    }


def _active_minutes(schedule, interval_start, interval_end):
    union = _merge([part for window in schedule for part in _split_window(window)])
    return sum(
        max(0, min(end, interval_end) - max(start, interval_start))
        for start, end in union
    )


def _lighting_power_kw(profile):
    return (
        float(profile["area_m2"])
        * float(profile["ppfd_umol_m2_s"])
        / float(profile["efficacy_umol_j"])
        / 1000.0
    )


def _load_specs(cfg):
    specs = []
    for profile in cfg["lighting_profiles"]:
        specs.append({
            "name": f"lighting: {profile['crop']}",
            "kind": "lighting",
            "criticality": profile["criticality"],
            "source_label": profile["source_label"],
            "power_kw": _lighting_power_kw(profile),
            "schedule": profile["schedule"],
        })
    for timer in cfg["timers"]:
        specs.append({
            "name": f"timer: {timer['name']}",
            "kind": "timer",
            "criticality": timer["criticality"],
            "source_label": timer["source_label"],
            "power_kw": float(timer["power_kw"]),
            "schedule": timer["schedule"],
        })
    for load in cfg["continuous_loads"]:
        specs.append({
            "name": f"continuous: {load['name']}",
            "kind": "continuous",
            "criticality": load["criticality"],
            "source_label": load["source_label"],
            "power_kw": float(load["power_kw"]),
            "schedule": None,
        })
    return specs


def _allocate(rows, criticality, served):
    selected = [row for row in rows if row["criticality"] == criticality]
    requested = sum(row["requested_kwh"] for row in selected)
    ratio = min(1.0, served / requested) if requested else 0.0
    for row in selected:
        row["served_kwh"] = row["requested_kwh"] * ratio
        row["shed_kwh"] = row["requested_kwh"] - row["served_kwh"]


def _clean(value):
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, float):
        rounded = round(value, 9)
        return 0.0 if rounded == 0 else rounded
    return value


def simulate_day(cfg, *, makeup_outage=None):
    """Simulate one bounded day using only the supplied synthetic mapping.

    Dispatch order is solar -> critical loads -> noncritical loads (grid up)
    -> battery charging. With grid down, noncritical loads are shed and the
    battery serves only critical loads. Same-class shortfalls are allocated
    proportionally. Battery charging then recovers from surplus solar and,
    when grid is available, up to the explicit grid recovery power limit.
    """
    validate_indoor_scenario(cfg)
    outage_schedule = []
    if makeup_outage is not None:
        if not isinstance(makeup_outage, (tuple, list)) or len(makeup_outage) != 2:
            raise IndoorScenarioError("makeup_outage requires two minute boundaries")
        window = {"start_minute": makeup_outage[0], "end_minute": makeup_outage[1]}
        outage_schedule = _schedule({"schedule": [window]}, "makeup_outage")
    count = cfg["intervals"]["count"]
    interval_minutes = MINUTES_PER_DAY // count
    duration_h = interval_minutes / 60.0
    specs = _load_specs(cfg)
    battery_cfg = cfg["battery"]
    water_cfg = cfg["water"]
    charge = float(battery_cfg["initial_charge_kwh"])
    initial_charge = charge
    water_stock = float(water_cfg["initial_stock_l"])
    initial_water = water_stock
    intervals = []
    totals = {
        key: 0.0 for key in (
            "requested_critical_kwh", "requested_noncritical_kwh",
            "served_critical_kwh", "served_noncritical_kwh",
            "shed_critical_kwh", "shed_noncritical_kwh",
            "solar_available_kwh", "solar_to_loads_kwh", "solar_to_battery_kwh",
            "solar_curtailed_kwh", "grid_to_loads_kwh", "grid_to_battery_kwh",
            "battery_to_loads_kwh",
        )
    }
    water_totals = {
        key: 0.0 for key in (
            "requested_withdrawal_l", "served_withdrawal_l", "shortfall_l",
            "recovered_l", "makeup_l", "overflow_l",
        )
    }
    load_total_map = {
        spec["name"]: {
            "name": spec["name"], "kind": spec["kind"],
            "criticality": spec["criticality"], "source_label": spec["source_label"],
            "requested_kwh": 0.0, "served_kwh": 0.0, "shed_kwh": 0.0,
        }
        for spec in specs
    }
    maximum_residual = 0.0

    for index in range(count):
        start = index * interval_minutes
        end = start + interval_minutes
        rows = []
        for spec in specs:
            active = (
                _active_minutes(spec["schedule"], start, end)
                if spec["schedule"] is not None else interval_minutes
            )
            requested = spec["power_kw"] * active / 60.0
            rows.append({
                "name": spec["name"], "kind": spec["kind"],
                "criticality": spec["criticality"], "source_label": spec["source_label"],
                "active_minutes": active, "requested_kwh": requested,
                "served_kwh": 0.0, "shed_kwh": 0.0,
            })
        critical_requested = sum(row["requested_kwh"] for row in rows if row["criticality"] == "critical")
        noncritical_requested = sum(
            row["requested_kwh"] for row in rows if row["criticality"] == "noncritical"
        )
        grid_available = cfg["grid"]["available_by_interval"][index]
        solar_available = float(cfg["solar"]["power_kw_by_interval"][index]) * duration_h
        solar_remaining = solar_available

        critical_solar = min(critical_requested, solar_remaining)
        solar_remaining -= critical_solar
        critical_served = critical_solar
        noncritical_served = 0.0
        grid_to_loads = 0.0
        battery_to_loads = 0.0

        if grid_available:
            noncritical_solar = min(noncritical_requested, solar_remaining)
            solar_remaining -= noncritical_solar
            noncritical_served = noncritical_solar
            grid_to_loads = (
                critical_requested - critical_served
                + noncritical_requested - noncritical_served
            )
            critical_served = critical_requested
            noncritical_served = noncritical_requested
        else:
            discharge_limit = float(battery_cfg["maximum_discharge_power_kw"]) * duration_h
            stored_available = max(
                0.0, charge - float(battery_cfg["minimum_charge_kwh"])
            )
            battery_output_available = min(
                discharge_limit,
                stored_available * float(battery_cfg["discharge_efficiency"]),
            )
            battery_to_loads = min(critical_requested - critical_served, battery_output_available)
            critical_served += battery_to_loads
            charge -= battery_to_loads / float(battery_cfg["discharge_efficiency"])

        charge_efficiency = float(battery_cfg["charge_efficiency"])
        charge_input_capacity = min(
            float(battery_cfg["maximum_charge_power_kw"]) * duration_h,
            max(0.0, float(battery_cfg["capacity_kwh"]) - charge) / charge_efficiency,
        )
        solar_to_battery = min(solar_remaining, charge_input_capacity)
        solar_remaining -= solar_to_battery
        charge += solar_to_battery * charge_efficiency

        grid_to_battery = 0.0
        if grid_available:
            target_input = max(
                0.0, float(battery_cfg["recovery_target_charge_kwh"]) - charge
            ) / charge_efficiency
            grid_to_battery = min(
                float(battery_cfg["grid_recovery_power_kw"]) * duration_h,
                charge_input_capacity - solar_to_battery,
                target_input,
            )
            charge += grid_to_battery * charge_efficiency

        critical_shed = critical_requested - critical_served
        noncritical_shed = noncritical_requested - noncritical_served
        _allocate(rows, "critical", critical_served)
        _allocate(rows, "noncritical", noncritical_served)
        solar_to_loads = critical_solar + (
            noncritical_solar if grid_available else 0.0
        )
        served = critical_served + noncritical_served
        requested = critical_requested + noncritical_requested
        residual = max(
            abs(requested - served - critical_shed - noncritical_shed),
            abs(solar_to_loads + grid_to_loads + battery_to_loads - served),
            abs(solar_available - solar_to_loads - solar_to_battery - solar_remaining),
            abs(
                charge - initial_charge
                - sum(row["solar_to_battery_kwh"] + row["grid_to_battery_kwh"] for row in intervals)
                * charge_efficiency
                - (solar_to_battery + grid_to_battery) * charge_efficiency
                + (
                    sum(row["battery_to_loads_kwh"] for row in intervals) + battery_to_loads
                ) / float(battery_cfg["discharge_efficiency"])
            ),
        )
        maximum_residual = max(maximum_residual, residual)

        water_recovery = float(water_cfg["recovery_l_per_hour_by_interval"][index]) * duration_h
        outage_minutes = _active_minutes(outage_schedule, start, end)
        makeup_hours = (interval_minutes - outage_minutes) / 60.0
        water_makeup = float(water_cfg["makeup_l_per_hour_by_interval"][index]) * makeup_hours
        water_requested = float(water_cfg["withdrawal_l_per_hour"]) * duration_h
        water_available = water_stock + water_recovery + water_makeup
        water_served = min(water_requested, water_available)
        water_after = water_available - water_served
        water_end = min(float(water_cfg["capacity_l"]), water_after)
        water_overflow = water_after - water_end

        interval = {
            "index": index,
            "start_minute": start,
            "end_minute": end,
            "duration_hours": duration_h,
            "grid_available": grid_available,
            "conservation_mode": not grid_available,
            "requested_critical_kwh": critical_requested,
            "requested_noncritical_kwh": noncritical_requested,
            "served_critical_kwh": critical_served,
            "served_noncritical_kwh": noncritical_served,
            "shed_critical_kwh": critical_shed,
            "shed_noncritical_kwh": noncritical_shed,
            "solar_available_kwh": solar_available,
            "solar_to_loads_kwh": solar_to_loads,
            "solar_to_battery_kwh": solar_to_battery,
            "solar_curtailed_kwh": solar_remaining,
            "grid_to_loads_kwh": grid_to_loads,
            "grid_to_battery_kwh": grid_to_battery,
            "battery_to_loads_kwh": battery_to_loads,
            "battery_charge_start_kwh": (
                intervals[-1]["battery_charge_end_kwh"] if intervals else initial_charge
            ),
            "battery_charge_end_kwh": charge,
            "water_stock_start_l": water_stock,
            "water_recovered_l": water_recovery,
            "water_makeup_l": water_makeup,
            "water_requested_withdrawal_l": water_requested,
            "water_served_withdrawal_l": water_served,
            "water_shortfall_l": water_requested - water_served,
            "water_overflow_l": water_overflow,
            "water_stock_end_l": water_end,
            "water_below_reserve": water_end < float(water_cfg["reserve_l"]),
            "loads": rows,
        }
        intervals.append(interval)

        local_totals = {
            "requested_critical_kwh": critical_requested,
            "requested_noncritical_kwh": noncritical_requested,
            "served_critical_kwh": critical_served,
            "served_noncritical_kwh": noncritical_served,
            "shed_critical_kwh": critical_shed,
            "shed_noncritical_kwh": noncritical_shed,
            "solar_available_kwh": solar_available,
            "solar_to_loads_kwh": solar_to_loads,
            "solar_to_battery_kwh": solar_to_battery,
            "solar_curtailed_kwh": solar_remaining,
            "grid_to_loads_kwh": grid_to_loads,
            "grid_to_battery_kwh": grid_to_battery,
            "battery_to_loads_kwh": battery_to_loads,
        }
        for key, value in local_totals.items():
            totals[key] += value
        water_values = {
            "requested_withdrawal_l": water_requested,
            "served_withdrawal_l": water_served,
            "shortfall_l": water_requested - water_served,
            "recovered_l": water_recovery,
            "makeup_l": water_makeup,
            "overflow_l": water_overflow,
        }
        for key, value in water_values.items():
            water_totals[key] += value
        for row in rows:
            aggregate = load_total_map[row["name"]]
            aggregate["requested_kwh"] += row["requested_kwh"]
            aggregate["served_kwh"] += row["served_kwh"]
            aggregate["shed_kwh"] += row["shed_kwh"]
        water_stock = water_end

    lighting = []
    load_totals = list(load_total_map.values())
    for profile in cfg["lighting_profiles"]:
        audit = _timer_audit(profile["schedule"])
        energy = load_total_map[f"lighting: {profile['crop']}"]
        lighting.append({
            "crop": profile["crop"],
            "source_label": profile["source_label"],
            "area_m2": float(profile["area_m2"]),
            "ppfd_umol_m2_s": float(profile["ppfd_umol_m2_s"]),
            "efficacy_umol_j": float(profile["efficacy_umol_j"]),
            "lighting_power_kw": _lighting_power_kw(profile),
            "criticality": profile["criticality"],
            "photoperiod_hours": audit["active_hours"],
            "dli_mol_m2_day": (
                float(profile["ppfd_umol_m2_s"]) * audit["active_hours"] * 3600.0 / 1_000_000.0
            ),
            "schedule": [dict(window) for window in profile["schedule"]],
            **audit,
            "requested_kwh": energy["requested_kwh"],
            "served_kwh": energy["served_kwh"],
            "shed_kwh": energy["shed_kwh"],
        })
    timer_audits = []
    for timer in cfg["timers"]:
        energy = load_total_map[f"timer: {timer['name']}"]
        timer_audits.append({
            "name": timer["name"],
            "source_label": timer["source_label"],
            "criticality": timer["criticality"],
            "power_kw": float(timer["power_kw"]),
            "schedule": [dict(window) for window in timer["schedule"]],
            **_timer_audit(timer["schedule"]),
            "requested_kwh": energy["requested_kwh"],
            "served_kwh": energy["served_kwh"],
            "shed_kwh": energy["shed_kwh"],
        })

    totals["battery_initial_charge_kwh"] = initial_charge
    totals["battery_final_charge_kwh"] = charge
    totals["battery_minimum_charge_kwh"] = float(battery_cfg["minimum_charge_kwh"])
    totals["battery_recovery_target_kwh"] = float(battery_cfg["recovery_target_charge_kwh"])
    totals["battery_recovery_target_met"] = (
        charge + 1e-9 >= float(battery_cfg["recovery_target_charge_kwh"])
    )
    totals["energy_balance_max_residual_kwh"] = maximum_residual
    totals["outage_intervals"] = sum(not row["grid_available"] for row in intervals)
    totals["conservation_intervals"] = totals["outage_intervals"]

    water_totals.update({
        "initial_stock_l": initial_water,
        "final_stock_l": water_stock,
        "minimum_end_stock_l": min(row["water_stock_end_l"] for row in intervals),
        "reserve_l": float(water_cfg["reserve_l"]),
        "final_stock_minus_reserve_l": water_stock - float(water_cfg["reserve_l"]),
        "below_reserve_intervals": sum(row["water_below_reserve"] for row in intervals),
    })
    chemicals = []
    for record in cfg["chemical_inventory"]:
        difference = float(record["stock_amount"]) - float(record["reserve_amount"])
        chemicals.append({
            "name": record["name"],
            "stock_amount": float(record["stock_amount"]),
            "reserve_amount": float(record["reserve_amount"]),
            "unit": record["unit"],
            "stock_minus_reserve": difference,
            "reserve_status": "BELOW_RESERVE" if difference < 0 else "AT_OR_ABOVE_RESERVE",
            "provenance": record["provenance"],
            "source_label": record["source_label"],
        })

    result = {
        "schema_version": 1,
        "scenario": dict(cfg["scenario"]),
        "interval_count": count,
        "interval_minutes": interval_minutes,
        "dispatch_policy": (
            "solar first; critical before noncritical; grid-down noncritical shedding; "
            "battery for critical loads only; proportional same-class shortfall allocation"
        ),
        "lighting_profiles": lighting,
        "timer_audits": timer_audits,
        "energy_summary": totals,
        "load_totals": load_totals,
        "water_summary": water_totals,
        "chemical_inventory": chemicals,
        "intervals": intervals,
        "limitations": list(LIMITATIONS),
    }
    if outage_schedule:
        result["scenario"]["source_label"] += (
            f". Scheduled makeup water interrupted from minute {makeup_outage[0]} "
            f"to minute {makeup_outage[1]} (end excluded, wrapping at midnight when needed)"
        )
    return _clean(result)
