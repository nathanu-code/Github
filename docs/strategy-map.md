# Strategy → Implementation Map

Traceability from each finding in the teardown to the code that implements it.

---

## The seven strategies worth stealing

### 1. Partial capture at step 3 of 8

**The finding.** Contact details were collected before every qualifying question.
A webhook fired with `completion: "partial"` the moment name and phone submitted, so
everyone abandoning at steps 4–8 stayed a reachable contact. In a typical application
funnel that is 40–70% of entrants otherwise lost.

**Implementation.** `config.js` places `type: 'contact'` at index 2 (step 3 of 8).
`assets/quiz.js` → `sendPartial()` fires on that step's submit, guarded by a
`partialSent` flag. `buildPayload('partial')` sets `lead_status: 'Partial'`.
Requests use `keepalive: true` so they complete even as the user navigates away.

**Verified.** E2E asserts zero webhooks before the contact step, exactly one after,
with `completion === 'partial'` and all three contact fields populated.

---

### 2. Free-text "#1 challenge" before the booking

**The finding.** The prospect writes the closer's script, in their own words, before
the call starts.

**Implementation.** `config.js` → step index 6, `key: 'challenge'`, with a 10-character
minimum so it can't be skipped with a single character. Delivered in the webhook
payload; `docs/ghl-setup.md` puts it in the internal notification body.

**Verified.** E2E asserts the free text reaches the complete payload.

---

### 3. Explicit self-selecting disqualifier with a real destination

**The finding.** The lowest budget option was labelled "(please don't book)" — but
their decline screen's CTA was `href="#"`, dead-ending every disqualified visitor.

**Implementation.** `config.js` marks the option `disqualify: true` with the label
inline. `assets/quiz.js` routes to `#scr-soft`, which carries `quiz.soft.ctaUrl` —
pointed at the Island Home surplus inventory, a genuine lower-tier offer. If that URL
is unset or `#`, the console warns rather than shipping a dead link silently.
Disqualified visitors still produce **both** webhook fires, tagged `Nurture`.

**Verified.** E2E asserts the decline route, a non-`#` href, `qualified: "no"`,
`lead_status: "Nurture"`, and that the contact was retained.

---

### 4. Friction-killer under every CTA

**The finding.** "Free · 30 minutes · No card required" under all four CTAs —
three objections, seven words, repeated.

**Implementation.** Single config value `lp.ctaMeta`, rendered into every
`[data-cta-meta]` node by `assets/lp.js`. One source, so the buttons can never drift
out of sync with each other.

**Verified.** E2E asserts all three LP CTAs carry it.

---

### 5. Pipe-delimited UTM convention

**The finding.** Their UTMs encoded funnel stage, budget mode, page type,
optimization event, test/scale stage, audience, geo, age band, creative length and
angle — every variable filterable in reporting.

**Implementation.** `docs/utm-convention.md`. Capture is in `assets/tracking.js` →
`captureUtm()`, which runs on **both** pages, uses first-touch precedence, and
persists through the LP→quiz navigation. `assets/quiz.js` attaches the result to both
webhook fires.

> This was the one bug found by testing rather than by reading. Capture originally
> lived only in `quiz.js`, so it read the quiz URL — which has no UTMs — and
> attribution was silently lost at the navigation. Moved to the shared layer.

**Verified.** E2E loads the LP with a UTM set and asserts `utm_campaign` arrives
intact in the payload after navigation.

---

### 6. TEST → WINNERS campaign separation

**The finding.** Their campaign name contained `WINNERS`, indicating a separate
consolidation campaign that proven creatives graduate into.

**Implementation.** `docs/utm-convention.md` — the `STAGE` field, promotion and
demotion bars. Account structure, not code.

---

### 7. Anchored slider

**The finding.** Their income slider defaulted to $30,000, not zero or blank — a
pre-set reference point the prospect adjusts away from.

**Implementation.** `config.js` → step index 5, `default: 25` linear feet (a typical
full kitchen). `assets/quiz.js` → `renderSlider()` seeds `answers` with the default
on render, so the anchor is recorded even if the prospect never touches the control.

**Verified.** E2E asserts the slider reads `25 linear ft` on arrival and that the
value reaches the payload.

---

## The three defects deliberately not copied

### A. `Lead` double-fire

**The defect.** `fbq('track','Lead')` fired on the LP CTA click *and* again at quiz
completion. One person who clicked and completed generated two Leads; anyone who
clicked and bounced generated one. Any optimization leaning on `Lead` was training on
polluted data.

**The fix.** `assets/tracking.js` — a `once()` guard backed by `sessionStorage` (which
survives the cross-page navigation) plus an in-memory fallback for private-mode
browsers where storage throws. `Lead` fires only from `applicationComplete()`, never
from a click. A click emits `ApplicationStart`, a *custom* event, so it can be
analysed without contaminating the standard event.

**Verified.** E2E asserts each event marks fired once, and that a second
`applicationComplete()` call returns `false` without emitting.

---

### B. Campaign optimizing for `SCHEDULE` with no `Schedule` event

**The defect.** The campaign name declared `SCHEDULE` as the optimization event.
No such event existed anywhere in the page code. The booking completes inside a
cross-origin iframe the parent page cannot observe.

**The fix.** Two paths, because one is not enough:

- **Browser:** `assets/tracking.js` → `listenForBooking()` matches `postMessage`
  from the booking origin. Deliberately broad, and every message from that origin is
  logged so the real payload shape can be confirmed against a live booking.
- **Server:** `docs/ghl-setup.md` §4b — Conversions API from the *Appointment Booked*
  workflow, deduplicated against the browser event via the shared `event_id` that the
  webhook payload carries.

**Honest status:** the browser listener is written against the documented behaviour
of the embed script but **has not been verified against a live calendar** — that
requires a real GHL booking, which this build can't make. Treat the server-side path
as authoritative and confirm the listener with one test booking. This is flagged in
the code and in the setup doc, not buried here.

---

### C. Google Ads tag with no conversion event

**The defect.** `gtag('config','AW-…')` was present. No `gtag('event','conversion')`
anywhere. The tag collected nothing actionable.

**The fix.** `assets/tracking.js` → `schedule()` fires a real conversion using
`googleAdsBookingLabel`. If the account ID is set but the label is missing, it warns
in the console — the failure mode that produced the original defect is now loud.

---

### D. Phone-only capture (bonus)

**The defect.** Their payload hardcoded `email: ""`. No email nurture path existed
for the majority who never answer a call.

**The fix.** Email is a validated, required field on the contact step and flows
through both payloads. Configurable via `fields.emailRequired` if you'd rather trade
completeness for a lower-friction form.

---

## What testing found that reading didn't

| Issue | How it surfaced |
|---|---|
| UTM capture in the wrong file — attribution lost at navigation | E2E assertion on the payload |
| Emitters returned `undefined`, so dedupe was unobservable | E2E assertion on the return value |
| H1 wrapping to four lines at desktop width | Screenshot |

The first would have shipped silently and cost every ad-level attribution in the
account.
