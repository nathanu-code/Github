# Platform specs used by the presets (checked Oct 19, 2026)

Master encode: MP4, H.264 High, yuv420p, constant frame rate (source rate, max 60 fps), AAC 48 kHz,
moov atom at the front, 3–90 s (Facebook Reels max 90 s).

| Platform | Preset | Why |
|---|---|---|
| TikTok | 9:16 1080×1920 | Each side 360–4096 px. Unaudited API apps can post private only |
| YouTube Shorts | 9:16 1080×1920 | Vertical and ≤3 min is detected as a Short. `videos.insert` has its own 100/day quota |
| Instagram Reels | 9:16 1080×1920 | Width ≤1920, 3 s–15 min, ≤300 MB. All API video posts as Reels (share_to_feed) |
| Facebook Reels | 9:16 1080×1920 | 3–90 s, min 540×960, 30 API Reels per Page per day |
| Threads | 9:16 1080×1920 | Width ≤1920, ≤5 min, 250 posts/day. Needs a public video URL |
| IG + FB feed (Meta Business Suite) | 4:5 1080×1350 | The team's existing manual workflow. No IG feed-only video API |
| Facebook feed (API) | 4:5 1080×1350 | Page `/videos` |
| X | 9:16 720×1280 | X docs list a 1280×1024 max and recommend 720×1280 portrait. ≤140 s plays natively |
| LinkedIn | 4:5 1080×1350 | Ratio 9:16–16:9 accepted. 4:5 keeps a strong feed footprint |

Caption limits: X 280 (weighted), Threads 500, TikTok 2,200, Instagram 2,200 (30 hashtags),
LinkedIn about 3,000, YouTube title 100 / description 5,000.

UI safe zones (banners stay inside): 9:16 top 11%, bottom 22%, sides 7% (14% in the lower half to
clear the action buttons). 4:5: 5% top and sides, 8% bottom.

Sources: docs.x.com/x-api/media, developers.facebook.com/docs/threads/posts,
developers.tiktok.com/doc/content-posting-api-reference-direct-post,
developers.google.com/youtube/v3/docs/videos/insert, developers.google.com/youtube/v3/determine_quota_cost,
developers.facebook.com/docs/video-api/guides/reels-publishing,
developers.facebook.com/docs/instagram-platform/content-publishing,
learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api.
Unconfirmed items: whether X accepts 1080×1920 over the API (so we use 720×1280), and whether
Instagram's 24-hour cap is 50 or 100 (we post 3 a day, well under either).
