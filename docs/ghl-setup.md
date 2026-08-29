# GoHighLevel Setup

The code handles capture. This handles what happens to the capture.

The single most valuable thing here is **step 2** — branching on `completion` is
what turns quiz abandoners from lost traffic into a working callback list.

---

## 1. Create the inbound webhook

1. **Automation → Workflows → Create Workflow → Start from scratch**
2. Trigger: **Inbound Webhook**
3. Copy the generated URL into `config.js`:

```js
webhooks: [
  'https://services.leadconnectorhq.com/hooks/<location>/webhook-trigger/<id>'
],
```

4. Walk the quiz once so GHL captures a sample payload — it needs a real request to
   map the fields.

### Payload reference

| Field | Type | Notes |
|---|---|---|
| `first_name` | string | |
| `phone` | string | E.164-ish, country code prefixed |
| `email` | string | **populated** — the reference funnel hardcoded this empty |
| `completion` | `partial` \| `complete` | **branch on this** |
| `lead_status` | `Partial` \| `Qualified` \| `Nurture` | |
| `qualified` | `yes` \| `no` \| `""` | empty on partials |
| `role`, `project`, `timeline`, `details`, `size`, `challenge`, `budget` | string | one per quiz step, keyed as configured |
| `event_id` | string | pass to the Conversions API for dedup (step 4) |
| `utm` | object | `utm_source`, `utm_campaign`, `utm_medium`, `utm_content`, `campaign_id`, `medium_id`, `content_id`, `fbclid`, `gclid` |
| `source` | string | `Design Call Quiz` |
| `submitted_at` | ISO 8601 | |

Map `utm.utm_campaign`, `utm.utm_medium` and `utm.utm_content` to custom contact
fields. Without them you can see that leads arrived but not which ad produced them.

---

## 2. Branch on `completion` — the money step

Add an **If/Else** immediately after the trigger.

### Branch A — `completion` is `partial`

This contact gave you their details and then stopped. They are not a bad lead;
they are an *unfinished* one. Typically 40–70% of everyone who starts.

Recommended sequence:

| Wait | Action |
|---|---|
| 0 min | Add tag `quiz-partial`. Create/update contact. |
| 8 min | **SMS:** "Hi {{contact.first_name}}, it's {{user.name}} at Grandeur — saw you started a cabinet quote and got cut off. What room are you working on?" |
| 1 hour | If no reply → task for a human to call. |
| 1 day | **Email:** the same question plus a link back to the quiz. |
| 3 days | Final SMS, then move to long-term nurture. |

**Critically:** add a *removal* condition on tag `quiz-complete`. Someone who
abandons at step 5 and comes back to finish at step 8 must not receive the
"you got cut off" message afterwards. Without this you will text people who
already booked.

### Branch B — `completion` is `complete` AND `qualified` is `yes`

| Wait | Action |
|---|---|
| 0 min | Tag `quiz-qualified`. Move to **Booking Requested** pipeline stage. |
| 0 min | Internal notification with `challenge` and `details` in the body — whoever takes the call reads the prospect's own words first. |
| 2 min | If no appointment booked → SMS with the calendar link. |
| 1 day | Reminder if still unbooked. |

### Branch C — `completion` is `complete` AND `qualified` is `no`

Do **not** discard. Tag `nurture-budget`, send the in-stock/surplus offer
(`quiz.soft.ctaUrl`), and add to a monthly list. Budgets change; a "no" at $5k
in September is often a "yes" at $20k in March.

---

## 3. Calendar

1. **Calendars → Create Calendar** → 30-minute design call.
2. Copy the booking link into `config.js`:

```js
booking: {
  calendarUrl: 'https://api.leadconnectorhq.com/widget/bookings/<slug>'
}
```

`assets/quiz.js` appends `first_name`, `name`, `full_name`, `phone` and `email` as
query parameters — several aliases, because widget builds differ in which key they
read. The prospect should land on a pre-filled form.

---

## 4. Conversions API — do not skip this

The booking happens inside a **cross-origin iframe**. The parent page cannot see it
directly. This is precisely why the reference funnel ran a campaign named `SCHEDULE`
while having no `Schedule` event anywhere in its code.

Two paths. **Configure the server-side one regardless** — it is the reliable one.

### 4a. Browser (best-effort, already implemented)

`assets/tracking.js` listens for `postMessage` from the booking origin and fires
`Schedule` when the payload looks like a confirmed appointment.

**This needs one verification against a live calendar.** The exact message shape is
provider-specific and changes between widget versions. Open the console, make a real
test booking, and read the logged lines:

```
[tracking] booking widget message: { … }
```

If the real event name doesn't match, widen `BOOKED_RE` in `assets/tracking.js`.
Once confirmed, remove the `console.debug` line.

### 4b. Server-side (authoritative)

In the GHL workflow triggered by **Appointment Booked**, add an outbound webhook to
Meta's Conversions API:

```
POST https://graph.facebook.com/v21.0/<PIXEL_ID>/events?access_token=<TOKEN>
```

```json
{
  "data": [{
    "event_name": "Schedule",
    "event_time": 1757000000,
    "event_id": "{{contact.event_id}}",
    "action_source": "website",
    "user_data": {
      "ph": "<sha256 of E.164 phone>",
      "em": "<sha256 of lowercased email>"
    }
  }]
}
```

`event_id` is why the browser passes it through the payload: Meta uses it to
deduplicate the browser event against the server event, so a booking counts once
even when both fire. Store it on the contact record in step 1.

`user_data` fields must be SHA-256 hashed. Never send raw PII.

### 4c. Google Ads

Set both in `config.js` — the tag alone records nothing:

```js
googleAdsId: 'AW-XXXXXXXXX',
googleAdsBookingLabel: 'AbC-D_efG-hIjKlMnOp'   // from the conversion action
```

If `googleAdsId` is set and the label is missing, the console warns rather than
failing silently.

---

## 5. Compliance

The consent language in `config.js` (`quiz.steps[].consent`) covers automated
calls, SMS and email, states that consent is not a condition of purchase, and
gives a STOP opt-out.

- Have your own counsel review it against current TCPA rules before running paid traffic.
- Honour STOP immediately — GHL does this natively; do not override it.
- Keep the consent text versioned with the timestamp of each submission.
- Hawaii has no additional state-level SMS consent requirement beyond federal TCPA
  as of this writing, but confirm before scaling.

---

## 6. Pre-launch checklist

- [ ] Webhook URL in `config.js`, sample payload captured in GHL
- [ ] If/Else branching on `completion` built, all three branches live
- [ ] **Removal condition on `quiz-complete`** set for the partial sequence
- [ ] Calendar URL in `config.js`, prefill confirmed with a real booking
- [ ] `metaPixelId` set; Meta Events Manager shows `ApplicationStart`,
      `ApplicationPartial`, `Lead`, `Schedule` — and **exactly one** `Lead` per person
- [ ] Conversions API webhook live with `event_id` passed through
- [ ] `googleAdsBookingLabel` set (or `googleAdsId` left empty)
- [ ] `quiz.soft.ctaUrl` points at a real page, not `#`
- [ ] Proof images added to `lp.gallery.images`
- [ ] Campaign named per `docs/utm-convention.md`, URL parameters pasted into the ad
- [ ] Walked the funnel end-to-end on a phone, on cellular, not just desktop wifi
