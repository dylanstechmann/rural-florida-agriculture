# Crop and system matrix (rural Florida scenario)

Hand-written reasoning document. The numbers it references are labeled
placeholder assumptions in `config/scenario.json`; the arithmetic lives in
`src/floridafarm` and `docs/scenario-report.md` is the generated output.

## Matrix (placeholder sizing, not a design)

| Crop | System | Area | Cycles/yr | kg/m2/cycle | Notes |
|---|---|---|---|---|---|
| Pea shoots | NFT multi-tier | 200 m2 | 20 | 1.6 | fast 10-14 day turns; fresh-market premium |
| Basil and specialty herbs | NFT multi-tier | 160 m2 | 16 | 1.8 | steady restaurant and retail demand |
| Strawberries | indoor stacked | 120 m2 | 4 | 4.0 | pollination and runner management; premium in off-season |
| Tomatoes | drip substrate | 200 m2 | 3 | 8.0 | tall crop; needs head height, not racks |
| Sweet peppers | drip substrate | 120 m2 | 2 | 5.5 | tall crop; trellised, single-zone |
| Oranges (citrus) | screenhouse + protected enclosure | 300 m2 | 1 | 3.0 | CUPS-style insect exclusion vs psyllid/HLB |

## Reasoning

### Peas and protein

Peas get a lot of attention as a "high-protein" crop. That claim needs care:
fresh peas are protein-rich for a vegetable, but a dense protein play would
look to field peas or soybeans — commodity crops with thin margins that do
not suit a premium protected-cultivation facility. Two framings are worth
separating:

1. **Pea shoots in NFT racks** — fast turns, premium salad and microgreen
   pricing, genuinely suited to stacked indoor production. This is the
   framing the scenario carries.
2. **Vining shelling or snap peas** — trellised drip-substrate crop with
   seasonal harvest labor. Kept as a small optional trial block, not a core
   crop; it is a fresh-market premium product, not a bulk protein source.

If a protein-commodity play ever becomes the goal, that is a different
facility and a different business case, not this scenario.

### Oranges

Citrus is a tall, long-lived tree crop. It does not belong in stacked
racks. The Florida-relevant framing is protected cultivation: a CUPS-style
screenhouse (fine-mesh insect exclusion, optional positive pressure) aimed
at excluding the Asian citrus psyllid, the vector of huanglongbing (HLB).
This is a concept reference to a real research direction in Florida citrus;
it is not a claim that exclusion defeats HLB or that the placeholder
yield approaches commercial groves.

### Seasonality

Indoor and protected premium is highest when field supply is low or field
quality is poor:

- Freeze events (placeholder: 2/year) hit field greens and raise winter
  leafy-green prices.
- Humid-season disease pressure (placeholder: 6 months) argues for protected
  cultivation and strict hygiene/airflow design rather than open bato buckets.
- Strawberries and tomatoes earn their indoor area mostly in the windows
  where Florida field supply thins out.

### Rejected for this scenario

- Staple grains and standard commodity row crops: margins and agronomy do not
  suit a premium protected-cultivation facility.
- Underground or bunker-style construction: high water table, flood risk and
  hurricanes make below-grade space a liability, not an asset.
- Aquaponics as the core nutrient loop: kept as a possible future annex with
  its own water-quality and fish-health complexity, not silently assumed.
- Any claim that these placeholder yields, cycles or prices are real: change
  the scenario file and regenerate.