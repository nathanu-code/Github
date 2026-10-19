# Integration and authorisation audit (Oct 19, 2026)

## What existed before this build
| Area | Finding |
|---|---|
| Workflow | Manual. ChatGPT suggests disaster videos each morning. Admin finds cleaner (watermark-free) copies on X and other sites, has ChatGPT edit and caption them, then posts by hand. IG and FB are posted together through Meta Business Suite at 4:5. |
| Slack | Private channel #world-ignored (C0C7UL356KF). Members: Admin, Nathan, Faith, plus an "Ops Bot (Team)" app. No automation messages. Daily posting screenshots are shared manually. |
| Slack connector | Available to Claude, signed in as **Faith** (U0A5DQ5TDT2). Posts appear under her name. Can't upload files. |
| Google Drive | Connector available (admin@grandeurdesignsupply.com). **No existing World Ignored folders, trackers or video files.** The Drive connector can create and read files but can't edit Sheets or upload large media. No Google Sheets editor connector exists in the org. |
| Buffer | Connected. Org "My Organization", free plan (3 channels, 10 scheduled posts). Only channel: GrowSales AI LinkedIn page. **No World Ignored channels.** |
| TikTok via Higgsfield | Connector present. **No TikTok accounts linked.** |
| Notion | Installed, not connected (not needed). |
| Social APIs | **No API keys, OAuth apps or tokens** for any World Ignored account. |
| Hosting | Claude Code cloud environment (Anthropic). Routines (scheduled triggers) available. Repo: nathanu-code/Github (**public**). |
| Editing templates | No template files. House style taken from posted screenshots: bold white uppercase headline, dark semi-transparent banner, location and date line. Previous edits used a blurred background, which Nathan asked to replace with full screen. |
| Previously published | 5 posts identified from Slack screenshots (Oct 6–17), imported into the tracker for repeat checks. |
| Reporting | Manual screenshots of Meta insights. No automation. TikTok views reported as near zero. |

## Platform status
| Platform | Account access | Publish via API | Analytics via API | What is automated today | Blocker |
|---|---|---|---|---|---|
| TikTok | ❌ not connected | adapter built, untested | adapter built | 9:16 export, caption, manual package | App + Content Posting API audit (unaudited = private only), tokens |
| YouTube Shorts | ❌ | adapter built, untested | adapter built (Data + Analytics API) | 9:16 export, title/description, manual package | OAuth client + refresh token as channel owner |
| Instagram Reels | ❌ | adapter built, untested | adapter built | 9:16 export, caption, manual package | Meta app, Page token, IG user ID |
| Instagram feed (4:5) | n/a | **not possible via API** | via Reels insights | 4:5 export + caption for Meta Business Suite | none (manual by design) |
| Facebook Reels + feed | ❌ | adapter built, untested | adapter built | 9:16 + 4:5 exports, caption | Meta app, Page token |
| Threads | ❌ | adapter built, untested | adapter built | 9:16 export, caption | Threads token + Google storage (needs a public video URL) |
| X | ❌ | adapter built, untested | adapter built | 720×1280 export, 280-char caption | Developer app (pay-per-use) + OAuth 1.0a user tokens |
| LinkedIn | ❌ (the Buffer channel is GrowSales AI, not World Ignored) | adapter built, untested | adapter built | 4:5 export, caption | Community Management API approval + token |

## Tasks
| Task | Status |
|---|---|
| Disaster discovery (feeds + Claude web research) | ✅ built. Feeds tested live (USGS, GDACS, EONET OK; GDELT rate-limited, throttled; ReliefWeb needs appname) |
| Verification workflow and statuses | ✅ built and tested (gates block skipping, credit-only rights, missing raw file) |
| Footage acquisition | ⚠️ by design only from rights holders or agencies (Drive "Raw Videos"); not automated scraping |
| Rights tracking and permission drafts | ✅ built; sending requests and recording evidence are team actions |
| Editing (banners, safety text, audio) | ✅ built and tested on sample footage |
| Full-frame reframing + subject tracking | ✅ built and tested (YOLOX, YuNet, motion, saliency, text detection) |
| Automated QC + preview frames | ✅ built and tested |
| Captions/hashtags/YouTube titles | ✅ built and tested (refuses unsourced casualty claims or missing credit) |
| Drive organisation | ✅ folders created; ⚠️ uploads need Google credentials |
| Tracker (Sheets) | ✅ sheet created + seeded; ⚠️ automatic sync needs Google credentials (git state is the source of truth meanwhile) |
| Slack review + approvals | ✅ built and tested (approver allow-list, version codes, no self-approval); posts via connector |
| Publishing (7 platforms) | ✅ adapters + idempotent runner tested with a fake platform; ❌ live tests blocked by credentials |
| Daily report | ✅ built; scheduled; analytics blocked by credentials |
| Scheduling (no laptop needed) | ✅ Claude Code routines created: research 05:47, report 06:52, 3 publish slots. **All currently disabled** until they have Slack and repo access, so they don't burn usage producing nothing. ⚠️ Test fire: clone, setup, analytics and report all worked, but routines lack Slack and repo-push access until they're given a source and connector in the routines UI (docs/SETUP.md §0) |
| Pause / emergency stop | ✅ `WI PAUSE` / `WI STOP` in Slack, or `wi control` |

## Security notes
- No secrets are stored in the repo, Slack, Drive or the tracker. `slack.scrub` redacts token-like
  strings from any outgoing message.
- The repository **nathanu-code/Github is public**. Code and tracker state (event names, public
  footage links, captions) are visible to anyone. Make the repo private in GitHub → Settings → General
  → Danger zone → Change visibility. Nothing else needs to change.
- The automation can't approve its own work: the connector identity is excluded from approvers.
- Publishing is off (`publishing_live: false`) until a person turns it on.
