"""Deterministic JSON and Markdown renderers for the indoor simulation."""

import json


def render_indoor_json(result):
    """Serialize a simulation result without timestamps or platform state."""
    return json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |"]
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def _clock(minutes):
    hours, remainder = divmod(minutes, 60)
    return f"{hours:02d}:{remainder:02d}"


def _windows(windows):
    if not windows:
        return "none"
    return ", ".join(
        f"[{_clock(window['start_minute'])}, {_clock(window['end_minute'])})"
        for window in windows
    )


def _served_dli(profile):
    planned = profile["dli_mol_m2_day"]
    if planned == 0:
        return "0.000"
    requested = profile["requested_kwh"]
    if requested == 0:
        return "unresolved"
    return f"{planned * (profile['served_kwh'] / requested):.3f}"


def render_indoor_markdown(result):
    """Render the committed indoor report from a result, not from a clock."""
    scenario = result["scenario"]
    energy = result["energy_summary"]
    water = result["water_summary"]
    lines = [
        f"# {scenario['name']} - generated interval report",
        "",
        "To regenerate the reference fixture, run `PYTHONPATH=src python3 -m floridafarm simulate-day "
        "--config config/indoor-simulation.json --json-out "
        "docs/indoor-simulation.json --markdown-out docs/indoor-simulation-report.md`.",
        "Do not edit by hand: tests compare both committed outputs with fresh deterministic renders.",
        "",
        f"Status: {scenario['status']}. {scenario['source_label']}.",
        "Nothing here is a measurement, agronomic recommendation or performance claim.",
        "",
        "## 1. Synthetic scenario and bounds",
        "",
        _table(["Field", "Value"], [
            ["Scenario", scenario["name"]],
            ["Version", scenario["version"]],
            ["Location placeholder", scenario["location_placeholder"]],
            ["Intervals", result["interval_count"]],
            ["Minutes per interval", result["interval_minutes"]],
            ["Time convention", "[start_minute, end_minute); midnight = 1440; wrapped windows split at midnight"],
        ]),
        "",
        "The interval count is configurable from 1 through 96 and must divide 1440 exactly. "
        "All power is kW, energy is kWh, time is minutes or hours, water is litres, and "
        "lighting uses the explicitly labelled units below.",
        "",
        "## 2. Source-labelled lighting and DLI arithmetic",
        "",
        "DLI (mol/m2/day) = PPFD (umol/m2/s) x union photoperiod (h) x 3600 / 1,000,000. "
        "Power (kW) = area (m2) x PPFD / efficacy (umol/J) / 1000. Overlapping windows "
        "are counted once, not as additive light or energy. These are bookkeeping "
        "identities on invented inputs, not crop targets or measured crop responses.",
        "Served-equivalent DLI uses the energy dispatched to each lighting profile: "
        "scheduled DLI x (served kWh / requested kWh). It assumes constant "
        "efficacy and uniform light distribution. A positive DLI with requested energy "
        "rounded to zero has an unresolved service fraction.",
        "",
        _table(
            ["Crop/profile", "Area m2", "PPFD umol/m2/s", "Efficacy umol/J", "Power kW",
             "Union photoperiod h", "Scheduled DLI mol/m2/day", "Served-equivalent DLI mol/m2/day",
             "Requested kWh", "Shed kWh"],
            [[
                profile["crop"], f"{profile['area_m2']:.1f}",
                f"{profile['ppfd_umol_m2_s']:.1f}", f"{profile['efficacy_umol_j']:.2f}",
                f"{profile['lighting_power_kw']:.3f}", f"{profile['photoperiod_hours']:.3f}",
                f"{profile['dli_mol_m2_day']:.3f}",
                _served_dli(profile),
                f"{profile['requested_kwh']:.3f}",
                f"{profile['shed_kwh']:.3f}",
            ] for profile in result["lighting_profiles"]],
        ),
        "",
    ]
    for profile in result["lighting_profiles"]:
        lines.extend([
            f"- **{profile['crop']}** source: {profile['source_label']}. "
            f"Schedule: {_windows(profile['schedule'])}; gaps: {_windows(profile['gaps'])}; "
            f"overlap regions: {_windows(profile['overlap_windows'])}.",
        ])
    lines.extend([
        "",
        "## 3. Timer gaps, overlaps and midnight boundaries",
        "",
        _table(
            ["Timer", "Source", "Schedule", "Active h", "Gap windows", "Overlap windows", "Overlap h"],
            [[
                timer["name"], timer["source_label"], _windows(timer["schedule"]),
                f"{timer['active_hours']:.3f}", _windows(timer["gaps"]),
                _windows(timer["overlap_windows"]), f"{timer['overlap_hours']:.3f}",
            ] for timer in result["timer_audits"]],
        ),
        "",
        "Schedules use half-open windows. A start later than its end wraps through midnight. "
        "The simulator unions split windows before computing active minutes, so adjacent "
        "interval boundaries and overlapping timers cannot double-count load.",
        "",
        "## 4. Energy, conservation and recovery",
        "",
        "Dispatch policy: " + result["dispatch_policy"] + ". When grid is up, remaining "
        "load is grid-served and the battery can recover from surplus solar plus the bounded "
        "grid recovery input. When grid is down, noncritical load is shed even if solar "
        "remains; surplus solar can charge the battery. No real device is switched.",
        "",
        _table(["Item", "Value"], [
            ["Critical requested / served / shed (kWh)",
             f"{energy['requested_critical_kwh']:.3f} / {energy['served_critical_kwh']:.3f} / {energy['shed_critical_kwh']:.3f}"],
            ["Noncritical requested / served / shed (kWh)",
             f"{energy['requested_noncritical_kwh']:.3f} / {energy['served_noncritical_kwh']:.3f} / {energy['shed_noncritical_kwh']:.3f}"],
            ["Solar available / to loads / to battery / curtailed (kWh)",
             f"{energy['solar_available_kwh']:.3f} / {energy['solar_to_loads_kwh']:.3f} / "
             f"{energy['solar_to_battery_kwh']:.3f} / {energy['solar_curtailed_kwh']:.3f}"],
            ["Grid to loads / battery recovery (kWh)",
             f"{energy['grid_to_loads_kwh']:.3f} / {energy['grid_to_battery_kwh']:.3f}"],
            ["Battery to critical loads (kWh)", f"{energy['battery_to_loads_kwh']:.3f}"],
            ["Battery initial / final / minimum (kWh)",
             f"{energy['battery_initial_charge_kwh']:.3f} / {energy['battery_final_charge_kwh']:.3f} / "
             f"{energy['battery_minimum_charge_kwh']:.3f}"],
            ["Battery recovery target and result",
             f"{energy['battery_recovery_target_kwh']:.3f} kWh; "
             f"{'MET' if energy['battery_recovery_target_met'] else 'GAP'}"],
            ["Outage/conservation intervals", energy["outage_intervals"]],
            ["Maximum energy-balance residual (kWh)", f"{energy['energy_balance_max_residual_kwh']:.9f}"],
        ]),
        "",
        f"Honest negative: the synthetic outage leaves {energy['shed_critical_kwh']:.3f} kWh "
        f"of critical load and {energy['shed_noncritical_kwh']:.3f} kWh of noncritical load "
        "unserved. Reaching the later battery recovery target does not erase that outage shortfall.",
        "",
        _table(
            ["Interval", "Grid", "Solar kWh", "Critical served/requested kWh", "Critical shed kWh",
             "Noncritical served/requested kWh", "Noncritical shed kWh", "Battery end kWh", "Water end L"],
            [[
                f"{_clock(row['start_minute'])}-{_clock(row['end_minute'])}",
                "up" if row["grid_available"] else "DOWN",
                f"{row['solar_available_kwh']:.3f}",
                f"{row['served_critical_kwh']:.3f} / {row['requested_critical_kwh']:.3f}",
                f"{row['shed_critical_kwh']:.3f}",
                f"{row['served_noncritical_kwh']:.3f} / {row['requested_noncritical_kwh']:.3f}",
                f"{row['shed_noncritical_kwh']:.3f}", f"{row['battery_charge_end_kwh']:.3f}",
                f"{row['water_stock_end_l']:.3f}",
            ] for row in result["intervals"]],
        ),
        "",
        "Battery charge includes charge efficiency on inputs and discharge efficiency on "
        "outputs. Requested = served + shed, source-to-load energy = served energy, and "
        "solar = loads + battery + curtailment, within floating-point tolerance.",
        "",
        "## 5. Independent water stock ledger",
        "",
        "This interval ledger is deliberately separate from the existing daily water balance; "
        "it does not duplicate its crop-area uptake model or claim hydraulic coupling. "
        "Recovery and makeup enter stock before withdrawal, stock is capped at capacity, "
        "and unmet withdrawal is reported rather than creating negative stock.",
        "",
        _table(["Item", "Value"], [
            ["Initial / minimum end / final stock (L)",
             f"{water['initial_stock_l']:.3f} / {water['minimum_end_stock_l']:.3f} / {water['final_stock_l']:.3f}"],
            ["Requested / served withdrawal / shortfall (L)",
             f"{water['requested_withdrawal_l']:.3f} / {water['served_withdrawal_l']:.3f} / {water['shortfall_l']:.3f}"],
            ["Recovery / makeup / overflow (L)",
             f"{water['recovered_l']:.3f} / {water['makeup_l']:.3f} / {water['overflow_l']:.3f}"],
            ["Reserve / final minus reserve (L)",
             f"{water['reserve_l']:.3f} / {water['final_stock_minus_reserve_l']:.3f}"],
            ["Intervals ending below reserve", water["below_reserve_intervals"]],
        ]),
        "",
        "## 6. Chemical/nutrient inventory metadata only",
        "",
        "Each record keeps its explicit unit; no mass/volume conversion or cross-unit total "
        "is attempted. Reserve status is stock metadata, not a recommendation to apply, "
        "mix, dilute or dose anything. Negative stocks and ambiguous units are rejected.",
        "",
        _table(
            ["Record", "Stock", "Reserve", "Stock minus reserve", "Status", "Provenance", "Source"],
            [[
                record["name"], f"{record['stock_amount']:.3f} {record['unit']}",
                f"{record['reserve_amount']:.3f} {record['unit']}",
                f"{record['stock_minus_reserve']:.3f} {record['unit']}",
                record["reserve_status"], record["provenance"], record["source_label"],
            ] for record in result["chemical_inventory"]],
        ),
        "",
        "## 7. Exact scope and unvalidated assumptions",
        "",
    ])
    lines.extend(f"- {item}" for item in result["limitations"])
    lines.extend([
        "- Timer, PPFD, efficacy, power, outage, solar, battery, water and reserve values are invented "
        "software inputs; none is an equipment setpoint, site measurement or validated assumption.",
        "- The model does not estimate yield, crop health, nutrient uptake, food safety, economics, "
        "structural resilience or storm performance.",
        "",
        "---",
        "Synthetic indoor interval bookkeeping only. Regenerate both outputs after editing the fixture.",
        "",
    ])
    return "\n".join(lines)
