import copy

import pytest

from wi import config, models
from wi.publish import runner
from wi.publish.base import PostResult, Publisher, PublishError
from wi.store import Store

from test_core import _cleared_item


class Fake(Publisher):
    name = "x"
    calls = []
    fail_plan = []          # list of exceptions to raise on successive publish calls
    existing = None

    def available(self):
        return True, "ok"

    def publish(self, video_path, caption, item, *, public_url=None):
        Fake.calls.append(caption)
        if Fake.fail_plan:
            raise Fake.fail_plan.pop(0)
        return PostResult(f"id{len(Fake.calls)}", f"https://x.com/wi/status/{len(Fake.calls)}")

    def find_existing(self, caption, since_iso):
        return Fake.existing


@pytest.fixture
def env(tmp_path, monkeypatch):
    s = copy.deepcopy(config.settings())
    s["control"]["publishing_live"] = True
    monkeypatch.setattr(config, "settings", lambda: s)
    monkeypatch.setattr(runner, "adapter", lambda p: Fake())
    monkeypatch.setattr("time.sleep", lambda *_: None)
    Fake.calls, Fake.fail_plan, Fake.existing = [], [], None
    st = Store(tmp_path)
    it = _cleared_item()
    video = tmp_path / "v.mp4"
    video.write_bytes(b"0")
    it["status"] = models.APPROVED
    it["captions"] = {"x": "caption"}
    it["edit"]["outputs"] = {"x720": {"path": str(video), "sha256": "a", "qc": {"passed": True}}}
    it["approval"].update(status="approved", content_hash=models.content_hash(it), platforms=["x"])
    st.add(it)
    return st, it


def test_publishes_once_and_never_duplicates(env):
    st, it = env
    r1 = runner.publish_item(it, st)
    r2 = runner.publish_item(it, st)
    assert r1["x"]["status"] == "published" and r1["x"]["url"]
    assert r2["x"]["note"] == "already done"
    assert len(Fake.calls) == 1


def test_retry_only_before_commit(env):
    st, it = env
    Fake.fail_plan = [PublishError("upload 503", before_commit=True)]
    r = runner.publish_item(it, st)
    assert r["x"]["status"] == "published" and len(Fake.calls) == 2


def test_ambiguous_failure_is_not_retried(env):
    st, it = env
    Fake.fail_plan = [PublishError("timeout on create", before_commit=False)]
    r = runner.publish_item(it, st)
    assert r["x"]["status"] == "needs_check" and len(Fake.calls) == 1


def test_interrupted_job_recovers_existing_post(env):
    st, it = env
    key = f"{it['id']}:x:{models.content_hash(it)}"
    it["publish"]["x"] = {"status": "uploading", "key": key, "started_at": "2026-10-19T00:00:00+00:00", "attempts": 1}
    Fake.existing = PostResult("id9", "https://x.com/wi/status/9")
    r = runner.publish_item(it, st)
    assert r["x"]["status"] == "published" and r["x"]["post_id"] == "id9"
    assert Fake.calls == []                      # found it, did not post again


def test_blocked_when_paused_or_unapproved(env):
    st, it = env
    st.set_control(paused=True, reason="test")
    assert "_blocked" in runner.publish_item(it, st)
    st.set_control(paused=False)
    it["captions"]["x"] = "changed after approval"
    assert "re-approval" in runner.publish_item(it, st)["_blocked"]
    assert Fake.calls == []


def test_dry_run_when_not_live(env, monkeypatch):
    st, it = env
    config.settings()["control"]["publishing_live"] = False
    r = runner.publish_item(it, st)
    assert r["x"]["status"] == "dry_run" and Fake.calls == []
