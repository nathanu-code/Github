# Operating cost estimate (3 videos/day, 7 platforms)

| Item | Cost | Notes |
|---|---|---|
| Claude Code routines (research, report, 3 slots) | Included in your Claude plan's usage | 5 runs a day. Research is the heavy one (web searches + rendering, about 15–30 min). Report and slot runs are short. The account showed a **weekly usage warning** today, so watch usage; the slot routines are created disabled until publishing has something to publish. |
| Rendering compute | $0 extra | Runs inside the routine container. About 2–3 min per 45 s clip for all three exports |
| Google Drive / Sheets / YouTube APIs | $0 | Within free quotas (YouTube uploads: 100/day) |
| Meta (FB, IG, Threads), TikTok, LinkedIn APIs | $0 | Free; approvals and audits take time, not money |
| X API | about $1.50–3 / month | Pay-per-use: about $0.015 per post (≈90/month) plus small per-read charges for analytics. Captions avoid links (link posts cost $0.20) |
| Slack | $0 | Existing workspace |
| Footage licensing | $0 to a few hundred dollars per clip | Direct permission from filmers is free. Agency licences are priced per clip and use (get quotes) |
| Buffer (optional, not needed) | $35+/month | Only if you prefer it to direct APIs (7 channels × $5 Essentials) |

**Expected:** under $5/month in API fees, plus Claude plan usage and any footage licences.

Resource guardrails: one video per slot, renders capped at 90 s, GDELT throttled, publish retries
capped at 3 and only when safe. `wi health` and the daily report show queue size, failures and token
problems.
