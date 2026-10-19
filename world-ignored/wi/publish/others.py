"""YouTube Shorts, TikTok, X and LinkedIn adapters.

Env:
  YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN   (scopes youtube.upload, youtube.readonly,
                                                                    yt-analytics.readonly)
  TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN     (video.publish, video.list, user.info.stats)
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET          (OAuth 1.0a user context; doesn't expire)
  LINKEDIN_ACCESS_TOKEN, LINKEDIN_ORG_ID                            (w_organization_social, r_organization_social,
                                                                    rw_organization_admin); LINKEDIN_VERSION=YYYYMM
"""
from __future__ import annotations

import math
import os
import time

import requests

from .. import config
from .base import PostResult, Publisher, PublishError


# --------------------------------------------------------------------------------------------------
class YouTubeShorts(Publisher):
    name = "youtube_shorts"
    env_vars = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")

    def _token(self) -> str:
        r = self.http("POST", "https://oauth2.googleapis.com/token", data={
            "client_id": config.env("YOUTUBE_CLIENT_ID"), "client_secret": config.env("YOUTUBE_CLIENT_SECRET"),
            "refresh_token": config.env("YOUTUBE_REFRESH_TOKEN"), "grant_type": "refresh_token"})
        return r.json()["access_token"]

    def publish(self, video_path, caption, item, *, public_url=None):
        tok = self._token()
        caps = item["captions"]
        body = {"snippet": {"title": caps["youtube_title"], "description": caps["youtube_description"],
                            "categoryId": "25", "tags": ["World Ignored", item["event"]["type"], item["event"]["country"]]},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
        size = os.path.getsize(video_path)
        init = self.http("POST", "https://www.googleapis.com/upload/youtube/v3/videos",
                         params={"uploadType": "resumable", "part": "snippet,status"}, json=body,
                         headers={"Authorization": f"Bearer {tok}", "X-Upload-Content-Type": "video/mp4",
                                  "X-Upload-Content-Length": str(size)})
        loc = init.headers["Location"]
        with open(video_path, "rb") as fh:
            # the final byte completes the upload and creates the video: treat as the commit call
            r = self.http("PUT", loc, commit=True, data=fh, timeout=1800,
                          headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"})
        vid = r.json()["id"]
        return PostResult(vid, f"https://youtube.com/shorts/{vid}")

    def find_existing(self, caption, since_iso):
        tok = self._token()
        r = self.http("GET", "https://www.googleapis.com/youtube/v3/search", headers={"Authorization": f"Bearer {tok}"},
                      params={"part": "snippet", "forMine": "true", "type": "video", "maxResults": 10,
                              "order": "date"}).json()
        for v in r.get("items", []):
            if v["snippet"]["publishedAt"] >= since_iso[:19] and v["snippet"]["title"][:40] in caption:
                vid = v["id"]["videoId"]
                return PostResult(vid, f"https://youtube.com/shorts/{vid}")
        return None

    def post_metrics(self, post_id):
        tok = self._token()
        h = {"Authorization": f"Bearer {tok}"}
        s = self.http("GET", "https://www.googleapis.com/youtube/v3/videos", headers=h,
                      params={"part": "statistics", "id": post_id}).json()
        st = s["items"][0]["statistics"] if s.get("items") else {}
        out = {"views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
               "comments": int(st.get("commentCount", 0))}
        try:
            today = time.strftime("%Y-%m-%d")
            a = self.http("GET", "https://youtubeanalytics.googleapis.com/v2/reports", headers=h, params={
                "ids": "channel==MINE", "startDate": "2020-01-01", "endDate": today, "filters": f"video=={post_id}",
                "metrics": "shares,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained"}).json()
            if a.get("rows"):
                sh, mins, avd, avp, subs = a["rows"][0]
                out.update(shares=sh, watch_time_ms=mins * 60000, avg_watch_ms=avd * 1000, retention_pct=avp,
                           subscribers_gained=subs)
        except PublishError:
            pass
        return out

    def account_metrics(self):
        tok = self._token()
        r = self.http("GET", "https://www.googleapis.com/youtube/v3/channels", headers={"Authorization": f"Bearer {tok}"},
                      params={"part": "statistics", "mine": "true"}).json()
        st = r["items"][0]["statistics"] if r.get("items") else {}
        return {"followers": int(st.get("subscriberCount", 0)) if st else None}


# --------------------------------------------------------------------------------------------------
class TikTok(Publisher):
    name = "tiktok"
    env_vars = ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN")
    API = "https://open.tiktokapis.com/v2"

    def _token(self) -> str:
        r = self.http("POST", f"{self.API}/oauth/token/", data={
            "client_key": config.env("TIKTOK_CLIENT_KEY"), "client_secret": config.env("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token", "refresh_token": config.env("TIKTOK_REFRESH_TOKEN")},
            headers={"Content-Type": "application/x-www-form-urlencoded"}).json()
        if r.get("refresh_token") and r["refresh_token"] != config.env("TIKTOK_REFRESH_TOKEN"):
            # TikTok rotated the refresh token: the stored secret must be updated (reported in health checks)
            (config.STATE_DIR / "token_rotation_needed.txt").write_text("TIKTOK_REFRESH_TOKEN rotated\n")
        return r["access_token"]

    def publish(self, video_path, caption, item, *, public_url=None):
        tok = self._token()
        h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
        info = self.http("POST", f"{self.API}/post/publish/creator_info/query/", headers=h).json()["data"]
        privacy = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in info.get("privacy_level_options", []) \
            else info["privacy_level_options"][0]
        size = os.path.getsize(video_path)
        chunk = min(size, 10 * 1024 * 1024)
        n = max(1, size // chunk)
        init = self.http("POST", f"{self.API}/post/publish/video/init/", commit=True, headers=h, json={
            "post_info": {"title": caption, "privacy_level": privacy, "disable_duet": False,
                          "disable_comment": False, "disable_stitch": False},
            "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk,
                            "total_chunk_count": n}}).json()["data"]
        pid, up = init["publish_id"], init["upload_url"]
        with open(video_path, "rb") as fh:
            for i in range(n):
                start = i * chunk
                data = fh.read(chunk if i < n - 1 else size - start)
                self.http("PUT", up, data=data, headers={"Content-Type": "video/mp4",
                                                         "Content-Range": f"bytes {start}-{start + len(data) - 1}/{size}"})
        for _ in range(60):
            st = self.http("POST", f"{self.API}/post/publish/status/fetch/", headers=h, json={"publish_id": pid}).json()["data"]
            if st.get("status") == "PUBLISH_COMPLETE":
                ids = st.get("publicaly_available_post_id") or []
                vid = str(ids[0]) if ids else pid
                user = info.get("creator_username", "")
                url = f"https://www.tiktok.com/@{user}/video/{vid}" if ids else ""
                return PostResult(vid, url, "published" if url else "processing")
            if st.get("status") == "FAILED":
                raise PublishError(f"TikTok failed: {st.get('fail_reason')}", before_commit=False)
            time.sleep(10)
        return PostResult(pid, "", "processing")

    def post_metrics(self, post_id):
        tok = self._token()
        r = self.http("POST", f"{self.API}/video/query/", params={"fields": "id,view_count,like_count,comment_count,share_count,share_url"},
                      headers={"Authorization": f"Bearer {tok}"}, json={"filters": {"video_ids": [post_id]}}).json()
        v = (r.get("data", {}).get("videos") or [{}])[0]
        return {"views": v.get("view_count"), "likes": v.get("like_count"), "comments": v.get("comment_count"),
                "shares": v.get("share_count"), "url": v.get("share_url")}

    def account_metrics(self):
        tok = self._token()
        r = self.http("GET", f"{self.API}/user/info/", params={"fields": "follower_count,likes_count,video_count"},
                      headers={"Authorization": f"Bearer {tok}"}).json()
        return {"followers": r.get("data", {}).get("user", {}).get("follower_count")}


# --------------------------------------------------------------------------------------------------
class X(Publisher):
    name = "x"
    env_vars = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")
    API = "https://api.x.com/2"

    def _auth(self):
        from requests_oauthlib import OAuth1
        return OAuth1(config.env("X_API_KEY"), config.env("X_API_SECRET"), config.env("X_ACCESS_TOKEN"),
                      config.env("X_ACCESS_SECRET"))

    def publish(self, video_path, caption, item, *, public_url=None):
        auth = self._auth()
        size = os.path.getsize(video_path)
        init = self.http("POST", f"{self.API}/media/upload/initialize", auth=auth, json={
            "media_type": "video/mp4", "total_bytes": size, "media_category": "tweet_video"}).json()
        mid = init["data"]["id"]
        seg = 4 * 1024 * 1024
        with open(video_path, "rb") as fh:
            for i in range(math.ceil(size / seg)):
                self.http("POST", f"{self.API}/media/upload/{mid}/append", auth=auth,
                          data={"segment_index": i}, files={"media": fh.read(seg)})
        fin = self.http("POST", f"{self.API}/media/upload/{mid}/finalize", auth=auth).json()["data"]
        info = fin.get("processing_info")
        while info and info.get("state") in ("pending", "in_progress"):
            time.sleep(info.get("check_after_secs", 5))
            info = self.http("GET", f"{self.API}/media/upload", auth=auth,
                             params={"command": "STATUS", "media_id": mid}).json()["data"].get("processing_info")
        if info and info.get("state") == "failed":
            raise PublishError(f"X media processing failed: {info}", before_commit=True)
        tw = self.http("POST", f"{self.API}/tweets", commit=True, auth=auth,
                       json={"text": caption, "media": {"media_ids": [mid]}}).json()["data"]
        me = self.http("GET", f"{self.API}/users/me", auth=auth).json()["data"]["username"]
        return PostResult(tw["id"], f"https://x.com/{me}/status/{tw['id']}")

    def find_existing(self, caption, since_iso):
        auth = self._auth()
        me = self.http("GET", f"{self.API}/users/me", auth=auth).json()["data"]
        r = self.http("GET", f"{self.API}/users/{me['id']}/tweets", auth=auth,
                      params={"max_results": 5, "start_time": since_iso[:19] + "Z"}).json()
        for t in r.get("data", []):
            if t["text"][:60] == caption[:60]:
                return PostResult(t["id"], f"https://x.com/{me['username']}/status/{t['id']}")
        return None

    def post_metrics(self, post_id):
        r = self.http("GET", f"{self.API}/tweets", auth=self._auth(),
                      params={"ids": post_id, "tweet.fields": "public_metrics,non_public_metrics"}).json()
        t = (r.get("data") or [{}])[0]
        pm, npm = t.get("public_metrics", {}), t.get("non_public_metrics", {})
        return {"views": pm.get("impression_count") or npm.get("impression_count"), "likes": pm.get("like_count"),
                "comments": pm.get("reply_count"), "shares": (pm.get("retweet_count") or 0) + (pm.get("quote_count") or 0),
                "saves": pm.get("bookmark_count"), "link_clicks": npm.get("url_link_clicks"),
                "profile_visits": npm.get("user_profile_clicks")}

    def account_metrics(self):
        r = self.http("GET", f"{self.API}/users/me", auth=self._auth(), params={"user.fields": "public_metrics"}).json()
        return {"followers": r["data"]["public_metrics"]["followers_count"]}


# --------------------------------------------------------------------------------------------------
class LinkedIn(Publisher):
    name = "linkedin"
    env_vars = ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_ORG_ID")

    def _h(self):
        return {"Authorization": f"Bearer {config.env('LINKEDIN_ACCESS_TOKEN')}",
                "Linkedin-Version": config.env("LINKEDIN_VERSION") or "202609",
                "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"}

    def publish(self, video_path, caption, item, *, public_url=None):
        org = f"urn:li:organization:{config.env('LINKEDIN_ORG_ID')}"
        size = os.path.getsize(video_path)
        init = self.http("POST", "https://api.linkedin.com/rest/videos?action=initializeUpload", headers=self._h(),
                         json={"initializeUploadRequest": {"owner": org, "fileSizeBytes": size,
                                                           "uploadCaptions": False, "uploadThumbnail": False}}).json()["value"]
        urn, etags = init["video"], []
        with open(video_path, "rb") as fh:
            for ins in init["uploadInstructions"]:
                fh.seek(ins["firstByte"])
                data = fh.read(ins["lastByte"] - ins["firstByte"] + 1)
                r = self.http("PUT", ins["uploadUrl"], data=data, headers={"Content-Type": "application/octet-stream"})
                etags.append(r.headers.get("etag"))
        self.http("POST", "https://api.linkedin.com/rest/videos?action=finalizeUpload", headers=self._h(), json={
            "finalizeUploadRequest": {"video": urn, "uploadToken": init.get("uploadToken", ""), "uploadedPartIds": etags}})
        for _ in range(60):
            st = self.http("GET", f"https://api.linkedin.com/rest/videos/{requests.utils.quote(urn, safe='')}",
                           headers=self._h()).json()
            if st.get("status") == "AVAILABLE":
                break
            if st.get("status") == "PROCESSING_FAILED":
                raise PublishError(f"LinkedIn video failed: {st}", before_commit=True)
            time.sleep(10)
        r = self.http("POST", "https://api.linkedin.com/rest/posts", commit=True, headers=self._h(), json={
            "author": org, "commentary": caption, "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": {"media": {"title": item["event"]["title"], "id": urn}},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False})
        post = r.headers.get("x-restli-id", "")
        return PostResult(post, f"https://www.linkedin.com/feed/update/{post}/")

    def post_metrics(self, post_id):
        org = f"urn:li:organization:{config.env('LINKEDIN_ORG_ID')}"
        key = "ugcPosts" if "ugcPost" in post_id else "shares"
        r = self.http("GET", "https://api.linkedin.com/rest/organizationalEntityShareStatistics", headers=self._h(),
                      params={"q": "organizationalEntity", "organizationalEntity": org, f"{key}": f"List({post_id})"}).json()
        s = (r.get("elements") or [{}])[0].get("totalShareStatistics", {})
        return {"views": s.get("impressionCount"), "reach": s.get("uniqueImpressionsCount"), "likes": s.get("likeCount"),
                "comments": s.get("commentCount"), "shares": s.get("shareCount"), "link_clicks": s.get("clickCount"),
                "engagement_rate": s.get("engagement")}

    def account_metrics(self):
        org = f"urn:li:organization:{config.env('LINKEDIN_ORG_ID')}"
        r = self.http("GET", f"https://api.linkedin.com/rest/networkSizes/{requests.utils.quote(org, safe='')}",
                      headers=self._h(), params={"edgeType": "COMPANY_FOLLOWED_BY_MEMBER"}).json()
        return {"followers": r.get("firstDegreeSize")}
