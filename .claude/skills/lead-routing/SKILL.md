---
name: lead-routing
description: Decide which brand a lead belongs to (Grandeur Design Supply, Ke'a Cabinetry, or Island Home), qualify it, and choose the next action. Covers brand assignment, qualification signals, disqualification, routing between the retail and surplus channels, and handoff into quoting or follow-up. Use when a new lead or inquiry arrives, when a lead is stalled, when deciding whether a lead is worth pursuing, or when unsure which business should own a contact.
metadata:
  origin: local
  business: Grandeur Design Supply / Ke'a Cabinetry / Island Home
---

# Lead Routing

Assigns an inbound lead to the right brand and the right next action.

Runs before `ghl-sms-templates` (which writes the message) and before
`project-quoting` (which prices the work). Getting the brand wrong at intake
means every downstream message and document carries the wrong identity.

## The three pipelines

| Brand | Sells | Channel | Typical buyer |
| --- | --- | --- | --- |
| **Grandeur Design Supply** | Windows, doors, cabinetry, lighting, flooring, countertops | Retail / project, grandeurdesignsupply.com | Homeowner or contractor with a defined project |
| **Ke'a Cabinetry** | Cabinetry-focused | Retail / project | Cabinet-specific buyer |
| **Island Home Cabinets / Building Materials** | Surplus cabinets, appliances, equipment, materials | Liquidation, Waipahu pickup | Price-driven, cash, in-person |

The retail brands and the surplus channel are different businesses with
different economics. Grandeur and Ke'a sell a specified product on a lead time.
Island Home sells what is physically on hand, now, at a price that clears it.
Routing a lead into the wrong one wastes both sides' time.

## Brand assignment

Route on **what the buyer needs**, not on what they first asked about.

**→ Grandeur Design Supply** when:
- The inquiry spans multiple categories (windows *and* flooring, whole-remodel)
- It is windows, doors, lighting, flooring, or countertops in any combination
- There are plans, blueprints, or a builder involved
- It is a new-construction or full-remodel project

**→ Ke'a Cabinetry** when:
- The inquiry is cabinetry-only and cabinetry-led
- The buyer is shopping cabinet lines, door styles, or box construction specifically

**→ Island Home** when:
- The buyer wants something available now, not ordered
- Price is the leading question, before spec
- They are asking about surplus, overstock, clearance, or used equipment
- They found us through a Craigslist or Marketplace listing
- Quantity is small and one-off, or they want to pick up

**Ambiguous cases:**

- *Contractor asking about cabinets for a spec house* → Ke'a or Grandeur
  depending on whether other categories are in play. Ask one question about
  scope before assigning.
- *Homeowner who wants cabinets "as cheap as possible"* → check Island Home
  inventory first. If we have stock that fits, that is a faster close at better
  margin than an import lead time. If not, route to Ke'a and reset expectations
  on lead time honestly.
- *Someone responding to a surplus listing who turns out to have a real project*
  → this is the valuable crossover. Move them to Grandeur or Ke'a, but keep the
  surplus option on the table; a mixed close (stock now, order the rest) is a
  legitimate outcome.

## Qualification

Establish four things. Not as an interrogation — most surface naturally in a
first exchange, and `ghl-sms-templates` advises asking one question at a time.

1. **Scope** — what and how much
2. **Timeline** — when they need it, and whether that is fixed
3. **Stage** — dreaming, planning with plans drawn, or ready to buy
4. **Decision authority** — whether this person can commit

Timeline against stage is the most useful pair. Someone with a firm install date
and no plans drawn has a problem they do not know about yet — ocean lead time
means the calendar is already tighter than they think. Surfacing that early is
genuinely helpful and it establishes credibility.

### Strong signals

- Plans or blueprints exist
- A general contractor or designer is engaged
- They volunteer a budget range
- Specific product questions (a named line, a performance requirement)
- A real, dated deadline
- They sent photos or measurements unprompted

### Weak signals

- "Just looking at options"
- No timeline, or a timeline that keeps moving
- Price-only questions with no scope
- Cannot describe the space
- Unreachable after first contact

Weak does not mean dead. It means nurture cadence, not quoting effort. Do not
build a takeoff for an unqualified lead — that is where quoting capacity is lost.

### Disqualification

Say so early and politely rather than carrying dead weight:

- Wants a product we do not carry and will not source
- Off-island delivery we cannot economically serve
- Budget is below our landed cost for the scope — being direct here is a
  kindness, and Island Home stock may still fit
- Wants installation labor when we are supply-only for that category
- Timeline is physically impossible against ocean lead time and cannot move

When declining, offer the nearest thing we *can* do. A clean referral is
remembered.

## Next action

| State | Action |
| --- | --- |
| New, qualified, plans in hand | Acknowledge, confirm receipt, begin intake → `project-quoting` |
| New, qualified, no plans | Ask the single highest-value question — usually "do you have plans drawn up yet?" → `ghl-sms-templates` |
| New, unqualified | Nurture cadence, no quoting effort |
| Photos sent, no measurements | Reference something specific in the photo to build credibility, then request measurements → `ghl-sms-templates` |
| Measurements received | Confirm receipt same day, state a realistic turnaround → `project-quoting` |
| Proposal sent, no response | Follow-up sequence, two tonal variants → `ghl-sms-templates` |
| Stalled past normal cycle | One value-forward touch citing lead times, then move to long nurture |
| Surplus inquiry on a live listing | Confirm availability, price, pickup terms → `craigslist-listings` |

## Speed matters more than polish

Response time is the highest-leverage variable in this pipeline, and it is
entirely within our control. A fast, plain reply beats a slow, considered one —
the first responder frames the project.

This is the same argument the GrowSales AI content makes about missed calls and
speed-to-lead. It applies to our own pipelines, and we should hold ourselves to it.

## Cross-brand hygiene

- **One brand per conversation.** Do not sign as Grandeur and follow up as Ke'a.
- **Match the sender to the brand.** `ghl-sms-templates` documents the
  established signature patterns.
- **Match the channel to the brand.** Surplus buyers came from a listing and
  expect listing-style directness. Project buyers expect a consultative tone.
- **Record which brand owns the contact in GHL at intake**, before the first
  reply — retroactive reassignment is where duplicate outreach comes from.

**Placeholder — fill from your own records:** current GHL pipeline names and
stage definitions, assignment rules if leads route to different people, and your
actual nurture cadence intervals.
