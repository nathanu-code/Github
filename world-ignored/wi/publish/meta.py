"""Facebook Page (Reels + feed video), Instagram (Reels, share_to_feed) and Threads via Meta Graph APIs.

Env:
  META_PAGE_ID, META_PAGE_TOKEN          Page access token (pages_manage_posts, pages_read_engagement,
                                         read_insights, instagram_content_publish, instagram_manage_insights)
  IG_USER_ID                             Instagram professional account linked to the Page
  THREADS_USER_ID, THREADS_TOKEN         Threads API long-lived token (threads_basic, threads_content_publish,
                                         threads_manage_insights); refreshed by `wi tokens-refresh`
  META_GRAPH_VERSION                     default v25.0
"""
from __future__ import annotations

import os
import time

from .. import config
from .base import PostResult, Publisher, PublishError


def _v() -> str:
    return config.env("META_GRAPH_VERSION") or "v25.0"


def G(path: str) -> str:
    return f"https://graph.facebook.com/{_v()}/{path.lstrip('/')}"


class FacebookReels(Publisher):
    name = "facebook_reels"
    env_vars = ("META_PAGE_ID", "META_PAGE_TOKEN")

    def publish(self, video_path, caption, item, *, public_url=None):
        page, tok = config.env("META_PAGE_ID"), config.env("META_PAGE_TOKEN")
        start = self.http("POST", G(f"{page}/video_reels"), data={"upload_phase": "start", "access_token": tok}).json()
        vid = start["video_id"]
        size = os.path.getsize(video_path)
        with open(video_path, "rb") as fh:
            self.http("POST", f"https://rupload.facebook.com/video-upload/{_v()}/{vid}", data=fh,
                      headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)}, timeout=900)
        self.http("POST", G(f"{page}/video_reels"), commit=True, data={
            "upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED", "description": caption,
            "access_token": tok})
        url = self._permalink(vid, tok)
        return PostResult(vid, url or f"https://www.facebook.com/reel/{vid}", "published" if url else "processing")

    def _permalink(self, vid, tok, tries=12):
        for _ in range(tries):
            r = self.http("GET", G(vid), params={"fields": "permalink_url,status", "access_token": tok}).json()
            if r.get("permalink_url"):
                link = r["permalink_url"]
                return link if link.startswith("http") else f"https://www.facebook.com{link}"
            time.sleep(10)
        return None

    def find_existing(self, caption, since_iso):
        page, tok = config.env("META_PAGE_ID"), config.env("META_PAGE_TOKEN")
        r = self.http("GET", G(f"{page}/videos"), params={"fields": "id,description,permalink_url,created_time",
                                                           "since": since_iso, "access_token": tok}).json()
        for v in r.get("data", []):
            if (v.get("description") or "")[:80] == caption[:80]:
                return PostResult(v["id"], f"https://www.facebook.com{v.get('permalink_url', '')}")
        return None

    def post_metrics(self, post_id):
        tok = config.env("META_PAGE_TOKEN")
        r = self.http("GET", G(f"{post_id}/video_insights"), params={"access_token": tok}).json()
        m = {i["name"]: i["values"][0]["value"] for i in r.get("data", []) if i.get("values")}
        likes = m.get("post_video_likes_by_reaction_type") or {}
        return {"views": m.get("blue_reels_play_count") or m.get("fb_reels_total_plays") or m.get("total_video_views"),
                "reach": m.get("post_impressions_unique"),
                "likes": sum(likes.values()) if isinstance(likes, dict) else None,
                "avg_watch_ms": m.get("post_video_avg_time_watched"),
                "watch_time_ms": m.get("post_video_view_time"),
                "shares": (m.get("post_video_social_actions") or {}).get("SHARE") if isinstance(m.get("post_video_social_actions"), dict) else None}

    def account_metrics(self):
        page, tok = config.env("META_PAGE_ID"), config.env("META_PAGE_TOKEN")
        r = self.http("GET", G(page), params={"fields": "followers_count,fan_count", "access_token": tok}).json()
        return {"followers": r.get("followers_count") or r.get("fan_count")}


class FacebookFeed(FacebookReels):
    """4:5 video post on the Page feed (the Meta Business Suite format)."""
    name = "facebook_feed"

    def publish(self, video_path, caption, item, *, public_url=None):
        page, tok = config.env("META_PAGE_ID"), config.env("META_PAGE_TOKEN")
        with open(video_path, "rb") as fh:
            r = self.http("POST", f"https://graph-video.facebook.com/{_v()}/{page}/videos", commit=True,
                          data={"description": caption, "access_token": tok}, files={"source": fh}, timeout=900).json()
        vid = r["id"]
        url = self._permalink(vid, tok)
        return PostResult(vid, url or f"https://www.facebook.com/{page}/videos/{vid}", "published" if url else "processing")


