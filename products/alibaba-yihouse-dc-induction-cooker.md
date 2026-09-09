# Alibaba — Yihouse 24V/48V DC Double Induction Cooker

| Field | Value |
|---|---|
| Listing title | "24V/48V DC Double Induction Cooker Solar Powered Dual Burner Induction Stove for RV Camper Truck Off Grid" |
| Supplier | Zhongshan Yihouse Electric Co., Ltd. |
| Platform | Alibaba.com ("Super" badge) |
| Found via | search: "solar cooker for home" |
| Captured | 2026-09-08 |
| Screenshot | [`images/alibaba-yihouse-dc-induction-cooker.png`](images/alibaba-yihouse-dc-induction-cooker.png) |

## This is not a solar cooker

It surfaced under a "solar cooker for home" search, but it is a completely
different device from the thermal solar cookers in
[`solar-cookers.md`](solar-cookers.md).

- A **solar cooker** converts sunlight directly into heat. No electricity, no
  battery, no wiring.
- **This** is an electric induction hob with a DC input. "Solar powered" means
  only that you can wire it to a solar/battery system. It is a *load*, not a
  generator.

Keep them straight — they solve different problems and fail for different
reasons.

## Pricing

| Quantity | Unit price |
|---|---|
| 1 piece (MOQ) | $184.00 |
| 100–999 pieces | $180.00 |
| ≥1,000 pieces | $175.00 |
| "Sample" | **$190.00** |

Two things to notice. The **sample costs more than simply ordering 1 piece**
($190 vs $184) — order the single piece. And the price barely moves with volume
(5% across 1,000 units), which is unusual for a factory and is a soft signal of
a trading company or very thin margin.

## Supplier signals

| Signal | Value | Read |
|---|---|---|
| Years on Alibaba | ~9 (partially cut off in screenshot — verify) | Solid, far better than a 2-year store |
| Store rating | 4.4 ★ on **1,384 reviews** | Big sample; mediocre score |
| Positive reviews | 93.4% | Acceptable, not excellent |
| Units sold, this listing | **4** | Very low — new or unpopular SKU |
| Extras | Free replacement parts, online technical support | Genuinely good signs |

Better-established than the [Vooma stove supplier](alibaba-vooma-camping-stove.md)
(9 years and 1,384 reviews vs 2 years and 30). But 4.4★/93.4% is middling, and
**4 units sold** means this specific product has almost no field history.

## The real engineering merit

There is a genuine reason this product category exists: **it skips the
inverter.**

A normal induction cooktop is a 120V AC appliance. Running one off a battery
bank needs a 2,000–3,000 W pure sine inverter — which costs money, wastes
10–15% in conversion, and draws idle current whenever it's on. A native
24V/48V DC unit eliminates all of that.

Second real advantage: **no combustion.** No carbon monoxide, no ventilation
requirement, no propane in a sealed space. In a van or small boat that is a
meaningful safety improvement, and it's why all-electric builds are a growing
niche.

## The power budget — read this before buying

Induction is a high-power load, and the arithmetic is unforgiving.

| Load | At 24V | At 48V |
|---|---|---|
| 1,500 W (one burner) | **~78 A** | ~39 A |
| 3,000 W (both burners) | **~156 A** | ~78 A |

(1,500 W at 24V with a 0.8 efficiency factor works out to 78 A.)

**156 A continuous is 2/0 AWG cable territory** with fusing to match. That is
not incidental wiring — it is a significant part of the install cost, and the
listing says nothing about it. **Buy the 48V version if you have the choice**;
it halves the current and everything downstream gets easier.

## The pictured system does not work

The listing photography shows the cooktop beside **two NPP 12V 55Ah AGM
batteries** and a couple of solar panels. Run the numbers:

| Step | Value |
|---|---|
| 2× 12V 55Ah in series | 24V 55Ah = **1,320 Wh** nominal |
| Lead-acid, 50% max depth of discharge | ~660 Wh usable |
| Peukert derating at induction-level current | lead-acid can deliver **as little as 60%** of rated capacity at high discharge |
| Realistically usable | **~400 Wh** |
| Cooking time at 1,500 W | **~16 minutes** |
| Cooking time at 3,000 W (both burners) | **~8 minutes** |

