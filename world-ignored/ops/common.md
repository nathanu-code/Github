# Common steps for every scheduled run

## Start
```bash
git clone -q -b world-ignored-ops https://github.com/nathanu-code/Github wi-ops && cd wi-ops/world-ignored
bash scripts/setup.sh
python -m wi health
```
**Slack access.** If `SLACK_BOT_TOKEN` is set (`wi health` → `slack_bot_token: true`), Python posts and
reads Slack itself: run `python -m wi slack-commands`, use `python -m wi approvals <id>` without a file,
and skip the outbox steps below (nothing gets queued). If neither the bot token nor the Slack connector
tools (`slack_send_message` etc.) are available, Slack can't be reached: still do the rest of the run,
commit state, and end your run with a clear summary saying Slack delivery was impossible.

Otherwise (connector mode), read the last ~30 messages of `#world-ignored` (`slack_read_channel`, channel `C0C7UL356KF`). If an
approver (Nathan `U0A4HF5FN6S`, Admin `U0A4HF78STG`) has posted `WI STOP`, `WI PAUSE` or `WI RESUME`
since the last run, apply it:
`python -m wi control stop|pause|resume --by <Name> --reason "<their message>"`.

## Delivering Slack messages (connector mode)
Python never posts directly unless `SLACK_BOT_TOKEN` is set. It queues messages instead:
```bash
python -m wi outbox            # JSON list of queued messages
```
For each queued message, in order:
1. Post `text` with `slack_send_message` to `channel_id` (and `thread_ts` if set). Post the text exactly
   as given. It is already formatted and labelled.
2. Record the returned message ts: `python -m wi slack-sent <id> <ts>`.
Files listed under `files` can't be uploaded through the connector. If they're in Drive, the links are
already in the text.

## Reading a review thread (approvals)
For an item awaiting approval, find its review message ts in `state/slack_sent.json` (kind
`review_package`, matching `item_id`). Read the replies with `slack_read_thread`, convert them to JSON
`[{"user": "<Slack user ID>", "ts": "<ts>", "text": "<text>"}]`, save to `work/thread_<id>.json`, then:
```bash
python -m wi approvals <id> work/thread_<id>.json
```
Never decide approval yourself. Only this command does.

## Finish (always, even after a failure)
```bash
cd .. && git add world-ignored/state && git commit -qm "ops: <runbook> $(TZ=Asia/Manila date +%F_%H%M)" || true
for i in 1 2 3 4; do git pull -q --rebase origin world-ignored-ops && git push -q origin world-ignored-ops && break; sleep $((2**i)); done
```
If any step failed, queue an alert so the team sees it:
`python -c "from wi import slack; slack.send(slack.alert('<what failed>', '<error>', '<what the team should do>'), kind='alert', dedupe_key='alert:<runbook>:<date>')"`
then deliver it from the outbox.
