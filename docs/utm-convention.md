# UTM & Campaign Naming Convention

Every creative variable becomes a filterable reporting dimension instead of a guess.
This is the convention reverse-engineered from a funnel that was clearly running it
at scale, adapted here.

---

## The format

Two pipe-delimited strings. Slashes separate fields; the field *position* carries
the meaning, so the order is fixed.

### Campaign name → `utm_campaign`

```
FUNNEL / BUDGET / PAGE / EVENT / STAGE / DATE
```

| Field | Values | Why it's there |
|---|---|---|
| `FUNNEL` | `TOF` · `MOF` · `BOF` | Cold, warm, or retargeting. Never mix in one campaign. |
| `BUDGET` | `CBO` · `ABO` | Campaign vs. ad-set budget optimization. |
| `PAGE` | `VSL` · `QUIZ` · `LONG` · `CALL` | Which landing page variant this points at. |
| `EVENT` | `SCHEDULE` · `LEAD` · `PURCHASE` | The conversion event being optimized for. |
| `STAGE` | `TEST` · `WINNERS` · `SCALE` | **The important one.** See below. |
| `DATE` | `MM-DD` | Launch date, so cohorts stay separable. |

Example:

```
TOF / CBO / QUIZ / SCHEDULE / WINNERS / 09-14
```

### Ad set name → `utm_medium`

```
AUDIENCE / GEO / AGE / LENGTH / ANGLE / DATE
```

| Field | Values | Why it's there |
|---|---|---|
| `AUDIENCE` | `BROAD` · `LAL1` · `INT-KITCHEN` · `RMKT-VID` | Targeting basis. |
| `GEO` | `OAHU` · `HI` · `US` | Geography. |
| `AGE` | `28-65` | Trim from data, not from instinct. |
| `LENGTH` | `SHORT` · `MID` · `LONG` | Creative runtime. |
| `ANGLE` | `A` · `B` · `C` | Which message angle. Keep a legend (below). |
| `DATE` | `MM-DD` | Launch date. |

Example:

```
BROAD / OAHU / 28-65 / SHORT / A / 09-14
```

### Ad name → `utm_content`

```
Ad <n> - v<m>
```

Iterate versions *within* a winning concept (`Ad 3 - v2`) rather than replacing the
concept outright. `v2` of a winner beats a brand-new `Ad 7` most of the time.

---

## The TEST → WINNERS split

This is the part that matters more than the naming.

**Two campaigns, always:**

1. **`...  / TEST / ...`** — small daily budget. New creative concepts enter here and
   nowhere else. Expect most to lose. This campaign's job is to be wrong cheaply.
2. **`... / WINNERS / ...`** — the scaling budget. A creative is only ever *promoted*
   into this campaign after it clears the bar in TEST.

Never introduce untested creative directly into the scaling campaign. One bad ad
in a CBO campaign eats budget that was learning something.

**Promotion bar** — set your own, but write it down and hold to it:

```
≥ 1,000 impressions   AND   cost-per-booked-call ≤ 1.3× current WINNERS average
```

**Demotion:** when a WINNERS ad's cost per booking drifts 40%+ above the campaign
average across 7 days, pause it. Don't nurse it.

---

## Angle legend

Keep this current — `ANGLE / A` is meaningless six weeks later without it.

| Code | Angle | Hook |
|---|---|---|
| `A` | Speed | "3 weeks, not 3 months" |
| `B` | Price | "Builder pricing without the builder" |
| `C` | Local | "Warehoused on-island, not on a barge" |
| `D` | Risk | "See the exact cabinets before you pay" |

---

## Meta URL parameters

Paste into the ad's **URL parameters** field. The `{{...}}` macros are filled in by
Meta at click time, so the IDs survive even if someone renames a campaign mid-flight.

```
utm_source=Meta+Ads
&utm_medium={{adset.name}}
&utm_campaign={{campaign.name}}
&utm_content={{ad.name}}
&utm_id={{campaign.id}}
&utm_term={{adset.id}}
&campaign_id={{campaign.id}}
&medium_id={{adset.id}}
&content_id={{ad.id}}
```

Both the readable name *and* the numeric ID are passed on purpose: names get edited,
IDs never change. `assets/tracking.js` captures all of these on the landing page and
persists them through to the CRM record — see below.

## Google Ads equivalent

```
utm_source=Google+Ads
&utm_medium={adgroupid}
&utm_campaign={campaignid}
&utm_content={creative}
&utm_term={keyword}
&gclid={gclid}
```

---

## How attribution survives the funnel

The ad click lands on `lp.html` carrying the parameters. The navigation to
`quiz.html` drops them from the URL — which is exactly where most funnels silently
lose attribution.

`assets/tracking.js` runs on **both** pages and:

1. Reads the parameters on first load and writes them to `sessionStorage`.
2. Uses first-touch precedence, so a later pageview without parameters cannot blank
   out attribution already captured.
3. Exposes them as `Track.utm()`, which `assets/quiz.js` attaches to **both** the
   partial and complete webhook payloads.

The result: every CRM record — including partials from people who never finished —
carries the campaign, ad set and ad that produced it.

Verified end-to-end: a UTM set on the LP arrives intact in the webhook payload after
the cross-page navigation.
