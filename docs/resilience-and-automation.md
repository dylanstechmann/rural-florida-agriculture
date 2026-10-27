# Resilience and automation (rural Florida scenario)

Hand-written concept notes for flood, storm and automation design. Borrowed
pattern from the AI/robot-parenting project: local-first control, N+1
redundancy, a qualification ladder, and honest negatives — never a silently
resized design. Nothing here is a wind, flood or code calculation.

## Flood and elevation

- Raised floors (placeholder 1.2 m) on piers/pilings, equipment pads above
  the local flood design elevation — real elevation to be set by site
  survey, not this document.
- Sensitive equipment (dosing, controls, batteries, refrigeration) elevated
  first; nothing electrical below the water line.
- Retention pond and site drainage; storm-mode drainage paths kept clear.
- Water-table reality: no below-grade rooms. Underground or bunker-style
  space is deliberately rejected for this scenario.

## Wind and storm (placeholder category-3 design intent)

- Hurricane straps and uplift connection placeholders on roofs and racks.
- Ballasted, hurricane-rated PV racking; panel removal or stow mode only if
  a real design says so.
- Storm shutters or rated glazing placeholders on openings.
- A written storm-mode checklist is part of the scenario config
  (`automation.storm_mode_checklist`), and running it is a qualification
  item, not an assumption.

## Automation: local-first

- Controls keep the water loop, dosing, climate and alarms running with no
  internet. Cloud dashboards are additive, never load-bearing.
- Manual overrides and safe failure states: power loss must leave valves
  and dosing in a safe state, not a guessed one.
- Backed-up control configurations, per-user permissions, and no remote
  control of critical equipment without explicit local approval.

## N+1 redundancy

`automation.n_plus_1` lists the redundant paths this concept refuses to run
single-string: water pumps, zone controllers, dosing pumps, and the
critical power path. Redundancy is verified by the qualification ladder,
not assumed by the model.

## Qualification ladder (borrowed pattern)

1. **Simulated day** — the control model runs a full labeled day
   (schedule, alarms, storm-mode transitions) before anything is bought.
2. **Wet test** — real water through the treatment train, dosing and return
   loop with sensors, before plants.
3. **Commissioning** — storm mode, power loss and N+1 switchovers rehearsed
   and timed.
4. **First crop-cycle audit** — water/kg and energy/kg measured per zone;
   no number is promoted to a dependable claim before this audit.

No demonstration (a clean simulated day, a working wet test) is ever
promoted to dependable capability. A timeout or failure produces a
checkpoint and a work item, never silent completion.

## Food safety and pests

- Post-harvest washing only where a real process requires it; otherwise
   harvest-to-packing hygiene and cold chain placeholders.
- Pest exclusion and monitoring: screens, seals, entry controls, and an
   IPM plan that assumes humid-season pressure.
- Citrus specifics: screenhouse exclusion is a placeholder research
   reference (psyllid/HLB), not a disease claim.

## Honest gaps this concept does not paper over

- The placeholder battery falls short of the 12-hour critical-load autonomy
  target — the report prints a GAP line.
- The placeholder solar array covers only a fraction of the modeled load.
- Storm mode, food safety and backup-power performance are checklist
  items until measured on a real site.