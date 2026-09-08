# Preparedness System — How the Pieces Fit

A synthesis across the records in this directory. Captured 2026-09-08.

## The organising principle

Don't buy the best item in each category. **Buy a set whose failure conditions
don't overlap**, then spend the remaining budget on depth in the layer that
fails first.

Every record here is built on that logic. Consolidated:

| System | Layer | Fails when |
|---|---|---|
| **Water** | Rain catchment + gravity filter | Drought; elements exhausted |
| | Seawater RO | Membrane fouls; you can't pump |
| | Distillation | No sun and no fuel |
| **Cooking** | Propane, 20 lb tanks | Tanks run dry |
| | Multi-fuel liquid stove | No liquid fuel available |
| | Wood stove | (Effectively never) |
| | Alcohol | Alcohol runs out |
| **Power** | LFP power station + solar | Extended overcast; unit fails |
| | (fuel generator, if scoped) | Fuel runs out |

A drought kills water layer 1. A cold snap kills a butane stove. A week of
overcast kills solar. **Nothing common kills all three layers of any system** —
that is the design goal, and it's cheaper than buying one expensive thing.

## The three findings worth acting on

### 1. Propane is the fuel answer, unambiguously

It's rare for one option to win on every axis, but propane does: **indefinite
shelf life**, cheapest per BTU (canisters cost 6–10× more per gallon), and it
works at any temperature (−44 °F boiling point vs. n-butane failing at ~30 °F).

Corollary: **gasoline is the worst thing to stockpile** — 3–6 months for
ethanol-blend. Most people's existing "fuel stockpile" is the fastest-spoiling
option they could have chosen.

Full detail: [`stoves-and-fuel.md`](stoves-and-fuel.md)

### 2. No filter desalinates — you need two water systems

Berkey, Sawyer, LifeStraw and every gravity/hollow-fibre filter remove **zero**
salt. Only RO does, and only **seawater-rated** RO (~800 psi) — an under-sink RO
unit at 50–100 psi cannot.

The crossover unit exists (a seawater desalinator handles rainwater trivially)
but you shouldn't use it that way: it burns your scarcest consumable on water a
$30 filter handles. Cheap filter for the abundant source, expensive one held in
reserve.

Full detail: [`water-filtration-rain-and-salt.md`](water-filtration-rain-and-salt.md)

### 3. Source the container, buy the mechanism

Chinese sourcing is fine — and often the same factories — for anything that
**holds, channels, or contains**. It is a bad idea for anything that **holds
pressure, burns fuel, stores energy, or is the last barrier before you drink**.

"Same factory" is not "same quality": the brand's run is built to the brand's
spec and QC; the house version off the same tooling is built to the factory's.

Full detail: [`sourcing-from-china.md`](sourcing-from-china.md)

## Build order

Sequenced by cost-to-benefit, cheapest high-impact first:

| # | Action | Cost | Why first |
|---|---|---|---|
| 1 | TDS meter | ~$40 | Nothing else is verifiable without it |
| 2 | First flush diverter | $20–60 | Highest water-quality leverage per dollar |
| 3 | Propane burner + 2–3× 20 lb tanks | ~$150–250 | Fuel that never expires, cheapest BTU |
| 4 | Wood/rocket stove | ~$30–100 | Removes the fuel supply chain entirely |
| 5 | Rain catchment, DIY IBC totes | $400–700 | Bulk water volume |
| 6 | Gravity filter (Berkey-class) + spare elements | ~$300+ | Makes catchment potable |
| 7 | LFP power station + panels | $500–2,000+ | Buy branded; size to a real load list |
| 8 | Seawater RO desalinator | $400–1,700 | Only if coastal — otherwise skip |
| 9 | Multi-fuel liquid stove | $150–250 | Fuel flexibility layer |

**Items 1–4 total under $500** and cover the two most likely real scenarios
(loss of grid, loss of water pressure). Items 7–8 are where the money goes and
should wait until the cheap layers are actually in place.

## Where the desalinator sits

Only worth it **if you are coastal**. Inland, rain catchment plus a gravity
filter does the same job for a fraction of the cost, and the $400–1,700 is
better spent on storage volume and spare filter elements.

If coastal: [QuenchSea 3.0](quenchsea-3.0.md) at $400 for 5–8 L/hr is the
volume-per-dollar choice; [Katadyn Survivor 06](katadyn-survivor-06.md) at
1.13 kg is the grab-bag choice. Full comparison in
[`desalination-buyers-guide.md`](desalination-buyers-guide.md).

## Still open

Two questions narrow all of this to specific purchases:

1. **Budget** — the range across these records spans under $500 to $10,000+.
2. **Scenario** — coastal vs. inland changes the water answer completely, and
   marine survival vs. home resilience changes nearly every recommendation.
