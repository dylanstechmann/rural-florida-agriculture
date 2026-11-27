# Synthetic arid indoor farm interval fixture - generated interval report

To regenerate the reference fixture, run `PYTHONPATH=src python3 -m floridafarm simulate-day --config config/indoor-simulation.json --json-out docs/indoor-simulation.json --markdown-out docs/indoor-simulation-report.md`.
Do not edit by hand: tests compare both committed outputs with fresh deterministic renders.

Status: NON-OPERATIONAL synthetic simulation with unvalidated assumptions; not a design or recommendation. agent-drafted synthetic software fixture; every value is invented.
Nothing here is a measurement, agronomic recommendation or performance claim.

## 1. Synthetic scenario and bounds

| Field | Value |
|---|---|
| Scenario | Synthetic arid indoor farm interval fixture |
| Version | 2026-11-26 |
| Location placeholder | generic arid vertical-farm concept; no real site and no measured Iran site data |
| Intervals | 24 |
| Minutes per interval | 60 |
| Time convention | [start_minute, end_minute); midnight = 1440; wrapped windows split at midnight |

The interval count is configurable from 1 through 96 and must divide 1440 exactly. All power is kW, energy is kWh, time is minutes or hours, water is litres, and lighting uses the explicitly labelled units below.

## 2. Source-labelled lighting and DLI arithmetic

DLI (mol/m2/day) = PPFD (umol/m2/s) x union photoperiod (h) x 3600 / 1,000,000. Power (kW) = area (m2) x PPFD / efficacy (umol/J) / 1000. Overlapping windows are counted once, not as additive light or energy. These are bookkeeping identities on invented inputs, not crop targets or measured crop responses.
Served-equivalent DLI uses the energy dispatched to each lighting profile: scheduled DLI x (served kWh / requested kWh). It assumes constant efficacy and uniform light distribution. A positive DLI with requested energy rounded to zero has an unresolved service fraction.

| Crop/profile | Area m2 | PPFD umol/m2/s | Efficacy umol/J | Power kW | Union photoperiod h | Scheduled DLI mol/m2/day | Served-equivalent DLI mol/m2/day | Requested kWh | Shed kWh |
|---|---|---|---|---|---|---|---|---|---|
| leafy greens (synthetic profile) | 120.0 | 200.0 | 2.50 | 9.600 | 12.000 | 8.640 | 8.640 | 115.200 | 0.000 |
| basil (synthetic profile) | 80.0 | 180.0 | 2.40 | 6.000 | 13.000 | 8.424 | 6.480 | 78.000 | 18.000 |

- **leafy greens (synthetic profile)** source: synthetic lighting arithmetic fixture; not an agronomic target or measured crop response. Schedule: [06:00, 18:00); gaps: [00:00, 06:00), [18:00, 24:00); overlap regions: none.
- **basil (synthetic profile)** source: synthetic lighting arithmetic fixture; not an agronomic target or measured crop response. Schedule: [18:00, 06:00), [05:00, 07:00); gaps: [07:00, 18:00); overlap regions: [05:00, 06:00).

## 3. Timer gaps, overlaps and midnight boundaries

| Timer | Source | Schedule | Active h | Gap windows | Overlap windows | Overlap h |
|---|---|---|---|---|---|---|
| airflow boost (synthetic timer) | synthetic timer fixture with deliberate gaps, overlaps and midnight wrap | [00:00, 04:00), [03:00, 05:00), [20:00, 01:00) | 9.000 | [05:00, 20:00) | [00:00, 01:00), [03:00, 04:00) | 2.000 |

Schedules use half-open windows. A start later than its end wraps through midnight. The simulator unions split windows before computing active minutes, so adjacent interval boundaries and overlapping timers cannot double-count load.

## 4. Energy, conservation and recovery

Dispatch policy: solar first; critical before noncritical; grid-down noncritical shedding; battery for critical loads only; proportional same-class shortfall allocation. When grid is up, remaining load is grid-served and the battery can recover from surplus solar plus the bounded grid recovery input. When grid is down, noncritical load is shed even if solar remains; surplus solar can charge the battery. No real device is switched.

| Item | Value |
|---|---|
| Critical requested / served / shed (kWh) | 360.000 / 342.000 / 18.000 |
| Noncritical requested / served / shed (kWh) | 283.200 / 250.200 / 33.000 |
| Solar available / to loads / to battery / curtailed (kWh) | 200.000 / 172.800 / 27.200 / 0.000 |
| Grid to loads / battery recovery (kWh) | 392.400 / 67.537 |
| Battery to critical loads (kWh) | 27.000 |
| Battery initial / final / minimum (kWh) | 40.000 / 100.000 / 10.000 |
| Battery recovery target and result | 100.000 kWh; MET |
| Outage/conservation intervals | 3 |
| Maximum energy-balance residual (kWh) | 0.000000000 |

Honest negative: the synthetic outage leaves 18.000 kWh of critical load and 33.000 kWh of noncritical load unserved. Reaching the later battery recovery target does not erase that outage shortfall.

