---
name: project-quoting
description: Turn plans, measurements, or a site visit into a priced proposal for cabinetry, windows, doors, flooring, countertops, and lighting. Covers intake completeness, takeoff structure, landed-cost pricing, allowances and exclusions, lead-time commitments, and proposal format. Use when the user has received measurements or plans, is building a quote or proposal, is revising pricing, or is deciding what to include or exclude in scope.
metadata:
  origin: local
  business: Grandeur Design Supply / Ke'a Cabinetry / Island Home
---

# Project Quoting

Takes a project from intake to a proposal that can be sent and defended.

Sits between the lead workflow (`lead-routing`, `ghl-sms-templates`) and the
supply side (`hawaii-import-logistics`, `cabinet-import-compliance`).

## When to Activate

- Measurements or plans arrived at admin@grandeurdesignsupply.com
- Building or revising a proposal
- Deciding scope boundaries — what is included, allowanced, or excluded
- A customer is pushing back on price and the quote needs defending or restructuring
- Committing a lead time in writing

## Stage 1 — Intake completeness

Do not start a takeoff on an incomplete package. An underspecified quote gets
revised, and revisions cost more than the delay of asking.

**Minimum to quote cabinetry:**
- [ ] Room dimensions with ceiling height
- [ ] Appliance sizes and locations (panel-ready or not)
- [ ] Sink and plumbing locations
- [ ] Window and door positions affecting cabinet runs
- [ ] Door style, finish, and species
- [ ] Box construction expectation (frameless vs face-frame)
- [ ] Countertop material, if we are supplying it

**Minimum to quote windows and doors:**
- [ ] Rough opening dimensions, per opening
- [ ] Operation type per opening (casement, sliding, picture, fixed)
- [ ] Glazing and performance expectations
- [ ] Frame material and finish
- [ ] Whether impact-rated or energy-performance requirements apply
- [ ] Installation scope — supply only, or supply and install

**Always establish, regardless of category:**
- [ ] Target install or delivery date
- [ ] Site access and delivery constraints
- [ ] Who is doing the installation
- [ ] Whether this is competing against another bid

If material items are missing, ask for them in **one** message rather than
serially. Use `ghl-sms-templates` for the request — the established pattern is a
single specific question, not a checklist dump at the customer.

## Stage 2 — Takeoff

Structure the takeoff so it survives a scope change without a rebuild:

1. **Itemize by location, then by unit.** Kitchen → base run → each cabinet by
   size and type. Not a lump sum per room.
2. **Every line carries a SKU or a spec**, not a description. "36in sink base,
   shaker, white" is a spec. "Sink cabinet" is a future dispute.
3. **Quantities separate from pricing.** The takeoff is a count; pricing is
   applied to it. Keeping them separate means a price change does not require
   re-counting.
4. **Flag every assumption inline.** Anything inferred rather than measured is an
   assumption and belongs in the exclusions.

## Stage 3 — Pricing

Price from **landed cost**, never from supplier unit price.

For imported goods, landed cost comes from `hawaii-import-logistics` — ex-works
price plus freight, duty, AD/CVD, brokerage, terminal, drayage, and damage
allowance. Quoting from the supplier's price list and adding a flat markup is how
freight-heavy jobs lose money on Oahu, because ocean freight is a much larger
share of landed cost here than a Mainland operation's markup assumptions account
for.

Sequence:

```
landed cost per unit  (see hawaii-import-logistics)
× quantity from takeoff
+ freight allocated to this job
+ install labor, if in scope
+ contingency for site conditions
= project cost
÷ (1 − target margin)          ← margin as a divisor, not a markup multiplier
= quoted price
```

Margin as a divisor is the common arithmetic error worth stating explicitly:
a 30% margin is `cost / 0.70`, not `cost × 1.30`. The latter yields 23%.

**Placeholder — fill from your own records:** target margin by category
(cabinetry, windows, doors, flooring, countertops typically differ), install
labor rates, contingency percentages by job type, and any volume or program
pricing from suppliers. Until these are recorded, this skill produces a correct
structure with your estimates in it — not a number to send.

## Stage 4 — Scope, allowances, exclusions

The three most common sources of margin loss, in order:

**Undefined finish and hardware.** "Cabinet hardware" spans an order of
magnitude. Either specify exactly, or set a stated per-unit allowance.

**Site conditions.** Out-of-square walls, unlevel floors, and undisclosed
structural conditions turn a supply job into a fabrication job. Exclude explicitly
or price the contingency.

**Scope creep at install.** "While you're here" is unbilled work unless the
proposal says otherwise. State what triggers a change order.

Every proposal should carry an explicit exclusions section. Standard candidates:

- Demolition and disposal of existing materials
- Plumbing, electrical, and gas disconnection or reconnection
- Structural modification, wall or soffit alteration
- Permits and inspection fees
- Countertop templating and fabrication, if supply-only
- Finish carpentry beyond the supplied scope
- Conditions not visible at time of measurement

## Stage 5 — Lead time

Lead time is a commitment. Treat it as one.

Build it from the actual chain and state the driver:

```
supplier production time
+ ocean transit          ← the long pole for imported goods
+ customs clearance      ← add buffer; holds are routine, not exceptional
+ drayage and receiving
+ any local fabrication
= realistic availability
```

Two Hawaii-specific rules:

- **Quote a range, not a date**, and name the assumption it rests on. "10–14
  weeks from deposit and final approved measurements" is defensible. "12 weeks"
  is a promise you do not control.
- **Sailing frequency quantizes slippage.** A two-day delay in approval can cost
  two weeks if it misses a sailing. Say this to the customer *before* the delay,
  not after — it converts a complaint into a reason to decide promptly, and it is
  the value hook the existing SMS follow-up patterns already lean on.

## Stage 6 — Proposal format

Structure that holds up under scrutiny:

1. **Project summary** — scope in two or three sentences
2. **Itemized scope** — by location, with specs, quantities, and per-line pricing
3. **Allowances** — stated per-unit, with what happens above and below
4. **Exclusions** — explicit
5. **Lead time** — as a range with its stated assumption
6. **Terms** — deposit, milestones, balance, change-order process
7. **Validity period** — required; see below
8. **Next step** — one clear action

**Always state a validity period.** Ocean freight rates, supplier pricing, and
duty exposure all move. An open-ended quote is a rate risk you are absorbing on
the customer's behalf, for free, for as long as they take to decide. Thirty days
is a common default; pick yours and apply it consistently.

## Handling price pushback

Diagnose before discounting:

- **Competing against a lower bid?** Ask what is in it. On Oahu the usual gap is
  freight treatment, lead-time realism, or a materially different product spec —
  not margin. Compare scope before conceding price.
- **Genuinely over budget?** Restructure rather than discount. Change door style,
  mix stock and custom, reduce specialty units, or phase the project. This
  preserves margin and gives the customer agency.
- **Testing?** Hold. A defensible itemized quote with stated exclusions is its own
  argument, and discounting on first contact teaches the customer that the first
  number was not real.

Discounting the same scope is the last resort, not the first — it concedes that
the original price was arbitrary.

## Checklist before sending

- [ ] Intake complete; no material assumptions left unstated
- [ ] Priced from landed cost, not supplier list price
- [ ] Margin applied as a divisor
- [ ] Duty and AD/CVD exposure confirmed for any imported line
- [ ] Allowances stated per unit
- [ ] Exclusions explicit
- [ ] Lead time a range, with its driver named
- [ ] Validity period stated
- [ ] Correct brand and sender for the pipeline — see `lead-routing`
- [ ] Follow-up scheduled; see `ghl-sms-templates`