**Ten to twenty minutes of cooking**, and that's while pulling roughly 1.5–2.8C
from AGM batteries — a rate that will shorten their life considerably.

The photo is marketing composition, not a system specification. Do not read it
as "this is what you need to run it."

## Wrong battery chemistry

AGM lead-acid is close to the worst possible choice for this load. An AGM cell
rated at C/20 delivers only about **60% of rated capacity at C/1**, and
high-current loads like induction cooktops are specifically called out as
causing a ~40% capacity loss. LiFePO4 has **minimal Peukert effect** — capacity
stays near its rating even at high loads, and voltage stays flatter.

If you buy this cooktop, pair it with **LiFePO4**, and size it properly: a real
all-electric cooking build wants a bank in the 400 Ah @ 12V / 200 Ah @ 24V range
or larger. See [`solar-generators.md`](solar-generators.md).

## Cookware constraint

Induction requires **ferromagnetic** cookware — cast iron and magnetic
stainless. **Aluminum, copper, and glass will not work at all.**

This matters for a camping or preparedness kit, where most lightweight cookware
is aluminum — including the kettle pictured in the
[Vooma stove listing](alibaba-vooma-camping-stove.md). Test every pot with a
magnet before committing to induction.

## Why this is the wrong tool for preparedness

Cooking is one of the **worst possible loads** to put on a battery bank: high
power, short duration, and there is an absurdly cheap alternative.

A 20 lb propane tank holds roughly 430,000 BTU ≈ **126 kWh** of energy, and
costs about **$26–40 to refill**. Storing 126 kWh in LiFePO4 would cost tens of
thousands of dollars.

**One $30 propane refill carries the cooking energy of an entire garage of
batteries.** For stockpiling, that comparison ends the discussion — and it
doesn't dent the [propane conclusion](stoves-and-fuel.md) at all.

Reserve your battery capacity for loads that genuinely can't be done another
way: refrigeration, lighting, comms, electronics, water pumping.

## Where it *is* the right tool

An **all-electric van, RV, or boat build** that has already committed to a large
LFP bank and wants propane out of the vehicle entirely — for CO safety, space,
or regulatory reasons. In that context the DC-native input is a real advantage
over an AC hob plus inverter, and this unit at $184 is priced reasonably.

That is a legitimate niche. It just isn't a preparedness fuel strategy.

## Sourcing assessment

**Tier 2 — only with verified certification.** This is a ~3 kW switching
power-electronics appliance. The NPP batteries in the photo carry UL and CE
marks, but **that is the batteries, not the cooktop** — no certification is
shown for the unit being sold. An induction hob failure at this power level is a
fire risk.

Before ordering:

1. **Demand CE/UL documentation for the cooktop** and validate it with the
   issuing body, not the supplier's PDF.
2. **Confirm 24V vs 48V** — is it auto-sensing across both, or two separate
   SKUs? The title implies both; confirm in writing.
3. **Get the actual wattage per burner** and whether both can run simultaneously
   at full power.
4. **Ask for the recommended cable gauge and fuse rating.** A supplier who can't
   answer this hasn't engineered the product.
5. **Order 1 piece at $184** (not the $190 "sample") and test it on a real bank
   before any volume commitment.

See [`sourcing-from-china.md`](sourcing-from-china.md) for the full risk tiers.

## Verdict

Well-priced for what it is, from a reasonably established supplier, solving a
real problem — for **all-electric vehicle builds**. For your preparedness
stack it's the wrong layer: propane stores the same energy for a rounding error
of the cost, and induction adds a cookware constraint on top.

If you want a genuinely solar-powered cooking option, that's the thermal solar
cooker in [`solar-cookers.md`](solar-cookers.md) — a $30–60 panel cooker plus a
WAPI, which needs no battery, no wiring, and no fuel at all.
