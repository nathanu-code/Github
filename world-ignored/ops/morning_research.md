# Morning research (runs ~05:45 PHT)

Goal: find the strongest **verifiable, rights-obtainable** disaster footage from the last 24–72 h, move
cleared items through editing, and send review packages. Fewer than three good videos is fine. Never
fill a slot with weak, unverified or uncleared footage.

Do `ops/common.md` → Start first.

## 1. Approvals and queued work from yesterday
- For every item in READY_FOR_APPROVAL, apply thread decisions (`ops/common.md` → Reading a review thread).
- Items in READY_FOR_EDITING with `edit.change_request` set: apply the requested change (headline,
  trim, safety text), then re-run step 5.

## 2. Authoritative event list
```bash
python -m wi feeds --hours 72
python -m wi tracker-csv        # what we already covered (repeat check)
```

## 3. Find footage (WebSearch, standard mode; send searches in parallel)
Search for footage of actual impact in the last 72 h. Good examples: people escaping, rescues, buildings
collapsing, cars swept away, landslides on camera, floods hitting communities, fires threatening homes,
storm damage happening live. **Skip** distant tornadoes, storm clouds and generic weather shots.
Useful queries: "<disaster> video <country> <this week>", "<place> flood footage", plus news sites and
official agencies (civil protection, fire services, national weather services) that publish video.

For each candidate collect: type, country, location, event date, filming date (verified or "unconfirmed"),
video publication date, original link, original filmer / rights holder (not a repost account), reliable
news or official sources, length and orientation, what happens in the footage, rights status, whether we
covered the event already, and concerns.

Verification checks (write each one down):
- The event is confirmed by ≥2 independent reliable outlets or ≥1 official authority, and/or matches a
  `feeds` event (USGS, GDACS, EONET).
- The footage matches the event: landmarks, signage or language, terrain, weather, and the date of the
  earliest upload you can find. Look for older copies of the same clip. Old footage reposted as new is a
  common failure.
- Original filmer: the earliest uploader, or the person named by a credible outlet or agency. Reposters
  and aggregator pages are not owners.

Score each candidate 0–1 on: `human_impact`, `disaster_activity_on_camera`, `newsworthiness`,
`verification_confidence`, `video_quality` (recency, originality and rights are computed). Set
`rights_outlook`:
- `cleared`: a licence or permission already exists (e.g. official or public-domain footage with terms).
- `agency_available`: offered by a licensing agency (Storyful, Newsflare, ViralHog, Reuters, AP, etc.).
- `contactable`: original filmer identified and reachable.
- `unknown`: anything else.

Write the candidates to `work/candidates.json`. Fields: `title`, `type`, `country`, `location`,
`event_date`, `filmed_date`, `published_date`, `footage_url`, `original_creator`, `platform`,
`orientation`, `duration_s`, `description`, `summary` (1–2 factual sentences, no unsourced numbers),
`sources` [{name, url}], `scores`{...}, `rights_outlook`, `significant_new_development`,
`verification_summary`, `concerns` []. Then:
```bash
python -m wi research-save work/candidates.json
```

## 4. Verification and rights for each pick
```bash
python -m wi verify-event <id>
python -m wi update <id> '{"verification": {"event_verified": true, "checks": [...]}}'   # only if true
python -m wi transition <id> EVENT_VERIFIED/FOOTAGE_UNVERIFIED --note "<sources>"
# only when footage checks pass:
python -m wi update <id> '{"verification": {"footage_verified": true}}'
python -m wi transition <id> FOOTAGE_VERIFIED/RIGHTS_PENDING
```
Rights: if the rights holder is identified but permission isn't on file, add a ready-to-send permission
request (template: `ops/rights_request_template.md`) to the recommendations. **Don't send it yourself.**
Mark rights cleared only when evidence exists: a permission screenshot or email in Drive "Sources and
Permissions", an agency licence, or an open/official licence URL:
```bash
python -m wi update <id> '{"rights": {"status": "cleared", "license_type": "written_permission", "holder": "...",
  "evidence_ref": "<Drive link or licence URL>", "permitted_platforms": ["all"], "attribution": "...",
  "restrictions": "..."}}'
python -m wi transition <id> RIGHTS_CLEARED
```

## 5. Editing (only items with a raw file from an authorised source)
Raw files: the team drops licensed files in Drive "Raw Videos". Ingest with the Drive file id or a local
path: `python -m wi ingest <id> <drive_file_id|path>`, then `python -m wi transition <id> READY_FOR_EDITING`.
```bash
python -m wi update <id> '{"edit": {"headline": "...", "subhead": "", "closing_headline": "...",
  "closing_subhead": "...", "trim": [start_s, end_s]}}'
python -m wi edit <id>          # renders 9:16, 4:5, X 720p; runs QC; uploads to Drive if configured
```
Open each `*.preview.jpg` (Read tool) and check: the banner isn't covering the action, the text is
readable, the footage fills the frame. If QC says MANUAL REVIEW, keep it but make sure the review
package shows the flag. Only if a reviewer asks for the blurred-background fallback:
`python -m wi edit <id> --fit blur`.
```bash
python -m wi captions <id>
python -m wi package <id> --slot post1|post2|post3 --date <YYYY-MM-DD>
```
Slots: post1 = strongest human-impact story; post2 = different country or disaster type; post3 = the
strongest remaining or a significant new development.

## 6. Deliver and finish
Deliver the outbox (`ops/common.md`), then Finish.
