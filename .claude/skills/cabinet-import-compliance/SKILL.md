---
name: cabinet-import-compliance
description: Regulatory exposure for importing cabinets, vanities, and wood building products — AD/CVD orders on Chinese wooden cabinets and the components trap, circumvention and transshipment risk, TSCA Title VI formaldehyde certification, Lacey Act declarations, and HTS classification. Use before committing a purchase order to an overseas cabinet supplier, when a container is held, when evaluating a new supplier or country of origin, or when a quoted price looks too good.
metadata:
  origin: local
  business: Grandeur Design Supply / Ke'a Cabinetry / Island Home
---

# Cabinet Import Compliance

Regulatory decision support for importing cabinetry and wood products.

This is the highest-consequence skill in this repo. A classification or origin
error on cabinets does not produce a small correction — it produces a duty bill
that can exceed the value of the goods, applied retroactively.

**This is decision support, not legal advice.** Every rate, order, and deadline
below moves. Confirm with your customs broker and against primary sources before
acting. Where this skill deliberately does not state a number, that is because
stating one would be worse than useless.

## When to Activate

- Evaluating a new overseas cabinet or vanity supplier
- A quoted unit price is materially below the market — this is the tell
- Committing a purchase order to any Asian origin
- A container is held, examined, or hit with a CBP request for information
- Classifying a new product for entry
- A supplier proposes routing through a third country

## 1. AD/CVD on wooden cabinets from China

**This is the dominant risk.** Antidumping and countervailing duty orders on
*Wooden Cabinets and Vanities and Components Thereof from the People's Republic
of China* have been in force since 2020.

Status as of this writing (verify before relying on it):

- The orders are **active**.
- ITC instituted **five-year sunset reviews** on March 3, 2025.
- Commerce continues to run **administrative reviews**; preliminary results for
  the 2024–2025 antidumping review published July 13, 2026, with a parallel
  countervailing review partially rescinded.

Three things about how these orders actually bite:

**"And components thereof" is the trap.** The scope is not limited to finished
cabinets. Doors, frames, boxes, and parts fall within it. A supplier shipping
"cabinet components" or "furniture parts" rather than assembled cabinets is not
outside the order by virtue of the label. Scope is determined by the order's
language and by Commerce scope rulings, not by the invoice description.

**Rates are producer-specific and change.** Each exporter/producer has its own
rate; unlisted parties fall to the country-wide rate, which is severe. Rates are
revised through administrative reviews. **Never carry a rate forward from a prior
shipment.** Confirm the current rate for your specific producer, by name, at time
of order.

**Liability is retroactive.** Entries are made with estimated duties and
liquidated later, sometimes years later, at the rate the review determines. A
shipment that cleared cheaply is not a shipment that is settled. Budget for the
gap and do not treat early clearance as final.

### Circumvention and transshipment

When an AD/CVD order lands, production shifts to neighboring countries. Some of
that is legitimate relocation. Some is transshipment designed to disguise Chinese
origin, and Commerce runs circumvention inquiries covering exactly that pattern
for this product class.

Country of origin for duty purposes is **where substantial transformation
occurred**, not where the container was loaded and not what the commercial
invoice says. Light assembly of Chinese components in a third country generally
does not confer new origin.

Treat these as red flags on any non-China Asian cabinet supplier:

- Price at or near the pre-order China price — the order exists precisely because
  that price was found to be unfair; a matching price implies matching source
- Reluctance to document the actual production facility, or to permit a visit
- Component sourcing that traces back to China with only assembly performed locally
- A supplier that appeared in the market after the orders took effect, with no
  prior manufacturing history
- Willingness to alter invoice descriptions or declared origin on request

**You are the importer of record. The liability is yours, not the supplier's.**
A supplier's assurance about origin has no legal weight in your defense. Diligence
is the only protection, and it must be documented at the time — not reconstructed
after a CBP inquiry.

## 2. TSCA Title VI — formaldehyde

Composite wood products (hardwood plywood, MDF, particleboard) and **finished
goods containing them** — which is nearly every cabinet — are regulated under
EPA's formaldehyde standards, 40 CFR Part 770.

Requirements:

- Panels must be certified compliant by an **EPA/CARB-recognized third-party
  certifier (TPC)**.
- Products must be **labeled** as TSCA Title VI compliant.
- **TSCA Section 13 import certification** is required at entry — in force since
  March 22, 2019.
- Records must be retained and traceable from finished good back to certified panel.

