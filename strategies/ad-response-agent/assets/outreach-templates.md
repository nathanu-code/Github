# Outreach templates

For everyone who doesn't answer the phone — which is most of them.

Every template rests on the same asset: a **timestamp they can verify**. Strip
that out and these are ordinary spam. Placeholders in `{braces}` map to fields
`leadgap.py show <id>` prints.

---

## Email — after a voicemail

**Subject:** `your contact form, {weekday} morning`

> Hi {first_name},
>
> Left you a quick voicemail. Not a pitch — a heads up.
>
> I filled out the contact form on {website} on {date} at {time}. As of this
> morning, {gap_time} later, I haven't had a call, a text, or an email.
>
> You've got {active_ads} ads running right now, so that form is where your ad
> spend lands. Something between the two is dropping people.
>
> I put together the timestamps — two-minute read, attached. If I got it wrong,
> tell me and I'll leave you alone.
>
> {your_name}
> {your_phone}

Why the subject line has no capital letters and no company name: it reads like a
note from a customer, because that's what you were.

## Email — cold, no call attempted

**Subject:** `filled out your form {weekday} — nobody called`

> {first_name},
>
> I submitted an inquiry on your site {date} at {time}. {gap_time} later I still
> haven't heard from anyone.
>
> I only checked because I saw your ads in the Meta Ad Library — {active_ads} of
> them live. Whatever those ads cost, the leads they produce are landing
> somewhere nobody's watching.
>
> Full audit attached: the exact timestamps, per channel.
>
> If your answer is "we know, we're working on it" — genuinely, no reply needed.
> If it's news to you, I fix this specific thing and it takes about a day to set
> up.
>
> {your_name}

The permission-to-ignore line at the end raises reply rates. It also filters out
everyone who'd waste your time.

## SMS follow-up

Only to a mobile number you have a legitimate reason to text, and only after a
call or voicemail. Check your obligations before automating any of this — see
[ANALYSIS.md §5](../ANALYSIS.md#5-what-the-reel-leaves-out-entirely).

> Hi {first_name} — {your_name} here, left you a voicemail. I filled out your
> contact form {weekday} and never got a reply. Sent the timestamps to
> {email_domain}. Worth two minutes if you're paying for those ads. Reply STOP
> and I won't text again.

## Instagram / Facebook DM

Businesses running Meta ads read their page DMs. Often the fastest route in.

> Hey — saw your ads running so I filled out the contact form on your site
> {weekday} to see how it goes on the customer end. {gap_time} later, no call, no
> text, no email.
>
> Not trying to sell you anything in a DM. Just figured if I'd been an actual
> customer you'd want to know. Happy to send the timestamps if useful.

Never pitch in the first DM. Ask permission to send the audit; the audit does the
selling.

## LinkedIn — for the multi-location operator

Better than a DM when there's an ops manager or marketing director between you
and the owner.

> {first_name} — quick one. I ran a response-time test on {company}'s inbound
> form on {date}: submitted at {time}, first contact {gap_time} later. You've got
> {active_ads} ads live, so that's paid traffic hitting an intake nobody's
> watching in real time.
>
> I do one thing — instant response on inbound ad leads. Not a receptionist, not
> a chatbot. Want the audit? It's a page.

---

## The follow-up sequence

| When | Channel | Content |
| --- | --- | --- |
| Day 0 | Call → voicemail | The 20-second finding |
| Day 0 | Email | Voicemail follow-up + audit attached |
| Day 2 | Call | "Did that audit make it through?" |
| Day 4 | DM or SMS | One line, referencing the audit |
| Day 8 | Email | Re-probe result: "ran it again Saturday, same outcome" |
| Day 14 | Email | Break-up: "closing the file — here's the audit either way" |

Day 8 is the strongest touch in the sequence and the one nobody sends. A second
probe with a fresh timestamp turns "you missed one" into "this is how you
operate," and it costs you thirty seconds:

```bash
python3 leadgap.py probe {id} --via form --at now --notes "day-8 re-probe"
```

The break-up email closes more deals than the first three touches combined.
Keep it warm and actually close the file:

> Closing this out — no hard feelings, you're clearly busy. Audit's below if you
> ever want it. If the form starts working again, ignore me entirely.

---

## Rules

1. **Never send a template without a real timestamp in it.** The evidence is the
   entire product.
2. **Never attach the audit to a first DM.** Ask first.
3. **Concede the autoresponder.** If they got an automated "we received your
   request," say so before they do. Conceding the small point is what makes the
   big one credible.
4. **Stop when they say stop.** Immediately, on every channel, and honour it in
   your own system before you sell anyone else's.
