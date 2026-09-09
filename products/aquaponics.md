# Aquaponics & RAS Fish Farming

Captured 2026-09-08. Sources: [FarmHub — component calculations and ratios](https://learn.farmhub.ag/resources/small-scale-aquaponic-food-production/8-management-and-troubleshooting/component-calculations-and-ratios/),
[Aquaponics.com — ten guidelines (Rakocy/UVI)](https://aquaponics.com/wp-content/uploads/articles/Ten-Guidelines-for-Aquaponics.pdf),
[Go Green — dissolved oxygen](https://gogreenaquaponics.com/blogs/news/the-importance-of-dissolved-oxygen-in-aquaponics),
[Go Green — protecting a system during power failure](https://gogreenaquaponics.com/blogs/news/how-to-protect-your-aquaponics-system-during-power-failure),
[ScienceDirect — stocking density and Nile tilapia growth](https://www.sciencedirect.com/science/article/pii/S2468550X21000381),
[Oklahoma State Extension — small-scale aquaponics](https://extension.okstate.edu/fact-sheets/principles-of-small-scale-aquaponics),
[Texas A&M — water usage in RAS/aquaponics](https://extension.rwfm.tamu.edu/wp-content/uploads/sites/8/2013/10/Water-Usage-in-Recirculating-AquacultureAquaponic-Systems.pdf)

Screenshots: [`images/`](images/) — `alibaba-qihang-ras-*.png`

## 1. Do aquaponics and fish farming work together well?

**Yes — this is real working technology, not a gimmick.** But the mechanism
isn't what most people picture.

Fish waste → **ammonia** → nitrifying bacteria oxidise it to **nitrite** → then
to **nitrate** → plants take up the nitrate → cleaned water returns to the fish.

**The bacteria are the engine**, not the fish and not the plants. Both are
customers of the biofilter. That's the thing beginners miss, and it's why
failures cascade instead of staying local: kill the biofilter and you lose the
fish *and* the plants.

### Two real tensions the marketing skips

**pH is a compromise both sides lose.** Fish and nitrifying bacteria want
roughly 7.0–7.5. Plants want roughly 5.5–6.5. Aquaponics runs around 6.8–7.0 —
tolerable for everyone, optimal for nobody. Expect slightly worse performance
than either a dedicated hydroponic or a dedicated RAS setup.

**Fruiting crops don't get enough.** Fruiting vegetables need about **one-third
more nutrients** than leafy greens. Fish feed alone typically can't supply
enough iron, potassium, and calcium, so you end up supplementing. "Complete
closed-loop food system" is oversold.

**Where it genuinely shines:** leafy greens and herbs with tilapia. That
combination is proven at scale and is what the research base is built on.

## 2. What if the water gets shut off?

Two completely different failure modes, and people worry about the wrong one.

### Mains water shut off — this is the easy one

Aquaponics is **recirculating**, so it barely consumes water. Small-scale
systems lose **1–5% of system volume per day** (about 1% is typical) to
evaporation, transpiration, plant uptake, and splashing.

| System volume | Daily top-up |
|---|---|
| 300 gal | ~3–15 gal/day |
| 1,000 gal | ~10–50 gal/day |

**Rainwater catchment covers that comfortably** — 1 inch of rain on a 1,000 sq ft
roof yields around 600 gallons. See [`water-catchment.md`](water-catchment.md).
Water supply is a solved problem here.

> **⚠ Do not put roof runoff straight into a fish tank.** Copper and zinc —
> from flashing, gutters, and galvanised surfaces — are **acutely toxic to fish
> at concentrations far below what matters for human drinking water**. Rainwater
> is also very low in alkalinity, so pH will swing hard without buffering.
> Test for metals, buffer the KH, and let water age before it touches fish.

### Power shut off — this is the one that kills

**Fish suffocate within hours without aeration.** Warm water and high stocking
density shorten that dramatically, and the first few hours decide whether the
system survives.

Worse, it's a **double failure**: the nitrifying bacteria are aerobic too. When
flow stops the biofilter goes anoxic and can crash — which then spikes ammonia
and kills fish *after* power returns.

**The good news is the load is tiny.** An air pump is roughly **20–100 W**,
against 3,000 W for the induction cooker in these records. This is the one food
production load a modest battery genuinely solves:

| Mitigation | Notes |
|---|---|
| **Battery-backed air pump + airstone** | The standard answer. Small load, long runtime, cheap |
| **Generator** | Necessary for larger systems and multi-day outages |
| **Stop feeding** | Most fish survive days without food. Feeding during an outage adds ammonia, which consumes the remaining oxygen |
| **Manual aeration** | Pour or splash water from a container to drive surface gas exchange |
| **Lower stocking density** | Insurance bought in advance — sparse tanks buy hours |

Even a small LFP power station covers a 40 W air pump for days. See
[`solar-generators.md`](solar-generators.md) and
[`home-solar-and-battery.md`](home-solar-and-battery.md).

### The honest preparedness verdict

**Aquaponics is the most power-fragile food production method there is.** A soil
garden needs zero electricity and fails slowly. Aquaponics fish die in hours.

As a resilience play it is a liability *unless* you have solved backup aeration
first. Because the load is small, that's genuinely solvable — but it must be
solved before you stock fish, not after.

## 3. How many fish can you grow per month?

This is where the marketing is most misleading. **Fish don't grow "per month" —
they grow to harvest size over 6–9 months.** Any monthly figure is a harvest
schedule, not a growth rate.

### Growth rate

| Metric | Value |
|---|---|
| Tilapia, fingerling → harvest (1–1.5 lb / 450–700 g) | **6–9 months** |
| At 25 °C, good water quality | 6–8 months |

Growth is **temperature-driven**. Cold water slows it sharply — which is why
heating is often the biggest continuous load in the whole system, bigger than
the pumps.

### Stocking density

| Guidance | Density |
|---|---|
| Beginner / balanced system | **0.5 lb per gallon** |
| Established system rule of thumb | 1 lb fish per **8–10 gallons** |
| Tilapia ceiling with serious filtration + oxygenation | 5–6 lb/gal |
| Research optimum (growth, FCR, survival, production) | **106 fish/m³** |

**Density and growth trade off directly.** A 15-week study found weight gain
inversely related to density: final weights were **42.6 g at 150 fish/m³ but
only 25.2 g at 450 fish/m³**. Cramming more fish in gets you more smaller fish,
slower — not more yield.

### Worked example — a 300 gallon system

| Step | Value |
|---|---|
| Standing stock at 1 lb / 8–10 gal | **30–37 lb of fish** |
| At 1–1.5 lb harvest weight | ~25–35 fish |
| Grow-out time | 6–9 months |
| Staggered cohorts → harvest rate | **~3–5 fish/month** |
| Live weight | ~4–7 lb/month |
| **Edible fillet** (tilapia dress out ~33–40%) | **~2–3.5 lb/month** |

**A 300-gallon home system yields roughly two to three and a half pounds of
fillet a month.** That is a real protein supplement. It is not a food supply,
and it's far below what most people assume before they run the numbers.

## 4. How big a space do you need?

The professional method sizes **plant area against daily feed**, not against
tank volume. This is the feed rate ratio:

| Growing method | Feed rate |
|---|---|
| **Deep water culture / raft (DWC)** | **60–100 g/m²/day** |
| Media grow beds | 15–40 g/m²/day |
| NFT (nutrient film technique) | 15–25 g/m²/day |

By crop: **40–50 g/m²** for leafy greens, **50–80 g/m²** for fruiting
vegetables. The canonical UVI figure (Rakocy) is 60–100 g/m²/day, with systems
able to biologically process up to 180 g/m²/day at capacity. All of these assume
standard 32%-protein feed.

**Note the 4× spread between methods.** Media beds need two to four times more
area than DWC for the same feed load, because in DWC the water column itself
does more of the nitrification work. Choosing raft over media beds is the
single biggest space lever available.

### Practical footprints

| Scale | Footprint |
|---|---|
| Small home system | 100–300 gal tank + 20–40 sq ft grow bed → **~50–100 sq ft** total with walkways |
| Garage corner, patio, or small greenhouse | Comfortably fits the above |

**Space is rarely the binding constraint.** Power reliability and *heat* are.
Tilapia want roughly 25–28 °C; holding that through winter is a large, constant
energy cost that dwarfs the pumps and is the reason most temperate home systems
quietly fail in their first January.

## 5. How fast do the vegetables grow?

Genuinely faster — this part of the pitch holds up.

| Crop | Aquaponics / hydro | Soil |
|---|---|---|
| **Lettuce** | **~28 days** | 60–100 days |
| **Basil** | 3–4 weeks to first harvest | 6–8 weeks |
| Leafy greens generally | **30–50% faster** (Utah State) | — |
| Fruiting crops (tomato, pepper, cucumber) | 2–4 months, and harder | — |

Some sources claim tomatoes in 30–45 days. **Discount that** — it isn't credible
for seed-to-harvest in any system, and fruiting crops are exactly where
aquaponics struggles on nutrients anyway.

### The calorie problem

Lettuce and basil are essentially calorie-free. Aquaponics produces **vitamins,
minerals, and some protein — not calories.**

Calories come from grains, potatoes, beans, and fats, and aquaponics does none
of those well. Whatever else it is, it is not a food-security system on its own.
Treat it as **fresh greens plus a modest protein supplement** alongside stored
staples.

## The Qihang listings

**Supplier: Guangzhou Qihang Imp&exp Co., Ltd.** ("QihangRAS"), Verified
Supplier, offering minor and drawing-based customisation.

Note **"Imp&exp"** — import/export in the registered name usually indicates a
**trading company rather than a factory**, exactly the case
[`sourcing-from-china.md`](sourcing-from-china.md) flags. Worth confirming
before you treat quoted lead times or customisation offers as factory-direct.

### Packaged systems

| Product | Price | MOQ |
|---|---|---|
| Aquaponics System, Fish + Vegetable Indoor Mini RAS | **$2,500 / $2,100 (10–49) / $1,850 (≥50)** | 1 set |
| RAS System Aquaculture Equipment for Indoor | $2,500 | 1 set |
| China Manufacturer Fish Farming Equipment Aquaponics | $2,500 | 1 set |
| Custom Recirculating Aquaculture System Factory RAS | $2,000–3,571 | 1 set |
| Salt Water Pisciculture Fish Farming Equipment | $1,357–2,000 | 1 set |
| Tilapia Fish Hatchery Incubator | $1,850–2,000 | 1 piece |
| Customized Fish Pond Integrated Temporary Breeding | $3,150 (was $3,500) | 1 set |
| Home Use All-in-One Biological Filter, Koi Pond | $475–582 | **10 sets** |
| **PP Small Koi Pond Filter, 3–20 m³** | **$291.92** (was $328) | 1 set |

The flagship aquaponics unit carries **CE "Complies with EU standards"** and
**one product review**. Recall that CE is largely self-declared — it is a much
weaker signal than the Solar Keymark discussed in
[`solar-charging-what-works.md`](solar-charging-what-works.md).

### Red flag: the species chart

The flagship listing's imagery advertises **tilapia, catfish, carp, crucian
carp, sturgeon, cod, eel, jade perch, prawn, and Penaeus vannamei** from one
product.

That combination is not physically coherent. **Cod is a cold-water marine
species; tilapia is warm freshwater; vannamei is a tropical marine shrimp.**
They need different temperatures, different salinities, and different system
designs. A vendor presenting them as interchangeable on one skid is doing
marketing, not engineering — and this is a $2,500 purchase where the
engineering is the entire value.

### The credible part is the component catalog

| Series | Models |
|---|---|
| **Combi drum filter** | YCM-C5, YCM-B5, YCM-01 |
| **Rotary drum filter** | PM-10 (10 T/H), PM-100 (100 T/H), stainless steel RDF |
| **Bakki shower** | PP, 316L stainless, customised |

These are **standard, well-understood RAS components.** Rotary drum filters for
mechanical solids removal and Bakki showers for biofiltration and degassing are
proven designs used in koi keeping and commercial RAS worldwide. There is no
mystery in them, which makes quality easy to assess on arrival.

### Buy components, not packages

Two reasons:

1. **The engineering risk is concentrated in the packages** — one review, an
   incoherent species claim, and no published spec for the thing that actually
   matters (oxygenation capacity, system volume, sustainable daily feed load).
2. **You would be shipping water tanks across an ocean.** Tanks are bulky, cheap
   locally (IBC totes, poly stock tanks), and expensive to freight. The
   filtration and mechanical parts are high value per kilogram; the tank is not.

So invert the usual rule here: **import the mechanism, source the container
locally.** Get the drum filter, blower, and controls from a vendor like this;
buy the tank down the road.

The **$291.92 PP koi pond filter (MOQ 1)** is a sensible low-risk way to test
this supplier's build quality before committing to anything larger.

### Questions to ask before ordering

1. **What exactly is in a "set"?** Tank, drum filter, biofilter, pump, blower,
   controls? Get an itemised bill of materials.
2. **System volume and sustainable daily feed load** in grams — this is the
   spec that determines actual production, and it's absent from the listing.
3. **Oxygenation spec.** Blower capacity, or whether an oxygen generator is
   included (the hatchery listing pictures one; the aquaponics one may not).
4. **Which single species is it actually designed for**, at what temperature and
   salinity?
5. **Ocean freight and duty on top of the quoted price** — on a bulky $2,500
   item this can be a large fraction of landed cost.
6. **Factory or trading company?** Ask for the business license.

## Verdict

**As a food system:** genuinely works for **leafy greens plus a modest fish
protein supplement.** Realistically, a 300-gallon home system gives you salad
and herbs year-round plus 2–3.5 lb of fillet a month. Fruiting crops need
supplementation; calories it does not produce at all.

**As a preparedness system:** the weakest thing in these records, because it is
the only food source that **dies in hours without electricity.** If you build
one, budget the battery-backed aeration first and treat it as a fresh-food
supplement to stored staples — never as the staple itself.

**As a purchase:** buy the drum filter and biofilter components, build the tank
locally, and start with the $292 unit to test quality.
