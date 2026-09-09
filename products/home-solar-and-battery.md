# Home Solar + Battery: Full vs Partial Off-Grid

Captured 2026-09-08. Sources: [GreenLancer — solar tax credit ending](https://www.greenlancer.com/post/solar-tax-credit-ending),
[SolarInsure — final OBBB tax credit changes](https://www.solarinsure.com/final-changes-to-solar-tax-credit-from-h-r-1),
[IntegrateSun — partial vs whole-home backup](https://www.integratesun.com/post/partial-vs-whole-home-battery-backup),
[Helios — whole-home vs partial](https://heliosenergyglobal.com/guides/whole-home-backup-vs-partial-backup),
[Anern — the truth about autonomy days](https://www.anernstore.com/blogs/off-grid-solar-solutions/myth-vs-reality-autonomy-days),
[SunForgeLab — off-grid sizing](https://sunforgelab.com/blog/guides/off-grid-solar-system-sizing-guide/),
[SunForgeLab — all-in-one inverters 2026](https://sunforgelab.com/blog/reviews/best-all-in-one-solar-inverters-2026/),
[Savolture — battery storage cost 2026](https://savolture.com/blog/solar-battery-storage-cost-2026/)

## Read this first: the federal credit is gone

**The 30% residential solar tax credit (Section 25D) ended on 31 December
2025.** The One Big Beautiful Bill, signed 4 July 2025, terminated it — and it
went from 30% to **zero on 1 January 2026**, with no phase-down and no
transition period. Section 25C (heat pumps and supporting panel upgrades) ended
the same day.

If you were working from any cost estimate that mentions "before the federal tax
credit," **add 30% back.** Nearly every published figure still assumes it.

**One route survives:** the business-side **Section 48E credit remains through
the end of 2027**, and it covers residential **leases, PPAs, and prepaid solar**
— where the provider owns the system and claims the credit. That's now the only
way federal money reaches a residential project.

So there's a real strategic fork:

| Ownership | Federal credit | Trade-off |
|---|---|---|
| **You buy it** | **None** | Full ownership, no escalator, best long-run economics — but you eat the whole capital cost |
| **Lease / PPA / prepaid** | 30% via 48E (provider claims it, through 2027) | Lower entry cost; you don't own the asset, and terms often carry escalators |

Check your **state and utility** incentives separately — those are unaffected by
this and in some states are substantial.

## The three architectures

| | Grid-tied, no battery | Grid-tied + battery (hybrid) | Full off-grid |
|---|---|---|---|
| **Behaviour in an outage** | **Shuts down** (anti-islanding is mandatory) | Keeps running | No grid to lose |
| **Sized for** | Annual average production | Annual average + a backup window | **The worst month of the year** |
| **System derate factor** | ~0.86 | ~0.86 | **~0.70** |
| **Cost per useful kWh** | Lowest | Middle | Highest by a wide margin |

The middle column is the one most people actually want and the one most people
skip past. A plain grid-tied array **does not** power your house in a blackout —
it disconnects by law to protect line workers. If resilience is your goal, the
battery is the point, not the panels.

## Why full off-grid is usually the wrong call if the grid exists

Off-grid economics are dominated by **December**, not by your annual average.

- December autonomy typically runs **40–60% shorter** than June.
- Winter peak-sun-hours are often **half** the annual average. A Vermont site
  averaging 4.0 PSH may see only **2.3 PSH in December**.
- Sizing for the worst month means being **massively overbuilt for summer** —
  you pay for capacity that spills for eight months a year.
- Off-grid also carries a worse derate (0.70 vs 0.86), because you're paying
  round-trip battery losses on nearly every kWh instead of consuming most of it
  directly.

**Grid-tied + battery gets you ~95% of the practical resilience without paying
for December.** True off-grid makes sense when the grid genuinely isn't
available — a remote parcel, or a utility connection quote in the tens of
thousands — not as a resilience upgrade to a connected home.

## Partial vs whole home — the actual numbers

| Scope | Battery | Installed cost |
|---|---|---|
| **Essential loads** — fridge, lights, Wi-Fi, medical devices, a few outlets | 5–13 kWh | **$10,000–19,000** |
| Single-unit essential system | 13 kWh | $12,000–18,000 |
| Medium home, broader coverage | 20–27 kWh | $22,000–32,000 |
| **Whole home** — HVAC, EV charger, electric range, everything | 2+ batteries | **$22,000–40,000+** |

Add the **critical-loads subpanel** for partial backup: materials $200–500,
electrician labour $300–800, plus $100–200 per additional circuit. Budget
**$500–1,500** all in. This subpanel is what makes partial backup work — the
essential circuits get moved onto their own breaker box that the battery feeds.

### Runtime is about what you connect, not just capacity

The same battery behaves completely differently depending on load:

| Load | Runtime from one battery |
|---|---|
| Full house output | **~2 hours** |
| Critical loads only | **10–12+ hours** |
| Critical loads, 10–13 kWh usable, no solar recharge | **2–3 days** |

That 2-hours-vs-12-hours spread is the whole argument for a critical-loads
panel. Restricting *what* draws from the battery multiplies runtime far more
cheaply than buying more battery.

### The honest recommendation

**Partial backup handles about 90% of what you actually need, at roughly half
the cost.** Go whole-home only if one of these applies:

- **Medical equipment** that cannot be interrupted
- **An all-electric home with no gas fallback** — no gas heat, cooking, or hot
  water to fall back on
- **Multi-day outages** as a routine expectation (high fire-risk zones, PSPS
  territory, storm-prone rural service)

## The loads that break the budget

Five loads account for most of the gap between a $12,000 system and a $40,000
one:

1. **Electric resistance heat**
2. **Central air conditioning**
3. **Electric water heater**
4. **Electric range / oven**
5. **EV charging** — and **well pumps**, for surge current rather than energy

The cheapest capacity you will ever buy is **moving these off electricity.**
Propane heat, propane cooking, and a propane water heater shrink the battery you
need dramatically — and propane has
[indefinite shelf life and the cheapest cost per BTU](stoves-and-fuel.md).

This is the same finding as the [DC induction
cooker](alibaba-yihouse-dc-induction-cooker.md): high-power thermal loads are
the worst possible things to put on a battery, and there is a dirt-cheap
alternative.

## Equipment and what it costs

### Hybrid inverters

| Unit | Price | Notes |
|---|---|---|
| **EG4 6000XP** | **~$1,500** | Best overall for DIY. 6 kW continuous, dual MPPT, 500 V PV input, 10-year warranty |
| Victron MultiPlus-II 48/5000 | ~$4,500 | Premium; excellent ecosystem and monitoring |
| Sol-Ark 15K | ~$7,000 | Premium grid-tied/hybrid; strong off-grid capability |

### Batteries — DIY vs turnkey is roughly 2×

| Format | Price | Per kWh |
|---|---|---|
| Server-rack LFP, 100 Ah / 5.12 kWh | $1,400–1,900 | **~$275–370/kWh** |
| Server-rack LFP cabinet, 314 Ah / 16.08 kWh | $4,200–5,500 | **~$260–340/kWh** |
| Branded turnkey (Powerwall-class), 13.5 kWh | $8,000–10,000 | **~$600–750/kWh** |

Server-rack LiFePO4 is roughly **half the cost per kWh** of a branded turnkey
battery. With the 30% credit gone, that delta matters more than it did a year
ago.

A complete EG4 6000XP plus two PowerPro batteries (28.6 kWh) lands around
**$20,000–27,000 installed** — and note that most published figures for systems
like this still say "before the federal tax credit," which no longer exists for
owner-purchased systems.

### UL 9540 is a hard gate, not a nice-to-have

**Most US jurisdictions require both a permit and UL 9540 certification for the
battery system.** Systems without a UL 9540 listing face **permit rejection,
re-application fees, and project delays.**

This is decisive for sourcing: you **cannot** buy generic Alibaba battery
modules for a permitted home installation, however good the price looks. Look
for UL 1973 / UL 9540 / UL 9540A on the datasheet — reputable server-rack
vendors (EndurEnergy, EG4, Eco-Worthy and similar) list them explicitly. See
[`sourcing-from-china.md`](sourcing-from-china.md), where lithium is Tier 3.

## Off-grid sizing rules

If you are genuinely going off-grid:

1. **Use winter sun hours, not the annual average.** This is the single most
   common and most expensive sizing error.
2. **Days of autonomy:** 2–3 days is typical **with a generator**; 3 days
   minimum without; **5 days** for a year-round homestead; 7+ for critical
   applications.
3. **Derate 0.70**, not 0.86 — panel temperature, wiring, controller, inverter,
   and battery round-trip losses all stack.
4. **Add margin:** 20–30% if you expect load growth, plus 10–20% for unexpected
   consumption and extra-cloudy stretches.
5. **Put a generator input on the inverter. Always.** This fundamentally changes
   the arithmetic — you size for the *interval between generator runs* rather
   than for worst-case weather, which can cut system cost substantially.

### The generator is the winter answer

A **propane generator** is the correct backstop, and it closes the loop with the
fuel research: propane's **indefinite shelf life** is exactly what a backup
generator needs, since it may sit unused for months at a time. Gasoline, at
[3–6 months](stoves-and-fuel.md), is the wrong fuel for a standby machine.

Trying to eliminate the generator by adding panels and batteries is how off-grid
budgets triple. The generator covers the handful of December weeks that would
otherwise dictate the size of the entire system.

## Decision framework

**1. Is the grid available at reasonable cost?**
Yes → grid-tied + battery, essentially always. No / quoted in the tens of
thousands → off-grid.

**2. What's your real outage profile?**
Hours, occasionally → small battery, critical loads only. Days, regularly →
larger partial or whole-home. Weeks → you need a generator regardless of how
much battery you buy.

**3. All-electric, or do you have a gas fallback?**
Gas heat, cooking, and hot water shrink the required battery enormously. If
you're all-electric, either accept whole-home cost or convert the big thermal
loads to propane first — the conversion is usually cheaper than the battery it
saves.

**4. DIY-capable, and is your jurisdiction workable?**
DIY roughly halves cost per kWh, but UL 9540 and permitting are non-negotiable
in most places. Confirm what your AHJ will accept **before** buying anything.

**5. Buy or lease?**
With 25D gone, cash purchase has no federal support; lease/PPA keeps 30% via 48E
through 2027 but you don't own the asset. Run both.

## Recommendation

For most people with a working grid connection:

**Grid-tied hybrid inverter + a 13–20 kWh LFP battery + a critical-loads
subpanel, roughly $12,000–20,000 installed** — plus a propane generator for
multi-day events. Move heating, cooking, and hot water to propane if they aren't
already; that single decision does more for your resilience-per-dollar than any
amount of extra battery.

Skip full off-grid unless the grid genuinely isn't an option. You would be
buying December capacity that sits idle for most of the year.
