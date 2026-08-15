---
name: hawaii-import-logistics
description: Ocean freight, landed cost, and port operations for moving cabinetry, windows, doors, and building materials into Oahu — Jones Act routing, Asia-direct vs Mainland transshipment, LCL vs FCL, drayage to Waipahu, demurrage and detention exposure. Use when quoting freight, choosing a routing, estimating landed cost, diagnosing a delayed or held container, or deciding how much to order at once.
metadata:
  origin: local
  business: Grandeur Design Supply / Ke'a Cabinetry / Island Home
---

# Hawaii Import Logistics

Freight and landed-cost reasoning for inbound building materials to Oahu.
Warehouse and pickup point is Waipahu, HI.

This skill covers the *movement and cost* side. For duties, AD/CVD exposure, and
regulatory filings, use `cabinet-import-compliance`.

## When to Activate

- Quoting a job where freight is a material share of cost
- Choosing between Asia-direct and Mainland-transshipped routing
- Deciding LCL versus FCL, or whether to consolidate orders
- A container is delayed, held, or accruing charges
- Estimating landed cost per unit before committing to a purchase order
- Setting reorder quantities against ocean lead times

## The structural fact that drives everything

**The Jones Act (46 U.S.C. § 55102)** requires that cargo moving between two US
points travel on a US-built, US-flagged, US-crewed vessel. Honolulu is a US
port. So:

- **Mainland → Honolulu is domestic.** Jones Act applies. The carrier set is
  small (Matson, Pasha), capacity is finite, and rates are structurally higher
  than an equivalent international leg.
- **Asia → Honolulu directly is international.** Jones Act does **not** apply.
  Foreign-flag carriers may serve it.

That asymmetry is the single biggest lever in this business. A container routed
Asia → Long Beach → Honolulu crosses into the domestic leg and picks up Jones
Act economics for the final stretch. The same container routed Asia → Honolulu
direct does not.

Direct service exists but is thinner than the West Coast lanes — fewer sailings,
fewer carriers, and less tolerance for a missed cutoff. The trade is cost and
customs simplicity against schedule flexibility.

**Always price both routings before committing on a large order.** The answer
changes with container size, sailing frequency, and how much schedule risk the
job can absorb.

## Routing decision

Work in this order:

1. **Where is the goods' origin?** Asia origin → price Asia-direct first.
   Mainland origin (domestic manufacturer, US distributor) → Jones Act leg is
   unavoidable; optimize on carrier and consolidation instead.
2. **What is the volume?** Below roughly a half-container, LCL or consolidation
   usually wins. At or above a full container, FCL almost always wins on a
   per-unit basis and removes deconsolidation delay.
3. **What is the schedule risk?** A job with a firm install date and no buffer
   should not ride a thin direct service with fortnightly sailings. Pay for the
   reliable lane.
4. **What is the cargo's damage profile?** LCL means your goods are handled at a
   consolidation point and share a container with unknown neighbors. For
   finished cabinet boxes and glass, that handling is where damage enters. FCL
   at a marginal premium is often cheaper than the claims rate on LCL.

## LCL versus FCL

| | LCL | FCL |
| --- | --- | --- |
| Cost basis | Per cubic meter / revenue ton | Flat per container |
| Break-even | Small volumes | Typically past ~50–60% container fill |
| Handling | Consolidation + deconsolidation, more touches | Sealed origin to destination |
| Damage exposure | Higher — shared container, more handling | Lower |
| Schedule | Adds deconsolidation days at destination | Faster to available |
| Best for | Sample orders, fill-in stock, single-job specials | Program buys, container-level SKUs |

The break-even is a volume calculation, not a rule of thumb — run it per
shipment. When a shipment lands near the break-even, FCL usually wins once
damage and deconsolidation delay are priced in, because those costs are real but
easy to leave out of the comparison.

## Landed cost

Never quote from unit price alone. Landed cost per unit is:

