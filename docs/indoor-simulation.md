# Non-operational indoor interval simulation

`config/indoor-simulation.json`, `src/floridafarm/indoor.py` and
`src/floridafarm/indoor_report.py` are a separate synthetic software track.
They do not alter or replace the daily model in `model.py`, the original
`config/scenario.json`, or `docs/scenario-report.md`.

Every input is invented and unvalidated. The generic arid vertical-farm
location is not a selected site and contains no measured Iran site data.
This is deterministic interval bookkeeping, not an equipment controller,
engineering design, agronomic recommendation or performance claim.

## Run and regenerate

Python 3.10 or later, standard library only:

```bash
PYTHONPATH=src python3 -m floridafarm simulate-day \
  --config config/indoor-simulation.json \
  --json-out docs/indoor-simulation.json \
  --markdown-out docs/indoor-simulation-report.md
python3 -m unittest discover -s tests -v
```

Both generated files are pinned by `tests/test_indoor_report.py`. They have
no timestamps, random values, environment lookups or external data reads.
Regenerate both after changing the fixture; never hand-edit either output.

Add `--water-handoff-out farm-water.json` to the same command to exchange
the simulated day with Habitat Resource Sandbox. This writes the configured
agricultural reservoir capacity in liters and the SHA-256 of the emitted
JSON report. Supply both files to the habitat water-budget comparison.
The capacity matters when comparing a different makeup schedule because
overflow can discard water before a later interval needs it.

Use `--makeup-outage 510 630` to interrupt scheduled makeup from 08:30 until
10:30. The model prorates the configured hourly makeup rate by the minutes
available in each interval. Internal farm recovery follows its own schedule.
A window can cross midnight, and `--makeup-outage 0 1440` removes the whole
day's scheduled makeup. Use distinct output filenames for a scenario variant.
Its JSON and Markdown carry the interruption times and the handoff pins the
variant's JSON. A multi-day habitat replay repeats this farm day, including
its interruption, on every modeled day.

## Bounds, units and schedules

- `intervals.count` is an integer from 1 through 96 and must divide 1440, so
  every interval has an equal whole-minute duration. The fixture uses 24
  one-hour intervals. Per-interval arrays must have exactly that length.
- Minutes use the half-open convention `[start_minute, end_minute)`. Midnight
  is minute 1440 as an end boundary. A start later than its end wraps through
  midnight; equal start/end values are rejected as ambiguous. Use `[0, 1440)`
  for a full day.
- Schedule windows are split at midnight and unioned. Gaps and overlap regions
  are reported, and overlapping windows never multiply photoperiod or energy.
  Partial interval overlap is integrated in minutes.
- Power is kW; energy is kWh; active power is converted with `kW x h`.
  Lighting area is m2, PPFD is umol/m2/s, efficacy is umol/J, photoperiod is
  hours and DLI is mol/m2/day. Water is L. Battery charge is stored kWh.
- Numeric inputs must be finite JSON numbers, not booleans or numeric strings.
  Stocks, powers and rates cannot be negative. Battery efficiencies are in
  `(0, 1]`; charge bounds and list lengths are checked. Unknown keys are
  rejected instead of being silently interpreted.

## Lighting arithmetic

Each per-crop profile carries a `source_label`. In the fixture that label
explicitly says the profile is synthetic, not an agronomic target or measured
crop response.

```text
lighting power kW = area_m2 x PPFD_umol_m2_s / efficacy_umol_j / 1000
photoperiod h     = union of scheduled active minutes / 60
DLI mol/m2/day    = PPFD_umol_m2_s x photoperiod_h x 3600 / 1,000,000
requested kWh     = lighting power kW x photoperiod h
served-equivalent DLI mol/m2/day = scheduled DLI x (served lighting kWh / requested lighting kWh)
```

No target DLI, yield response or crop-health outcome is inferred. The two
profiles exist to exercise the arithmetic, source labels, overlap handling
and midnight boundaries.

## Loads, conservation and recovery

Lighting and timers contribute only during their unioned active minutes.
Continuous equipment contributes its kW for every interval. Each load is
labelled `critical` or `noncritical`.

Dispatch is deliberately simple and deterministic:

1. Available solar serves critical load first.
2. With grid available, solar then serves noncritical load, grid covers all
   remaining load, and no battery discharge is used.
3. With grid unavailable, conservation mode sheds all noncritical load.
   Solar and then the battery serve critical load; any remaining critical
   load is explicitly reported as shed. Surplus solar can charge the battery
   rather than serving shed noncritical load.