| Interval | Grid | Solar kWh | Critical served/requested kWh | Critical shed kWh | Noncritical served/requested kWh | Noncritical shed kWh | Battery end kWh | Water end L |
|---|---|---|---|---|---|---|---|---|
| 00:00-01:00 | DOWN | 0.000 | 15.000 / 15.000 | 0.000 | 0.000 / 11.000 | 11.000 | 23.333 | 280.000 |
| 01:00-02:00 | DOWN | 0.000 | 12.000 / 15.000 | 3.000 | 0.000 / 11.000 | 11.000 | 10.000 | 260.000 |
| 02:00-03:00 | DOWN | 0.000 | 0.000 / 15.000 | 15.000 | 0.000 / 11.000 | 11.000 | 10.000 | 240.000 |
| 03:00-04:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 11.000 / 11.000 | 0.000 | 14.750 | 245.000 |
| 04:00-05:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 11.000 / 11.000 | 0.000 | 19.500 | 250.000 |
| 05:00-06:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 9.000 / 9.000 | 0.000 | 24.250 | 255.000 |
| 06:00-07:00 | up | 5.000 | 15.000 / 15.000 | 0.000 | 18.600 / 18.600 | 0.000 | 29.000 | 260.000 |
| 07:00-08:00 | up | 15.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 33.750 | 265.000 |
| 08:00-09:00 | up | 25.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 38.500 | 270.000 |
| 09:00-10:00 | up | 35.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 50.280 | 275.000 |
| 10:00-11:00 | up | 40.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 66.810 | 280.000 |
| 11:00-12:00 | up | 35.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 78.590 | 285.000 |
| 12:00-13:00 | up | 25.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 83.340 | 290.000 |
| 13:00-14:00 | up | 15.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 88.090 | 295.000 |
| 14:00-15:00 | up | 5.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 92.840 | 300.000 |
| 15:00-16:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 97.590 | 305.000 |
| 16:00-17:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 100.000 | 310.000 |
| 17:00-18:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 12.600 / 12.600 | 0.000 | 100.000 | 315.000 |
| 18:00-19:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 9.000 / 9.000 | 0.000 | 100.000 | 320.000 |
| 19:00-20:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 9.000 / 9.000 | 0.000 | 100.000 | 325.000 |
| 20:00-21:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 11.000 / 11.000 | 0.000 | 100.000 | 330.000 |
| 21:00-22:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 11.000 / 11.000 | 0.000 | 100.000 | 335.000 |
| 22:00-23:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 11.000 / 11.000 | 0.000 | 100.000 | 340.000 |
| 23:00-24:00 | up | 0.000 | 15.000 / 15.000 | 0.000 | 11.000 / 11.000 | 0.000 | 100.000 | 345.000 |

Battery charge includes charge efficiency on inputs and discharge efficiency on outputs. Requested = served + shed, source-to-load energy = served energy, and solar = loads + battery + curtailment, within floating-point tolerance.

## 5. Independent water stock ledger

This interval ledger is deliberately separate from the existing daily water balance; it does not duplicate its crop-area uptake model or claim hydraulic coupling. Recovery and makeup enter stock before withdrawal, stock is capped at capacity, and unmet withdrawal is reported rather than creating negative stock.

| Item | Value |
|---|---|
| Initial / minimum end / final stock (L) | 300.000 / 240.000 / 345.000 |
| Requested / served withdrawal / shortfall (L) | 480.000 / 480.000 / 0.000 |
| Recovery / makeup / overflow (L) | 315.000 / 210.000 / 0.000 |
| Reserve / final minus reserve (L) | 200.000 / 145.000 |
| Intervals ending below reserve | 0 |

## 6. Chemical/nutrient inventory metadata only

Each record keeps its explicit unit; no mass/volume conversion or cross-unit total is attempted. Reserve status is stock metadata, not a recommendation to apply, mix, dilute or dose anything. Negative stocks and ambiguous units are rejected.

| Record | Stock | Reserve | Stock minus reserve | Status | Provenance | Source |
|---|---|---|---|---|---|---|
| Nutrient salt A (synthetic inventory label) | 25.000 kg | 10.000 kg | 15.000 kg | AT_OR_ABOVE_RESERVE | synthetic record INV-A-001; no supplier receipt, assay or measured stock | inventory metadata only; no mixing, dosing or use recommendation |
| Nutrient salt B (synthetic inventory label) | 8.000 kg | 12.000 kg | -4.000 kg | BELOW_RESERVE | synthetic record INV-B-002; no supplier receipt, assay or measured stock | inventory metadata only; no mixing, dosing or use recommendation |

## 7. Exact scope and unvalidated assumptions

- NON-OPERATIONAL synthetic arithmetic; no actuator, hardware, network or real-time clock interface.
- No crop-specific nutrient dosing or mixing recommendation and no measured crop-response claim.
- No food-safety claim, storm-resilience certification, engineering design or site validation.
- The arid location is a generic concept, not measured Iran site data.
- Plant base editing is a separate trait-evidence topic, not modeled here and not an environmental-control substitute.
- Timer, PPFD, efficacy, power, outage, solar, battery, water and reserve values are invented software inputs; none is an equipment setpoint, site measurement or validated assumption.
- The model does not estimate yield, crop health, nutrient uptake, food safety, economics, structural resilience or storm performance.

---
Synthetic indoor interval bookkeeping only. Regenerate both outputs after editing the fixture.
