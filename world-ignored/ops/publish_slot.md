# Publishing slot (post1 07:45, post2 12:45, post3 18:45 PHT; posts go out at 08:00 / 13:00 / 19:00)

Do `ops/common.md` → Start first. The routine message tells you the slot id.

1. For the item scheduled in this slot today that is still READY_FOR_APPROVAL, apply thread decisions
   (`ops/common.md` → Reading a review thread). Don't approve anything yourself.
2. Wait until the slot time (PHT) if you're early. Use a Monitor until-loop on `date`; don't sleep in a chain.
3. Run:
   ```bash
   python -m wi publish-slot <slot>
   ```
   The command enforces every gate: pause/stop, `publishing_live`, approval of this exact version and
   these platforms, rights, and verification. It posts through the official APIs where credentials exist
   and marks every other platform "manual". Nothing is posted twice: the ledger blocks re-posts and checks
   for interrupted uploads.
   - `_empty`: nothing was approved for this slot. Don't post to Slack (no noise). The 07:00 report already
     lists the queue.
   - `_blocked`: the command queues a short thread reply on the review package explaining why.
4. Deliver the outbox (confirmations with post URLs, manual-upload packages, alerts), then Finish.

`needs_check` means a publish call may or may not have gone through. Never retry it blindly. The alert
asks the team to check the account.

**Recording manual posts.** When an approver replies in the review thread with links to posts they
uploaded by hand (manual platforms, or a confirmed `needs_check`), record each one so the tracker and
analytics include it:
```bash
python -m wi record-post <id> <platform> <https://post-url> --by <Name>
```
