# Setup: credentials and access

Secrets go in the **Claude Code cloud environment** that the routines run in, never in this repo,
Slack or Drive. Open the environment menu in a Claude Code session's title bar, choose **Edit**, and
add each value as an environment variable or network secret with the exact name below. New sessions
(including routine runs) pick them up automatically. Check with `python -m wi health`.

Priority order: steps 1–3 unblock the whole pipeline. Steps 4–9 each switch one platform from
manual to automatic.

## 0. Give the scheduled routines repo + Slack access (top priority)
A test run of the 7 AM routine on Oct 19 showed that routines created from a session have **no
connectors** (this org can't attach them that way) and **can't push** to the repo, so they could build
the report but couldn't post it or save state. Fix both in claude.ai, under Code, then Routines:
1. Open each "World Ignored" routine, then **Edit**, then add the repository **nathanu-code/Github** as a
   source (with push access), and attach the **Slack** connector (and Google Drive).
2. Or set `SLACK_BOT_TOKEN` (step 3), and Python posts and reads Slack itself.
Then use "Run now" on the report routine and check that the report lands in #world-ignored.

## 1. Google Drive + Sheets ✅ connected (Oct 19, 2026)
Set up with Google OAuth as **admin@grandeurdesignsupply.com** (admin@ has Editor access to Faith's
"*World Ignored" folder, so files stay in place and no service-account key is needed).
- Google Cloud project **World Ignored Automation**; Drive API + Sheets API enabled; consent screen
  **Internal**; scopes `drive` + `spreadsheets`; OAuth client "World Ignored Playground" (Web application,
  redirect URI `https://developers.google.com/oauthplayground`).
- Refresh token obtained in Google OAuth Playground and saved, with the client ID and secret, as
  environment variables `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`,
  `GOOGLE_OAUTH_REFRESH_TOKEN` in the cloud environment "Greg YouTube Cloud fare" (edit it from
  claude.ai/code → environment picker under the prompt box → gear → Edit).
- Root folder: `*World Ignored` (`18qBzGnXMVRlgTQlq1YRVk2aHpxtqKwGX`); the 10 automation subfolders
  and the Content Tracker sheet live inside it (ids in `state/drive.json`).
- Check any time: `python -m wi drive-check <folder id> --upload-test`.
- Revoke: myaccount.google.com/permissions (as admin@) → World Ignored Automation → Remove access.
  To rotate the client secret: Cloud Console → Google Auth Platform → Clients → add a new secret,
  update the environment variable, then disable and delete the old one.

## 2. Footage rights process (team decision, no code needed)
Pick at least one route: direct permission (template: `ops/rights_request_template.md`) and/or a
licensing-agency account (Storyful, Newsflare, ViralHog, Trusted Media, Reuters Connect, AP). Licensed
raw files go in Drive **World Ignored/Raw Videos**, and evidence goes in **Sources and Permissions**.

## 3. Slack bot (recommended)
Today the automation posts through the Slack connector, which is signed in as Faith, so messages
appear under her name, and it can't upload files. A bot fixes both:
1. Go to api.slack.com/apps, then **Create app**, in the Grandeur Materials workspace.
2. Add bot scopes `chat:write`, `files:write`, `groups:history`, `channels:history`, `reactions:read`.
3. Install the app, then `/invite @<bot>` in #world-ignored.
4. Secret `SLACK_BOT_TOKEN` = the `xoxb-…` token.
After this, Faith (`U0A5DQ5TDT2`) can be added as an approver in `config/settings.yaml`.

## 4. Meta: Facebook Page, Instagram, Threads
1. At developers.facebook.com, create an app (type Business), linked to the business that owns the
   World Ignored Page.
2. Add the products Facebook Login for Business, Instagram Graph API and Threads API.
3. Permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `read_insights`,
   `pages_manage_engagement`, `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`,
   `threads_basic`, `threads_content_publish`, `threads_manage_insights`. Accounts with a role on the
   app work without App Review. Make Faith or Admin an app admin.
4. Generate a long-lived **Page** access token. Set the secrets `META_PAGE_ID`, `META_PAGE_TOKEN`, and
   `IG_USER_ID` (the Instagram professional account ID connected to the Page).
5. Threads: generate a long-lived Threads user token (valid 60 days, refreshable). Set `THREADS_USER_ID`
   and `THREADS_TOKEN`.

Note: Instagram's API posts all video as **Reels** (share_to_feed=true). The 4:5 joint FB+IG **feed**
post through Meta Business Suite has no API equivalent, so it stays a manual upload. The automation
prepares the 4:5 file and the caption.

## 5. YouTube
1. In Google Cloud (the same project is fine), enable the **YouTube Data API v3** and the **YouTube
   Analytics API**.
2. Create an OAuth client and authorise it **as the World Ignored channel owner** with the scopes
   `youtube.upload`, `youtube.readonly` and `yt-analytics.readonly`.
3. Set `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.
4. Publish the OAuth consent screen ("In production"). Refresh tokens issued in Testing mode expire
   after 7 days.

## 6. TikTok
1. At developers.tiktok.com, create an app with **Login Kit** and **Content Posting API** (Direct Post
   enabled), and the scopes `video.publish`, `video.list`, `user.info.stats`.
2. **Audit:** until TikTok audits the app, API posts are private (SELF_ONLY) only. Apply for the audit
   right away. It reportedly takes weeks.
3. Authorise the World Ignored account and set `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`,
   `TIKTOK_REFRESH_TOKEN`. If TikTok rotates the refresh token, the daily report will say so.

## 7. X
1. At developer.x.com, create a project and app (pay-per-use: about $0.015 per post; posts with links
   cost more, so captions avoid links).
2. User authentication: OAuth 1.0a, Read and Write. Generate the access token and secret **for the
   World Ignored account**.
3. Set `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET` (these don't expire).

## 8. LinkedIn
1. At linkedin.com/developers, create an app linked to the World Ignored Page, then request the
   **Community Management API** product.
2. Scopes: `w_organization_social`, `r_organization_social`, `rw_organization_admin`. The authorising
   member must be a Page admin.
3. Set `LINKEDIN_ACCESS_TOKEN` (60 days) and `LINKEDIN_ORG_ID`. The report warns before expiry once
   connected.

## 9. Optional
- ReliefWeb API: request an approved `appname` at apidoc.reliefweb.int for one more official source.
- Buffer: the connected Buffer org ("My Organization") has only GrowSales AI's LinkedIn page and the
  free plan (3 channels, 10 scheduled posts). It could replace steps 4–8 for some networks, but it needs
  a public video URL per post and a paid plan for 7 channels. Direct APIs are cleaner.

## Going live
When `wi health` shows the platforms you want as connected, the first approved videos have
been checked in a dry run (`python -m wi publish-slot post1 --dry-run`), and rights evidence exists:
set `control.publishing_live: true` in `config/settings.yaml` on the `world-ignored-ops` branch.
Publishing stays off until a person makes that change.
