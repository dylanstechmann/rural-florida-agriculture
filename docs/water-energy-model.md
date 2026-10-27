# Water and energy model (rural Florida scenario)

How the generated numbers in `docs/scenario-report.md` are produced. All of
it is transparent arithmetic on labeled placeholders in
`config/scenario.json`. Change the config and regenerate; never hand-edit
the report (`tests/test_report.py` fails if they disagree).

## Areas

- Canopy area = `zone_count x lit_area_m2_per_zone x tiers_per_zone`
  (placeholder: 4 x 60 x 4 = 960 m2 of lit canopy).
- Zone footprint = `zone_count x lit_area_m2_per_zone` (240 m2).
- Screenhouse area is a separate flat enclosure (300 m2, citrus).

## Water balance (per day, placeholders)

1. Uptake = indoor canopy x `uptake_l_per_m2_per_day`
   + screenhouse area x `screenhouse_uptake_l_per_m2_per_day`.
2. Recirculated = uptake x `recirculation_fraction` (capped below 1.0 in
   validation on purpose: "zero discharge" is never claimed).
3. Purge/makeup before recovery = uptake x (1 - recirculation).
4. Net makeup = purge - `condensate_recovery_l_per_day` (floored at 0).
5. Rain harvest = `annual_rainfall_mm/1000 x roof_harvest_area_m2 x
   rain_harvest_efficiency / 365`.
6. Irrigation tank = net makeup x `irrigation_backup_days`, reported next to
   "days of full uptake it covers" so a tiny number is not mistaken for a
   finished storage design.

At the placeholder values, rain harvest far exceeds net makeup — the honest
reading is "rainwater could cover makeup several times over," not "the tank
is finished." Storm mode and dry spells set real storage targets; that is
site work, not this file.

## Energy balance (per day, placeholders)

1. LED = canopy x `led_watts_per_m2_lit/1000 x lit_hours_per_day`.
2. HVAC/dehumidification = `hvac_kwh_per_m2_per_day` x controlled floor
   (zone footprint + packhouse).
3. Plus pumps, packhouse refrigeration and controls as flat placeholders.
4. Solar = `solar_array_kwp x peak_sun_hours_per_day x
   solar_performance_ratio`.
5. Solar fraction = min(1, solar / total). Honest accounting: the placeholder
   array covers about an eighth of the modeled load, not "the whole farm."
6. Critical loads = total x `critical_load_fraction`; battery autonomy =
   `battery_kwh / (critical/24)`, compared against
   `design_backup_autonomy_hours` and reported PASS or GAP.

At the placeholder values the battery lands well short of the 12-hour
critical-load autonomy target, so the report prints a GAP line — the honest
answer, not a silently resized battery. The report also prints the array
size in kWp that would be needed for a 50% solar fraction.

## Regenerating

```bash
cd rural-florida-agriculture
PYTHONPATH=src python -m floridafarm validate
PYTHONPATH=src python -m floridafarm report --out docs/scenario-report.md
python -m unittest discover -s tests -v
```

## What this model is not

- Not a hydraulic or electrical design: no pipe sizing, head loss, fault
  currents, code checks or equipment selection.
- Not a yield, price or weather prediction: every input is a labeled
  placeholder, and outputs move exactly with them.
- Not a safety case: storm mode, food safety and backup-power verification
  are checklist items in `docs/resilience-and-automation.md`, not results
  claimed here.