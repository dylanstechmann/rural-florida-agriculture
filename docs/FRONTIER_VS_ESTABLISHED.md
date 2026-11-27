# Frontier versus established

**Date:** 2026-11-27

This boundary applies to the agent-run indoor interval fixture and its offline
software checks. "Established" below means reproducible **SOFTWARE** behavior
on the stated synthetic inputs, not measured farm performance or scientific
validation.

## Established SOFTWARE observations

The original pre-integration checkpoint passed **49/49 tests**. After the
fast-forward integration, the final reconciled tree at commit
`17689b1b75c397f6e11f1fead0c4efd4e9648fb4` passed **52/52 tests** before
that commit was pushed. Both counts are retained as software observations;
the increase reflects the reconciled incoming test suite.

The blackout regression derives its case from fixture version `2026-11-26`,
keeps producer artifact `schema_version` 1, disables grid and solar input, and
starts the battery at its 10 kWh minimum charge. Exact JSON serialization and
SHA-256 pins make unintended changes visible.

| Synthetic software check | Established observation |
| --- | --- |
| Complete-blackout electrical ledger | 643.2 kWh requested and shed; 0 kWh served. |
| Independent agricultural water ledger | 480 L requested and served withdrawal; 315 L recovered; zero water shortfall. |
| Producer sequence | Recovery follows shed power at zero-based interval indices 3 through 23. |
| External habitat import comparison | The read-only reproducer matched its archived comparison and reported 21 recovery-after-shed-power conflicts. |

These observations establish deterministic ledger arithmetic, regression
coverage, artifact identity and the consumer adapter's stated classification.
The habitat conflicts are comparisons between two software models, not observed
physical faults. The independent producer water schedule is not evidence that
water recovery actually operates without electrical power.

## Frontier, open or not established

- **Actual farm performance:** no selected site, operating farm, equipment
  measurements, commissioning data, production record or independently
  reviewed performance result establishes real performance.
- **Physical water/power coupling:** pump, treatment, recovery, storage and
  control dependencies remain unmeasured and unvalidated. The producer's
  separate water ledger must not be read as a physical coupling model.
- **Operational sustainability:** resource autonomy, reliability, resilience,
  maintenance, food closure, economics and long-term operation remain open.
- **Real-world and agronomic validation:** crop health, yield, quality,
  lighting response, water quality, nutrient outcomes and food safety are not
  established here. Synthetic ledger outputs are not agronomic evidence.

## Update when evidence changes

Revisit this document whenever the fixture, schema, dispatch or water
assumptions, source pins, tests, or external consumer comparison change, and
when reviewed measurements or validation evidence become available. Date each
update and record the applicable commit, fixture/schema versions, commands,
source provenance and reviewer status. Keep a changed software result separate
from a new physical or agronomic claim; new evidence must not be retroactively
inferred from these synthetic observations.
