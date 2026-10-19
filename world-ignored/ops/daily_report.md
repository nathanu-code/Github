# Daily report (runs ~06:50 PHT, delivered by 07:00)

Do `ops/common.md` → Start first.

```bash
python -m wi analytics                       # snapshot from every connected platform API
python -m wi report --send                   # queues one consolidated report (deduped per day)
python -m wi sheet-sync --with-analytics     # mirrors tracker + analytics to Google Sheets (needs Google creds)
```
- `report --send` queues the message. Deliver it from the outbox (`ops/common.md`). Post exactly one
  report per day. The dedupe key prevents a second one, so if the outbox has none, a report was
  already sent today.
- If Google credentials are configured, also save the report text to Drive "Daily Performance Reports":
  `python -c "from wi.storage import Drive; from wi import report; Drive().upload_text(report.build(), 'Daily Performance Reports', 'report_<date>.md')"`
- Never add metrics that the APIs didn't return. "n/a" is correct when a platform isn't connected.

If `analytics` or `report` fails, queue and deliver an alert (see Finish in `ops/common.md`) that says
what failed and what the team needs to do. Then Finish.
