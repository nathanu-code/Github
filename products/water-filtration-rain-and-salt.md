# Water Filtration: Rainwater AND Saltwater

Captured 2026-09-08. Sources: [Sawyer/Backpacking Light on seawater](https://backpackinglight.com/forums/topic/lightweight-desalinization-water-filter/),
[Berkey with rainwater](https://www.robingreenfield.org/berkey/), plus the
desalination records in this directory.

## The short answer

**No conventional filter does both, and the crossover product is a
seawater-rated RO unit — but you should not use it as your daily filter.**

The honest architecture is **two systems, not one**:

| Source | Tool | Why |
|---|---|---|
| Rainwater (daily volume) | Gravity/hollow-fibre filter + disinfection | Cheap, high volume, easy consumables |
| Seawater (emergency only) | Seawater-rated RO desalinator | The only thing that removes salt |

## Why one filter can't cover both

Everything marketed as a "water filter" — Berkey, Sawyer, LifeStraw, ceramic
elements, carbon blocks — removes things **larger than water molecules**:
bacteria, protozoa, viruses, sediment, some chemicals. Against dissolved salt
they do **nothing at all**. Sawyer states plainly that its filters are not
effective on seawater because they are not designed to remove ions; Sawyer sells
separate RO units for marine use.

Salt is dissolved, not suspended — there is nothing to strain. Full explanation
in [`desalination-buyers-guide.md`](desalination-buyers-guide.md).

**Only reverse osmosis removes salt.** That is the entire crossover.

## The RO trap: not all RO does seawater

This catches people who assume "RO" is one thing. It isn't — pressure is the
dividing line:

| RO type | Operating pressure | Handles seawater? |
|---|---|---|
| Tap / under-sink RO | ~50–100 psi | **No** |
| Brackish water RO | ~150–400 psi | Partially |
| **Seawater RO** | **~800 psi (5.5 MPa)** | **Yes** |

A household under-sink RO unit cannot desalinate seawater. It lacks the pressure
to overcome seawater's osmotic pressure, and forcing it damages the membrane
without producing fresh water.

So the only single unit that genuinely covers both is a **seawater-rated RO
desalinator** — and it handles rainwater trivially, because rainwater is far
gentler feedwater than seawater.

## But don't use the desalinator for rainwater

Technically it works. Practically it's a mistake:

1. **Membrane life is your scarcest resource.** A seawater RO membrane is the
   most expensive, hardest-to-replace consumable in your entire kit. Running it
   on rainwater burns it on water a $30 gravity filter handles perfectly.
2. **Throughput mismatch.** A hand pump gives 0.89–8 L/hr of hard labour. A
   Berkey-class gravity filter passes far more water for zero effort.
3. **Wrong failure timing.** You want the desalinator's membrane fresh and
   untouched on the day rain fails — which is precisely the day you need it.

**Use the cheap filter for the abundant source; reserve the expensive one for
the emergency source.**

## Recommended architecture

### Primary — rainwater (daily)

1. First flush diverter (see [`water-catchment.md`](water-catchment.md))
2. Sediment pre-filter
3. Gravity filter, Berkey-class, for bacteria/protozoa/virus
4. Disinfection: UV, chlorine, or boiling

Cheap, high-volume, low-effort, and consumables are easy to stock deep.

### Secondary — seawater (when rain fails)

A seawater RO unit sized to the situation:

| Unit | Output | Price |
|---|---|---|
| [QuenchSea 3.0](quenchsea-3.0.md) | 5–8 L/hr | $400 |
| [Katadyn Survivor 06](katadyn-survivor-06.md) | 0.89 L/hr | ~$1,000–1,700 |
| [Electric watermaker](electric-watermakers.md) | 6–65+ L/hr | $1,200–7,000+ |

### Tertiary — distillation (when both fail)

Solar or fire distillation handles **both** salt and pathogens, needs no
consumables, and cannot break. Its yield is very low — see
[`solar-thermal-distillation.md`](solar-thermal-distillation.md). Its role is
that it never runs out, not that it's sufficient.

## Failure-mode check

The point of the layering is non-overlapping failures:

| Layer | Fails when |
|---|---|
| Rainwater catchment + filter | Drought; or filter elements exhausted |
| Seawater RO | Membrane fouls/expires; or you can't pump |
| Distillation | No sun and no fuel |

A drought takes out layer 1 and leaves 2 and 3. A fouled membrane takes out 2
and leaves 1 and 3. Nothing common takes out all three — which is the whole
design goal.

## Mineral note

Both RO output and rainwater are **very low in dissolved minerals.** Flat
tasting and, as a sole long-term source, worth supplementing with electrolytes
or a remineralising element. Distilled water is the most mineral-free of all.

## Buy a TDS meter

**~$40, and it is the only way to know any of this is working.** A TDS pen tells
you whether an RO membrane is still rejecting salt and whether your rainwater is
in range. Test on arrival, then annually. Untested water gear is an assumption,
not equipment.

## Sourcing note

Gravity-filter housings, tanks, and plumbing are safe commodity buys.
**Membranes and filter elements are not** — a counterfeit or degraded RO
membrane fails silently, producing water that looks and tastes fine while
passing salt or pathogens. Buy elements from the manufacturer or an authorised
dealer, and verify with the TDS meter. See
[`sourcing-from-china.md`](sourcing-from-china.md).
