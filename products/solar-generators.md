# Solar Generators / Portable Power Stations

Captured 2026-09-08. Sources: [PopSci — best solar generators 2026](https://www.popsci.com/reviews/best-solar-generators/),
[Entropy Survival — four-brand comparison](https://entropysurvival.com/blogs/news-views/ecoflow-vs-jackery-vs-bluetti-vs-anker-2026-comparison),
[PowerGen Store](https://powergenstore.com/blogs/news/ecoflow-vs-jackery-vs-bluetti-vs-anker-solix-which-solar-generator-is-best),
[UL Standards — counterfeit lithium cells](https://ulse.org/insight/ul-standards-engagement-anti-counterfeiting-counterfeit-lithium-ion-cells-and-batteries/)

## The answer to your sourcing question, up front

**The reputable brands in this category already *are* Chinese companies.**
EcoFlow, Bluetti, Anker, and Jackery are all Chinese. There is no Western brand
to undercut and no factory arbitrage to find — you would be trying to source
around companies that buy cells at a volume you cannot approach.

This is also the **one category where buying unbranded is actively dangerous.**
See the safety section below.

## The only spec that matters first: LiFePO4

| Chemistry | Cycles to 80% capacity | Real-world life |
|---|---|---|
| **LiFePO4 (LFP)** | **3,000–6,000** | 10–17 years of regular use |
| Standard Li-ion / NMC | 500–800 | Degrades notably under outage-use patterns |

That is a 4–10× difference in usable life. For a preparedness purchase — where
the unit may sit for years and then be cycled hard — **LFP is not optional.**
All four major brands now use LFP on their core models, which makes them broadly
comparable on longevity and pushes the decision to features.

Reject any unit that doesn't state LiFePO4 explicitly.

## Brand positioning

| Brand | Strength | Notable |
|---|---|---|
| **EcoFlow** | Charging speed + smart features | X-Stream: ~80% in ~50 min. DELTA 3 Plus: 1,000 W dual MPPT solar in |
| **Bluetti** | Massive expandable capacity | AC200L accepts 1,200 W solar. AC200MAX charges in ~2 hrs |
| **Anker (Solix)** | Fast charging | Claims 3,000 cycles to 80% on LFP |
| **Jackery** | Simplicity and portability | Least complex; good for non-technical users |

All four now span every price tier. Practical decision order:

1. **LiFePO4** — non-negotiable.
2. **Solar input ceiling** — this governs how fast you can recharge off-grid,
   and it is the spec people under-buy. Bluetti's 1,200 W and EcoFlow's 1,000 W
   are the leaders.
3. **Capacity vs. expandability** — Bluetti if you expect to grow the bank.
4. **Charge speed** — matters if you're topping up from a generator or a brief
   grid window; irrelevant if you're only ever charging from solar.
5. **Output wattage and surge** — check against the actual loads you plan to
   run, not the nameplate.

## Sizing reality check

A portable power station is not a house generator. Budget by load:

- **Phones, radios, lights, laptop, CPAP** — a 500–1,000 Wh unit covers days.
- **Fridge (~1–2 kWh/day)** — needs 2 kWh+ plus real solar input to sustain.
- **Well pump, electric cooking, AC** — this is a whole-home battery and
  generator question, not a portable-power-station question.

Pair with a **water-pumping and RO** load if that's the plan: an electric
watermaker at 30 L/hr draws roughly 11 A at 12 V. See
[`electric-watermakers.md`](electric-watermakers.md).

## Safety — why not to source these generically

Counterfeit and non-compliant lithium cells are a documented fire hazard, and
the failure is not gradual:

- Counterfeit cells have been found **missing internal protective devices** —
  the PTC (positive temperature coefficient) element and the CID (current
  interrupt device) that protect against external short circuit and overcharge
  respectively.
- Without them, cells are **prone to thermal runaway.**
- Industry reporting describes an influx of **relabelled or home-built cells**
  entering consumer and light-mobility markets.
- The manufacturing-hygiene gap is stark: legitimate cell production is
  described as resembling "the cleanest hospital you could imagine," while some
  audited facilities had staff watering plants beside the production line or
  smoking on the floor.

A power station is a large lithium pack that will live in your home, charge
unattended, and sit for long periods. **This is the wrong place to save 30%.**
Buy a branded LFP unit with real certification.

## Recommendation

Buy branded — EcoFlow, Bluetti, Anker, or Jackery — with **LiFePO4 confirmed**,
sized to your actual load list, and prioritising solar input wattage. Expect to
pay retail; there is no credible sourcing shortcut in this category, and the
downside of the shortcut is a house fire.

Where you *can* save: buy the panels separately. Generic mono-crystalline panels
with standard MC4 connectors are a commodity, are not a fire risk in the same
way, and often cost far less than brand-matched folding panels. Confirm voltage
and current are inside your unit's MPPT input window before buying.
