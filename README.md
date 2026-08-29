# Lead Capture Funnel

A two-page application funnel — landing page → 8-step qualifying quiz → booking —
built from a teardown of a high-spend Meta funnel, with its measurement defects
fixed rather than copied.

Configured for **Grandeur Design Supply** (kitchen cabinet design consultation).
All brand, copy and quiz content lives in `config.js`; re-pointing it at another
business is a one-file edit.

---

## Why this exists

The reference funnel did one thing exceptionally well and three things wrong.

**The thing it did well** — it captured name and phone at **step 3 of 8**, before any
qualifying question, and fired a webhook immediately. Everyone who abandoned at steps
4–8 was still a reachable contact instead of lost traffic. That is typically 40–70%
of everyone who starts.

**The things it did wrong** — it fired Meta's `Lead` event twice per person and once
on a mere button click; it ran a campaign named `SCHEDULE` with no `Schedule` event
anywhere in its code; and it loaded a Google Ads tag that recorded no conversions.
It also hardcoded `email: ""`, leaving no email nurture path at all.

This build keeps the first and fixes the rest. Full traceability in
[`docs/strategy-map.md`](docs/strategy-map.md).

---

## Structure

```
config.js              ← single source of truth: brand, copy, quiz, IDs, webhooks
lp.html                  landing page
quiz.html                8-step quiz
assets/
  funnel.css             shared styles (design tokens at the top)
  tracking.js            pixel layer — dedupe, UTM capture, Schedule event
  lp.js                  landing page rendering
  quiz.js                quiz engine, partial capture, routing
docs/
  strategy-map.md        every strategy → the code that implements it
  utm-convention.md      campaign naming + TEST/WINNERS structure
  ghl-setup.md           CRM workflows, Conversions API, launch checklist
build.js                 optional: inline everything into dist/ for page builders
```

---

## Quick start

```bash
# serve locally
python3 -m http.server 8000
# then open http://localhost:8000/lp.html
```

Then fill in `config.js`:

```js
webhooks: ['https://services.leadconnectorhq.com/hooks/…'],  // CRM inbound webhook
booking: { calendarUrl: 'https://api.leadconnectorhq.com/widget/bookings/…' },
tracking: { metaPixelId: '…', googleAdsId: '…', googleAdsBookingLabel: '…' }
```

Every ID is optional. Leave one empty and that platform is skipped cleanly —
the funnel still runs, it just doesn't report to that platform.

**Deploy** as static files anywhere (Netlify, Vercel, S3, GitHub Pages). For a page
builder that won't serve sibling assets, run `node build.js` and paste `dist/lp.html`
and `dist/quiz.html` as raw HTML.

---

## The quiz

Order is deliberate. Only **one** question changes routing.

| # | Step | Purpose |
|---|---|---|
| 1 | Who are you | Cheap first click — starts the commitment ladder |
| 2 | Project type | Segmentation |
| **3** | **Name · phone · email** | **Partial webhook fires here** |
| 4 | Timeline | Sales intel |
| 5 | About the space | Sales intel |
| 6 | Size (anchored slider) | Anchoring — defaults to 25 linear ft, never 0 |
| 7 | #1 challenge | Hands the closer their script, in the prospect's words |
| 8 | Budget | **The gate** — the only question that routes |

Steps 1, 2 and 4–7 exist to build commitment and arm the sales call. The gate is
whichever option carries `disqualify: true` in config.

**Both outcomes stay in the CRM.** Qualified → prefilled calendar, tagged
`Qualified`. Disqualified → a genuine lower-tier offer (surplus inventory), tagged
`Nurture`. Nobody is dead-ended.

---

## Configuration notes

**Moving the contact step.** Step 3 of 8 is the tested position — late enough that
two easy clicks build commitment, early enough that most people reach it. Moving it
later captures fewer contacts; moving it to step 1 raises the barrier before any
investment. The engine handles any position, but change it deliberately.

**Adding a question.** Append to `quiz.steps` with a unique `key`. Supported types:
`choice`, `contact`, `text`, `slider`. The key becomes the webhook payload field —
no other file needs touching.

**Adding a disqualifier.** Put `disqualify: true` on any `choice` option. Multiple
steps can gate; any one match routes to the decline screen.

---

## Testing

The funnel was verified end-to-end in a real browser (Playwright/Chromium) across 40
assertions covering both routing paths: partial-fire timing and payload shape, UTM
survival across the page navigation, pixel dedupe, slider anchoring, calendar
prefill, form validation, and console errors.

Testing caught three defects that reading the code did not — including UTM capture
sitting in the wrong file, which silently dropped ad-level attribution at the LP→quiz
navigation. See the table at the end of `docs/strategy-map.md`.

---

## Known limitation

The browser-side `Schedule` event listens for a `postMessage` from the booking
iframe. That listener is written against the embed script's documented behaviour but
**has not been verified against a live calendar** — doing so requires a real booking.

Configure the server-side Conversions API path in
[`docs/ghl-setup.md`](docs/ghl-setup.md) §4b regardless; it is authoritative, and the
two deduplicate against each other via the shared `event_id`. Confirm the browser
listener with one test booking and the console output it logs.

---

## Before running paid traffic

The full checklist is in [`docs/ghl-setup.md`](docs/ghl-setup.md) §6. The three that
break things most often:

1. **Set a removal condition on the partial sequence** for the `quiz-complete` tag —
   otherwise people who abandon and later finish get texted "you got cut off" after
   they've already booked.
2. **Verify exactly one `Lead` per person** in Meta Events Manager. That was the
   original funnel's most expensive bug.
3. **Point `quiz.soft.ctaUrl` at something real.** The reference funnel shipped `#`.

The consent language in `config.js` covers automated calls, SMS and email with a STOP
opt-out. Have your own counsel review it against current TCPA rules before scaling.