```
  ex-works unit price
+ origin handling / export clearance
+ ocean freight (allocated per unit)
+ fuel and applicable surcharges
+ marine insurance
+ duty and any AD/CVD  ── see cabinet-import-compliance
+ customs brokerage and entry fees
+ terminal handling at Honolulu
+ drayage Honolulu → Waipahu
+ demurrage / detention actually incurred
+ receiving labor and damage/shrink allowance
─────────────────────────────────────────
= true landed cost per unit
```

Two lines are habitually understated and both are avoidable:

- **AD/CVD.** On wooden cabinets from China this is not a rounding error and can
  exceed the goods' value. See `cabinet-import-compliance` before assuming a
  duty rate.
- **Demurrage and detention.** These accrue daily and compound with any
  clearance problem. They are the cost of being unprepared at the dock, not a
  freight cost.

**Placeholder — fill from your own records:** current per-container freight by
lane, brokerage fee schedule, drayage rate to Waipahu, insurance rate, and your
historical damage/shrink percentage. Until those are recorded here, any landed
cost this skill helps produce is a structure with estimates in it, not a quote.

## Demurrage and detention

Two different clocks, frequently confused:

- **Demurrage** — your container is sitting at the terminal past free time. You
  are being charged for occupying the terminal's yard.
- **Detention** — you have taken the container out but not returned it empty
  within the allowed window.

Both are daily, both escalate in tiers, and both are largely preventable. The
controllable inputs are: entry filed and cleared before arrival, broker holding
complete documents, drayage booked ahead of discharge, and a receiving crew
available to strip and return.

When a container starts accruing, the diagnostic order is:

1. Is there a **customs hold**? (Entry problem, exam, PGA hold, AD/CVD question.)
   Resolve with the broker — this is document work, not a trucking problem.
2. Is there a **carrier hold**? (Unpaid freight, missing release.) Usually
   cleared same-day once identified.
3. Is it a **drayage capacity** problem? Oahu trucking is a small pool; a missed
   booking can cost days.
4. Is it a **receiving** problem on our side? Container out, nowhere to put it.

Escalate on the first, not the last. Most multi-day accruals trace to a document
issue that nobody surfaced early.

## Port and drayage

- Discharge is at Honolulu Harbor (Sand Island terminal complex).
- Waipahu is a short inland move — roughly 15 miles. Drayage is cheap relative to
  the ocean leg but capacity-constrained, so book against the vessel ETA rather
  than against actual discharge.
- Oahu has no rail alternative and one commercial harbor of consequence. There
  is no rerouting your way out of a congestion event; the only lever is time.

## Ordering against lead time

Ocean lead time to Oahu is long enough that reorder decisions must be made
against forecast, not against current stock. Use `inventory-demand-planning`
(vendored ECC skill) for the safety-stock math; feed it these Hawaii-specific
inputs:

- Lead time is **longer and more variable** than a Mainland operation's. Safety
  stock must cover lead-time variability, not just demand variability.
- **Sailing frequency quantizes your reorder points.** If the direct service
  sails every two weeks, a two-day slip in a purchase order costs fourteen days,
  not two.
- **Container economics create minimum order quantities** that may exceed what
  demand alone would justify. That tension — order a full container of slow
  movers, or pay LCL rates on the fast movers — is a recurring decision, not a
  one-time setup.

**Placeholder — fill from your own records:** actual observed lead times by
supplier and lane, sailing frequency for the services you use, and your
suppliers' MOQs.

## Checklist before committing a purchase order

- [ ] Both routings priced (Asia-direct and Mainland-transshipped) where origin allows
- [ ] LCL/FCL break-even actually computed for this volume
- [ ] Duty and AD/CVD exposure confirmed via `cabinet-import-compliance`
- [ ] TSCA Title VI and Lacey Act documentation confirmed available from supplier
- [ ] Landed cost per unit calculated, not extrapolated from a previous shipment
- [ ] Reorder timed against sailing schedule, not against stock level alone
- [ ] Receiving capacity available in the arrival window

## Caveat

Carrier services, sailing frequencies, rates, and free-time allowances change.
Verify current schedules and tariffs with the carrier or broker before quoting a
customer. The Jones Act structure is stable; everything downstream of it is not.