class InstagramReels(Publisher):
    name = "instagram_reels"
    env_vars = ("IG_USER_ID", "META_PAGE_TOKEN")

    def publish(self, video_path, caption, item, *, public_url=None):
        ig, tok = config.env("IG_USER_ID"), config.env("META_PAGE_TOKEN")
        # resumable upload avoids needing a public URL
        c = self.http("POST", G(f"{ig}/media"), data={"media_type": "REELS", "upload_type": "resumable",
                                                     "caption": caption, "share_to_feed": "true",
                                                     "access_token": tok}).json()
        cid, uri = c["id"], c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{_v()}/{c['id']}"
        size = os.path.getsize(video_path)
        with open(video_path, "rb") as fh:
            self.http("POST", uri, data=fh, timeout=900,
                      headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)})
        for _ in range(60):
            st = self.http("GET", G(cid), params={"fields": "status_code,status", "access_token": tok}).json()
            if st.get("status_code") == "FINISHED":
                break
            if st.get("status_code") in ("ERROR", "EXPIRED"):
                raise PublishError(f"IG container {st}", before_commit=True)
            time.sleep(10)
        else:
            raise PublishError("IG container not ready after 10 min", before_commit=True)
        pub = self.http("POST", G(f"{ig}/media_publish"), commit=True,
                        data={"creation_id": cid, "access_token": tok}).json()
        mid = pub["id"]
        link = self.http("GET", G(mid), params={"fields": "permalink", "access_token": tok}).json().get("permalink")
        return PostResult(mid, link or "", "published" if link else "processing")

    def find_existing(self, caption, since_iso):
        ig, tok = config.env("IG_USER_ID"), config.env("META_PAGE_TOKEN")
        r = self.http("GET", G(f"{ig}/media"), params={"fields": "id,caption,permalink,timestamp", "limit": 10,
                                                        "access_token": tok}).json()
        for m in r.get("data", []):
            if (m.get("caption") or "")[:80] == caption[:80] and m.get("timestamp", "") >= since_iso[:19]:
                return PostResult(m["id"], m.get("permalink", ""))
        return None

    def post_metrics(self, post_id):
        tok = config.env("META_PAGE_TOKEN")
        r = self.http("GET", G(f"{post_id}/insights"), params={
            "metric": "views,reach,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time,"
                      "ig_reels_video_view_total_time", "access_token": tok}).json()
        m = {i["name"]: i["values"][0]["value"] for i in r.get("data", []) if i.get("values")}
        return {"views": m.get("views"), "reach": m.get("reach"), "likes": m.get("likes"), "comments": m.get("comments"),
                "shares": m.get("shares"), "saves": m.get("saved"), "avg_watch_ms": m.get("ig_reels_avg_watch_time"),
                "watch_time_ms": m.get("ig_reels_video_view_total_time")}

    def account_metrics(self):
        ig, tok = config.env("IG_USER_ID"), config.env("META_PAGE_TOKEN")
        r = self.http("GET", G(ig), params={"fields": "followers_count,media_count", "access_token": tok}).json()
        return {"followers": r.get("followers_count")}


class InstagramFeed(Publisher):
    """The API has no feed-only video; the 4:5 joint FB+IG feed post stays a manual Meta Business Suite task."""
    name = "instagram_feed"
    posting_method = "manual (Meta Business Suite)"

    def available(self):
        return False, "Instagram's API publishes all video as Reels; post the 4:5 version manually in Meta Business Suite"


class Threads(Publisher):
    name = "threads"
    env_vars = ("THREADS_USER_ID", "THREADS_TOKEN")

    def needs_public_url(self):
        return True

    def publish(self, video_path, caption, item, *, public_url=None):
        if not public_url:
            raise PublishError("Threads needs a public video URL", before_commit=True)
        uid, tok = config.env("THREADS_USER_ID"), config.env("THREADS_TOKEN")
        base = "https://graph.threads.net/v1.0"
        c = self.http("POST", f"{base}/{uid}/threads", data={"media_type": "VIDEO", "video_url": public_url,
                                                             "text": caption, "access_token": tok}).json()
        cid = c["id"]
        for _ in range(60):
            st = self.http("GET", f"{base}/{cid}", params={"fields": "status,error_message", "access_token": tok}).json()
            if st.get("status") == "FINISHED":
                break
            if st.get("status") in ("ERROR", "EXPIRED"):
                raise PublishError(f"Threads container {st}", before_commit=True)
            time.sleep(10)
        pub = self.http("POST", f"{base}/{uid}/threads_publish", commit=True,
                        data={"creation_id": cid, "access_token": tok}).json()
        link = self.http("GET", f"{base}/{pub['id']}", params={"fields": "permalink", "access_token": tok}).json().get("permalink")
        return PostResult(pub["id"], link or "", "published" if link else "processing")

    def find_existing(self, caption, since_iso):
        uid, tok = config.env("THREADS_USER_ID"), config.env("THREADS_TOKEN")
        r = self.http("GET", f"https://graph.threads.net/v1.0/{uid}/threads",
                      params={"fields": "id,text,permalink,timestamp", "limit": 10, "access_token": tok}).json()
        for t in r.get("data", []):
            if (t.get("text") or "")[:80] == caption[:80]:
                return PostResult(t["id"], t.get("permalink", ""))
        return None

    def post_metrics(self, post_id):
        tok = config.env("THREADS_TOKEN")
        r = self.http("GET", f"https://graph.threads.net/v1.0/{post_id}/insights",
                      params={"metric": "views,likes,replies,reposts,quotes,shares", "access_token": tok}).json()
        m = {i["name"]: i["values"][0]["value"] for i in r.get("data", []) if i.get("values")}
        return {"views": m.get("views"), "likes": m.get("likes"), "comments": m.get("replies"),
                "shares": (m.get("reposts") or 0) + (m.get("quotes") or 0) + (m.get("shares") or 0)}

    def account_metrics(self):
        uid, tok = config.env("THREADS_USER_ID"), config.env("THREADS_TOKEN")
        r = self.http("GET", f"https://graph.threads.net/v1.0/{uid}/threads_insights",
                      params={"metric": "followers_count", "access_token": tok}).json()
        for i in r.get("data", []):
            if i["name"] == "followers_count":
                return {"followers": (i.get("total_value") or {}).get("value")}
        return {}
