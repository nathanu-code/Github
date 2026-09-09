# Seawater Desalination — Options Breakdown

Captured 2026-09-08. Prices and specs are point-in-time; each linked record
carries its own sources.

## Why a filter can't do this

Salt does not float in water as particles — it **dissociates into sodium and
chloride ions** that bind to water molecules at molecular scale. There is no
mesh fine enough to strain them, because there is nothing to strain. A hydrated
sodium ion is roughly the same size as the water molecules around it.

Only two mechanisms actually separate them:

1. **Reverse osmosis** — force water molecules through a membrane so tight that
   ions cannot follow. RO membranes run around **0.0001 microns** (well under
   1.5 nm).
2. **Distillation** — evaporate the water and leave the salt behind, since salt
   does not become gas at water's boiling point.

Every product below is one of those two. There is no third mechanism, and no
gravity filter, straw, or tablet does it. *(A widely repeated figure of 0.00001
microns is off by a factor of ten — that would be smaller than a single atom.)*

## The four approaches

| | Output | Power source | Cost | Hard limit | Best for |
|---|---|---|---|---|---|
| [Manual RO — QuenchSea 3.0](quenchsea-3.0.md) | 5–8 L/hr | Hand lever | $400 | Your stamina; 6 kg to carry | Best litres-per-dollar; small crew |
| [Manual RO — Katadyn Survivor 06](katadyn-survivor-06.md) | 0.89 L/hr | Hand pump | ~$1,000–1,700 | Your stamina | Lightest ditch-bag option; proven |
| [Forward osmosis pouches](forward-osmosis-pouches.md) | ~pouch volume / ~5 hrs | Osmotic gradient (syrup) | Low per pouch | Syrup charges — then dead | When you *cannot* pump |
| [Solar / thermal distillation](solar-thermal-distillation.md) | ~0.5–1.5 L/day per m² | Sun or fire | ~$0 | Collection area and sun | Static shore camp; last resort |
| [Electric watermakers](electric-watermakers.md) | 6–65+ L/hr | 12/24 V or petrol | $1,200–$7,000+ | Amp-hours or fuel | Continuous supply, not survival |

## The number that decides everything

**An adult needs about 3 litres per day.** Hold every option against that:

| Option | Time to make one person's daily water |
|---|---|
| Electric watermaker (30 L/hr) | 6 minutes |
| QuenchSea 3.0 (5–8 L/hr) | ~25–35 min of pumping |
| Katadyn Survivor 06 (0.89 L/hr) | **~3.4 hrs of continuous pumping** |
| Forward osmosis pouch | ~5 hrs wait, multiple pouches, capped by charges |
| Improvised solar still | **Does not get there.** Days. |

This reframes the whole category. The manual devices are not "slower versions"
of watermakers — the Survivor 06 asks for three and a half hours of hard
physical work per person per day, while dehydrated. That is the spec that
matters, not salt rejection.

## How to choose

**Marine survival (life raft / ditch bag).** Weight and reliability beat
throughput, because the device only matters if it is in the bag you actually
grab. Katadyn Survivor 06 at 1.13 kg is the orthodox answer and is what
life-raft servicing expects. QuenchSea's 6 kg is a real penalty here, but 5–8
L/hr for $400 changes the calculus if more than one or two people are aboard.
Consider both: pump as primary, pouches as the injured-crew fallback.

**Coastal home / bug-out position.** Electric or petrol watermaker as the
supply, a manual pump as the power-failure backup, and a purpose-built solar
still if you have the footprint. Here distillation finally makes sense — you
have the area, the sun, and the time.

**Coastal camping / hiking.** QuenchSea if you can carry 6 kg and want real
volume; Survivor 06 if grams matter more than litres. Know the solar still
method regardless, since it costs nothing to learn.

**Cruising yacht.** Both layers, always. Electric watermaker for living,
manual pump in the raft for the day the boat's power is gone.

## Buying cautions

- **Forward osmosis availability has collapsed.** SeaPack is out of production
  and HTI has closed. The remaining Amazon-available option (OTS Osmo Seal) has
  much thinner documentation and no comparable independent testing. Verify
  before depending on it.
- **Watch the warranty on the cheap end.** QuenchSea's is 3 months and excludes
  every consumable — membranes, pre-filters, seals. That is the shortest term in
  this set by a wide margin.
- **Consumables are the real cost.** Membranes and pre-filters are recurring;
  QuenchSea does not publish lifespans, which makes total cost of ownership
  impossible to model from published data.
- **Confirm production status and part numbers.** Several models across the
  Katadyn/Spectra lines are being discontinued or rebranded, and price spreads
  across retailers for the same family run 40%+.
- **Test on arrival.** A TDS pen is ~$40 and is the only way to know a membrane
  is performing. An untested desalinator is an assumption, not equipment.

## Open questions before a final recommendation

Two things narrow this to a single answer:

1. **Budget** — the range here spans $0 to $7,000+.
2. **Use case** — marine survival, home bug-out bag, or coastal camping. These
   point at genuinely different products, not different tiers of one product.
