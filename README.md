# Rural Florida high-tech agriculture concept

Standalone scenario track: rural Florida, USA — flood-aware, storm-rated,
solar-plus-storage controlled-environment agriculture for higher-value crops.

Status: agent-drafted 2026-10-27 from the owner's direction. Labeled
placeholder assumptions only. No site is chosen, nothing here is
owner-reviewed or independently reviewed, and no number is a measurement,
price quote or performance claim. Regenerate outputs after editing the
scenario file; never hand-edit generated files.

This repository is maintained independently. It began as a scenario track
beside a separate Iran controlled-environment concept and was split into
its own repository so the two can be published, updated and compared
independently.

## Why a scenario track

A separate Iran concept asks how controlled-environment agriculture adapts
across a large, water-constrained country. This repository asks the same
question for a completely different environment: rural Florida — humid,
hurricane-exposed, flood-prone, rain-rich, with strong winter fresh-market
demand and a different pest and disease picture. Keeping it a labeled,
config-driven scenario (rather than a fixed design) is the pattern borrowed
from an earlier private project: a scenario track beside a baseline, never
replacing it.

## Shared conventions

- Color legend: blue water, green nutrients/crops, orange power, purple
  controls, red waste/purge, gray structure.
- Scene pattern: index, campus, systems schematic.
- Honesty rules: concept visualization and placeholder arithmetic, never
  engineering, survey or construction data.

## What is deliberately different

- Cooling and dehumidification instead of winter heating.
- Elevated, storm-rated, above-ground construction (raised-floor placeholder
  1.2 m). NOT an underground bunker: rural Florida means a high water table,
  flood exposure and hurricanes, so below-grade space is a liability there.
- Hurricane-rated ballasted PV racking, storm shutters/straps, a retention
  pond, and rainwater harvest sized against the water balance.
- Citrus (oranges) in a CUPS-style insect-exclusion screenhouse, not in
  stacked indoor racks: citrus is a tall, long-lived tree crop, and the
  Florida-relevant framing is psyllid/HLB exclusion research, not racks.
- High-value fresh crops first (pea shoots, herbs, strawberries, tomatoes,
  peppers). Peas are evaluated honestly: as pea shoots (fast turns, premium
  pricing, genuinely suited to racks) rather than as a bulk protein play.

## Structure

```
rural-florida-agriculture/
├── README.md                  # this file
├── pyproject.toml
├── .gitignore
├── config/
│   ├── scenario.json               # original labeled daily-model assumptions
│   └── indoor-simulation.json      # separate synthetic interval fixture
├── docs/
│   ├── crop-system-matrix.md          # hand-written crop reasoning
│   ├── water-energy-model.md          # model equations and regen instructions
│   ├── resilience-and-automation.md   # flood/storm resilience, N+1, local-first
│   ├── scenario-report.md             # GENERATED original report (tests pin it)
│   ├── indoor-simulation.md           # interval units, equations and exact scope
│   ├── indoor-simulation-report.md    # GENERATED indoor Markdown (tests pin it)
│   └── indoor-simulation.json         # GENERATED indoor JSON (tests pin it)
├── src/floridafarm/           # daily model plus isolated indoor simulator and CLIs
├── tests/                     # unittest suite (stdlib only)
└── viz/
    ├── rural-florida-campus.blend   # FLRural_* scenes (separate from Iran blend)
    └── renders/                    # 1920x1080 PNG renders
```

## Run it

Python 3.10 or later, standard library only.

```bash
cd rural-florida-agriculture
PYTHONPATH=src python -m floridafarm validate                      # check the scenario file
PYTHONPATH=src python -m floridafarm report --out docs/scenario-report.md   # regenerate the report
python -m unittest discover -s tests -v                            # run the test suite
```

`tests/test_report.py` fails if the committed `docs/scenario-report.md` no
longer matches the model, so the generated file never silently drifts from
the assumptions.

### Separate NON-OPERATIONAL indoor simulated day

A bounded interval fixture exercises lighting, timers, energy dispatch,
battery recovery, water stock and inventory metadata without changing the
original daily scenario or its generated report:

```bash
PYTHONPATH=src python3 -m floridafarm simulate-day \
  --config config/indoor-simulation.json \
  --json-out docs/indoor-simulation.json \
  --markdown-out docs/indoor-simulation-report.md
```

The default is 24 hourly intervals; a configured count must divide 1440 and
is capped at 96. Source-labelled synthetic PPFD schedules produce union
photoperiod and DLI arithmetic. Half-open timer windows support gaps,
overlaps and midnight wrapping. The energy ledger accounts for continuous
and scheduled loads, solar/grid availability, battery state, critical and
noncritical served/shed energy, conservation and recovery. A separate water
ledger tracks stock, recovery, makeup, shortfall and reserve. Chemical and
nutrient records are provenance/stock/reserve metadata only.

This track is **NON-OPERATIONAL simulation**: no actuator or hardware
interface, no real-site measurements, no crop-specific nutrient dosing or
mixing recommendation, no food-safety claim, and no storm-resilience
certification. The generic arid fixture is not measured Iran site data.
Plant base editing is outside this model and, if discussed elsewhere, is a
separate trait-evidence layer rather than an environmental-control
substitute. See `docs/indoor-simulation.md` for equations, validation and
all unvalidated assumptions. Both indoor outputs are deterministic and
pinned by `tests/test_indoor_report.py`.

`tests/test_indoor_blackout.py` also pins the studied schema-v1 blackout
artifact: with grid and solar disabled and the battery at its reserve floor,
all 643.2 kWh are shed while the deliberately independent agricultural water
ledger still records 480 L served withdrawal and 315 L recovered. The separate
habitat consumer's 21 power/water-coupling conflicts remain an external
integration result; the producer does not silently adopt that coupling.

## 3D visualizations

`viz/rural-florida-campus.blend` holds three labeled scenes:
`FLRural_Index` (title card and legend), `FLRural_Campus` (elevated
flood-aware campus: grow halls on piers, CUPS-style citrus screenhouse,
packhouse, battery + generator shed, rain tanks and treatment skid, solar
field, retention pond) and `FLRural_Systems` (node-link schematic of water,
power, controls, N+1 and storm mode). Renders are in `viz/renders/`.
Metric units: 1 Blender unit = 1 metre.

## Pattern borrowed from an earlier private project

- A labeled side scenario beside a baseline, never replacing it.
- Config-driven assumptions; regenerate outputs instead of hand-editing.
- A generated report pinned by tests (report/model agreement enforced).
- Local-first control: the facility keeps running safely without internet.
- N+1 redundancy for pumps, controllers, dosing and the critical power path.
- A qualification ladder: simulated day → wet test → commissioning → first
  crop-cycle audit. Demonstrations are never promoted to dependable capability.
- Honest negatives printed instead of hidden — for example, the placeholder
  battery falls short of the 12-hour critical-load autonomy target, and the
  report says so rather than resizing silently.

## Honesty rules

This is concept visualization and placeholder arithmetic. Real deployment
needs site selection, soil and water-table
studies, wind and flood design to real codes, permits, water rights, market
research, food-safety plans and local agronomy.