4. Remaining solar charges the battery up to its power and capacity limits.
   With grid available, bounded grid recovery charging can raise charge to
   the configured recovery target after solar charging.
5. Same-class shortfalls are allocated proportionally across loads in the
   JSON detail. No priority is presented as a real control policy.

For each interval, requested energy equals served plus shed energy;
source-to-load energy equals served energy; and solar availability equals
solar to loads plus solar to battery plus curtailment. Stored battery charge
uses input charge efficiency and output discharge efficiency, never drops
below the configured minimum, and never exceeds capacity. The fixture
intentionally retains 18 kWh of critical and 33 kWh of noncritical outage
shortfall even though the battery later reaches its recovery target.

## Independent water ledger

The interval water ledger is intentionally separate from the existing daily
crop-area water balance. It does not reuse its uptake equations, duplicate
that model, or claim to represent a coupled irrigation controller.

```text
available L = start stock + interval recovery + interval makeup
served withdrawal L = min(requested withdrawal, available)
end stock L = min(capacity, available - served withdrawal)
overflow L = available - served withdrawal - end stock
shortfall L = requested withdrawal - served withdrawal
```

Stock cannot become negative. Reserve is reported metadata, not a hidden
interlock, and ending below reserve is retained as an honest result.

## Complete-blackout regression and schema-v1 handoff

`tests/test_indoor_blackout.py` derives a blackout case in memory from the
committed fixture. It disables grid availability in all 24 intervals, sets all
solar inputs to zero, and sets initial battery charge to the existing 10 kWh
reserve floor. Every other input, including scenario version `2026-11-26` and
the independent agricultural water ledger, remains unchanged. The emitted
artifact remains `schema_version` 1; this regression does not revise the
interface or reinterpret the scientific assumptions.

The current fixture requests and sheds 643.2 kWh, serves 0 kWh, and finishes
with the battery at 10 kWh. It still records 480 L of requested and served
agricultural withdrawal, 315 L recovered and zero water shortfall. Those water
entries are explicit producer inputs and stock arithmetic, not evidence that
recovery can operate without power. Introducing power-coupled producer water
would require an explicit fixture and interface revision rather than a silent
change to this case.

The exact serialized producer SHA-256 pins are
`82981f9df5227450aa41d4b4620494564cc56c90f05fe6198d4ba0d3ffc78ba5`
for the ordinary artifact and
`3996c10f0ccb3944bee2e6c53bdf84c8cc544d7f3d47d45dda654692e79bf3bf`
for the blackout artifact. The producer regression also pins recovery after a
preceding shed-power interval at zero-based indices 3 through 23. The separate
habitat importer interprets those 21 observations as power/water-coupling
conflicts under its delayed, power-coupled consumer model. That consumer
classification is verified by the external comparison reproducer, not by
pretending the producer and consumer share a water model.

## Chemical/nutrient inventory metadata

Inventory records contain only a name, nonnegative stock and reserve amounts,
one explicit unit (`kg`, `g`, `L` or `mL`), provenance and a source label.
Stock minus reserve and reserve status are calculated per record. There are
no cross-unit totals or conversions. Negative amounts, unsupported/ambiguous
units, duplicate names and unknown fields such as dosing or mixing
instructions are rejected.

These records are not nutrient recipes, application rates, compatibility
instructions or crop-specific dosing recommendations. They do not model
consumption or claim that reserve status is sufficient for any operation.

## Exact exclusions and unvalidated assumptions

- **NON-OPERATIONAL:** there is no actuator interface, device driver, network
  call, real-time clock, hardware discovery or control side effect. "Served"
  and "shed" are labels in arithmetic, not commands to equipment.
- No food-safety claim, storm-resilience certification, structural/electrical
  design, site suitability conclusion or real backup-autonomy claim.
- No crop-specific nutrient dosing/mixing recommendation, plant-health claim,
  measured yield, economic forecast or validated lighting setpoint.
- Plant base editing belongs, if addressed elsewhere, to a separate
  trait-evidence layer. It is not modeled here and is never a substitute for
  environmental control, energy, water or inventory accounting.
- Timer behavior, solar availability, grid outages, equipment powers,
  battery efficiency, water recovery/makeup and all reserves are invented
  software inputs. Real qualification would require separate measurements,
  engineering review and commissioning outside this repository increment.