Practical: get the TPC certificate and the panel supplier chain **before**
shipment, not at the port. This is a routine hold reason and it is entirely
preventable with document discipline. A supplier who cannot promptly produce TPC
documentation is telling you something about their panel sourcing.

## 3. Lacey Act

Wood products require a **plant and plant product declaration** (PPQ Form 505)
at entry, covering genus, species, country of harvest, quantity, and value.

The Lacey Act also prohibits trade in illegally harvested plant material, with a
due-care standard. Species identification matters, and exotic hardwoods carry
additional CITES exposure. "The supplier told us it was X" is weak due care;
documented species verification is strong.

## 4. Classification

Cabinets and vanities generally classify in Chapter 94 (furniture) — wooden
kitchen furniture, other wooden furniture, and parts headings. The precise
subheading depends on construction, function, and whether the item enters
assembled or as parts.

Use the vendored `customs-trade-compliance` skill for the General Rules of
Interpretation methodology. Two cabinet-specific notes:

- **Parts versus finished goods** changes both the classification and, critically,
  the AD/CVD analysis. Do not let a convenient parts classification create a false
  sense of scope exclusion — the order covers components.
- **A binding ruling from CBP** is available in advance and is worth pursuing for
  any product you will import repeatedly at volume. It converts a recurring
  uncertainty into a documented position.

## 5. Section 301

Chinese-origin goods may carry Section 301 tariffs **in addition to** any AD/CVD.
These are separate mechanisms and they stack. List coverage and rates have been
revised repeatedly. Confirm current applicability for your HTS subheading at time
of order.

## Diligence file

For every overseas cabinet supplier, hold and keep current:

- [ ] Producer legal name and physical factory address — verified, not asserted
- [ ] Current AD/CVD rate for that specific producer, dated
- [ ] Country of origin determination with substantial-transformation reasoning
- [ ] Component sourcing, especially where components originate in China
- [ ] TPC certificate for composite wood panels
- [ ] Lacey Act species and harvest-country documentation
- [ ] HTS classification with reasoning, or a CBP binding ruling
- [ ] Commercial invoice and packing list conforming to 19 CFR § 141.86

Build this file **before** the first order. Reconstructing it under a CF-28 is
where importers discover what they failed to ask.

## When a container is held

1. Get the **hold type** from the broker — CBP exam, PGA hold, AD/CVD question,
   or documentation deficiency. These have different resolutions and different
   clocks.
2. **Do not guess at responses to CBP.** A CF-28 Request for Information or CF-29
   Notice of Action is the start of a formal process. Answer with the broker, and
   with counsel if AD/CVD scope or origin is at issue.
3. **Demurrage runs the whole time.** Factor it into how fast you resolve, but do
   not let it push you into a hasty or inaccurate filing — an incorrect statement
   to CBP is far more expensive than storage.
4. If an error is found, ask the broker about **prior disclosure**. Voluntarily
   disclosing before CBP finds it substantially mitigates penalties under 19 USC
   § 1592. This is a legal decision, not an operational one.

## Sources

Verify against primary sources before acting:

- [Federal Register — Wooden Cabinets and Vanities from China, AD administrative review 2024–2025 preliminary results](https://www.federalregister.gov/documents/2026/07/13/2026-14030/wooden-cabinets-and-vanities-and-components-thereof-from-the-peoples-republic-of-china-preliminary)
- [Federal Register — parallel CVD administrative review, partial rescission](https://www.federalregister.gov/documents/2026/07/13/2026-14031/wooden-cabinets-and-vanities-and-components-thereof-from-peoples-republic-of-china-preliminary)
- [USITC — Wooden Cabinets and Vanities from China (sunset review publication)](https://www.usitc.gov/publications/701_731/pub5661.pdf)
- [EPA — Formaldehyde Emission Standards for Composite Wood Products](https://www.epa.gov/formaldehyde/formaldehyde-emission-standards-composite-wood-products)
- [eCFR — 40 CFR Part 770](https://www.ecfr.gov/current/title-40/chapter-I/subchapter-R/part-770)
- [CBP CSMS — Requirements for Importing Regulated Composite Wood Products](https://content.govdelivery.com/accounts/USDHSCBP/bulletins/221d3a7)

Commerce's AD/CVD proceedings are searchable at access.trade.gov; CBP rulings at
rulings.cbp.gov.

## Caveat

Rates, scope rulings, circumvention determinations, sunset outcomes, and Section
301 lists all change — several did in the year this was written. This skill
encodes the *structure* of the exposure and where to look. It does not encode
current numbers, deliberately. For any decision with money on it, confirm with
your customs broker, and involve trade counsel where scope or origin is in
question.
