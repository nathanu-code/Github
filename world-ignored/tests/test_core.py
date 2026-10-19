import copy

import numpy as np
import pytest

from wi import captions, models
from wi.edit import banners as bn
from wi.edit.analyze import Analysis
from wi.edit.layout import best_placement, safe_rect
from wi.edit.reframe import onscreen_maps, plan_crop
from wi.store import Store, normalize_url


# ---------- banners ----------------------------------------------------------------------------
@pytest.mark.parametrize("headline", [
    "TWO-STORY HOUSE COLLAPSES INTO FLOODWATERS",
    "FLASH FLOOD SWEEPS DOZENS OF CARS THROUGH CITY STREETS",
    "LANDSLIDE",
])
def test_banner_text_fits_with_padding(headline):
    b = bn.render_banner(bn.opening_blocks(headline, "", "SAKARYA, TÜRKIYE  |  OCT 15, 2026"), 1080, 930)
    assert bn.check_banner(b) == []
    assert all(0 < l and r < b.width and 0 < t and bt < b.height for l, t, r, bt in b.text_boxes)
    assert b.lines[-1] == "SAKARYA, TÜRKIYE | OCT 15, 2026" or "TÜRKIYE" in b.lines[-1]


def test_overlong_headline_is_refused():
    with pytest.raises(bn.BannerOverflow):
        bn.render_banner(bn.opening_blocks("FLASH FLOOD SWEEPS DOZENS OF CARS THROUGH CITY STREETS AFTER "
                                           "RECORD RAINFALL OVERNIGHT IN THE REGION", "", "X | Y"), 1080, 930)


def test_closing_banner_fits_narrow():
    b = bn.render_banner(bn.closing_blocks("MOVING FLOODWATER CAN SWEEP CARS AWAY", "AVOID FLOODED ROADS"), 1080, 778)
    assert bn.check_banner(b) == []


# ---------- reframing and placement --------------------------------------------------------------
def _analysis(subject_xy, src=(1920, 1080), n=30):
    mh, mw = int(96 * src[1] / src[0]), 96
    maps = np.full((n, mh, mw), 1e-4, np.float32)
    for i in range(n):
        x, y = subject_xy(i) if callable(subject_xy) else subject_xy
        cx, cy = int(x * mw), int(y * mh)
        maps[i, max(0, cy - 4):cy + 4, max(0, cx - 4):cx + 4] += 1.0
        maps[i] /= maps[i].sum()
    return Analysis(np.arange(n) / 3.0, maps, src)


def test_crop_follows_off_centre_subject():
    an = _analysis((0.85, 0.5))
    plan = plan_crop(an, (1080, 1920))
    x0, _, w, h = plan.window_at(1.0)
    assert abs(w / h - 1080 / 1920) < 1e-3          # exact aspect, no distortion
    assert x0 <= 0.85 * 1920 <= x0 + w               # subject inside crop
    assert plan.coverage.mean() > 0.9


def test_crop_tracks_moving_subject():
    an = _analysis(lambda i: (0.15 + 0.7 * i / 29, 0.5), n=30)
    plan = plan_crop(an, (1080, 1920))
    assert plan.mode == "tracking"
    assert plan.coverage.mean() > 0.75
    assert np.all(np.abs(np.diff(plan.centers)) < 0.08 * 1920)  # no jumps


def test_wide_subject_spread_is_flagged():
    an = _analysis(lambda i: (0.05 if i % 2 else 0.95, 0.5))
    plan = plan_crop(an, (1080, 1920))
    assert plan.coverage_stats()["mean"] < 0.62      # QC will send this to manual review


def test_banner_avoids_subject_at_top():
    an = _analysis((0.5, 0.25), src=(1080, 1920))
    plan = plan_crop(an, (1080, 1920))
    onscreen = onscreen_maps(an, plan, (54, 96))
    zone = {"top": 0.11, "bottom": 0.22, "side": 0.07, "side_lower": 0.14, "lower_from": 0.45}
    _, p = best_placement(onscreen, an.times, (1080, 1920), [(330, False), (380, True)], zone, (0, 4))
    subject_y = 0.25 * 1920
    assert not (p.y <= subject_y <= p.y + p.h)
    assert p.overlap < 0.05


def test_safe_rect_is_centred():
    zone = {"top": 0.11, "bottom": 0.22, "side": 0.07, "side_lower": 0.14, "lower_from": 0.45}
    x0, _, x1, y1 = safe_rect((1080, 1920), zone)
    assert x0 == 1080 - x1 and y1 <= 0.45 * 1920 + 1


# ---------- workflow gates ------------------------------------------------------------------------
def _cleared_item():
    it = models.new_item(event_type="flood", title="House collapses into floodwaters", country="Türkiye",
                         location="Sakarya", event_date="2026-10-15", footage_url="https://x.com/a/status/1?s=20")
    it["event"]["sources"] = [{"name": "Anadolu Agency", "url": "https://example.org/aa"}]
    it["event"]["summary"] = "A two-story house collapsed after a stream overflowed and undermined its foundation."
    it["verification"].update(event_verified=True, footage_verified=True)
    it["rights"].update(status="cleared", holder="Jane Filmer", license_type="written_permission",
                        evidence_ref="drive:abc123", permitted_platforms=["tiktok", "x"], attribution="Jane Filmer")
    it["footage"]["raw_path"] = "/tmp/raw.mp4"
    return it


def test_credit_only_never_clears_rights():
    it = _cleared_item()
    it["rights"]["license_type"] = "credit_only"
    it["status"] = models.FOOTAGE_VERIFIED
    with pytest.raises(models.GateError, match="does not clear"):
        models.transition(it, models.RIGHTS_CLEARED, actor="t")


def test_cannot_skip_verification():
    it = _cleared_item()
    with pytest.raises(models.GateError):
        models.transition(it, models.RIGHTS_CLEARED, actor="t")   # UNVERIFIED -> RIGHTS_CLEARED not allowed


def test_full_path_and_reapproval_on_change():
    it = _cleared_item()
    for st in (models.EVENT_VERIFIED, models.FOOTAGE_VERIFIED, models.RIGHTS_CLEARED, models.READY_FOR_EDITING):
        models.transition(it, st, actor="t")
    it["edit"]["outputs"] = {"v9x16": {"sha256": "aaa", "qc": {"passed": True}}}
    models.transition(it, models.EDITED, actor="t")
    with pytest.raises(models.GateError, match="captions"):
        models.transition(it, models.READY_FOR_APPROVAL, actor="t")
    it["captions"] = {"x": "hello"}
    models.transition(it, models.READY_FOR_APPROVAL, actor="t")
    with pytest.raises(models.GateError):
        models.transition(it, models.APPROVED, actor="t")          # nobody approved yet
    it["approval"].update(status="approved", content_hash=models.content_hash(it), platforms=["x"])
    models.transition(it, models.APPROVED, actor="t")
    ok, _ = models.approval_valid(it, ["x"])
    assert ok
    assert not models.approval_valid(it, ["tiktok"])[0]           # platform not approved
    it["captions"]["x"] = "edited caption"
    assert models.invalidate_approval_if_changed(it)
    assert it["status"] == models.READY_FOR_APPROVAL and it["approval"]["status"] == "stale"


# ---------- store / dedupe ------------------------------------------------------------------------
def test_url_normalisation():
    assert normalize_url("https://twitter.com/a/status/1?s=20&t=x") == normalize_url("https://x.com/a/status/1")
    assert normalize_url("https://youtu.be/abc") == "youtube.com/watch?v=abc"


def test_store_rejects_duplicates(tmp_path):
    st = Store(tmp_path)
    a = _cleared_item()
    st.add(a)
    b = copy.deepcopy(a)
    b["id"] += "-2"
    with pytest.raises(ValueError, match="duplicate"):
        st.add(b)
    assert "Video ID" in st.to_csv()


# ---------- captions ----------------------------------------------------------------------------
def test_captions_use_only_verified_fields():
    it = _cleared_item()
    caps = captions.build(it)
    assert "HOUSE COLLAPSES INTO FLOODWATERS" in caps["instagram_reels"]
    assert "📍 Sakarya, Türkiye" in caps["instagram_reels"]
    assert "October 15, 2026" in caps["instagram_reels"]
    assert "🎥 Jane Filmer" in caps["instagram_reels"]
    assert caps["instagram_reels"].rstrip().endswith("#WorldUnignored")
    assert "Fact source" in caps["instagram_reels"]
    assert len(caps["threads"]) <= 500 and captions._x_len(caps["x"]) <= 280
    assert "http" not in caps["x"]
    assert len(caps["youtube_title"]) <= 100


def test_captions_refuse_unsourced_casualty_claims():
    it = _cleared_item()
    it["event"]["summary"] = "At least 12 people died when the house collapsed."
    with pytest.raises(captions.CaptionError):
        captions.build(it)


def test_captions_refuse_missing_credit():
    it = _cleared_item()
    it["rights"]["attribution"] = ""
    with pytest.raises(captions.CaptionError, match="attribution"):
        captions.build(it)


def test_location_line():
    it = _cleared_item()
    assert captions.location_line(it) == "SAKARYA, TÜRKIYE  |  OCT 15, 2026"


def test_slack_outbox_dedupes_queued_messages(tmp_path, monkeypatch):
    from wi import config, slack
    monkeypatch.setattr(config, "STATE_DIR", tmp_path)
    monkeypatch.setattr(slack, "OUTBOX", tmp_path / "outbox")
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    a = slack.send("report", kind="daily_report", dedupe_key="daily_report:2026-10-19")
    b = slack.send("report", kind="daily_report", dedupe_key="daily_report:2026-10-19")
    assert a["status"] == "queued" and b["status"] == "already_queued"
    assert len(list((tmp_path / "outbox").glob("*.json"))) == 1
    assert "[redacted]" in slack.scrub("token xoxb-123-abc")


def test_old_or_impactless_footage_is_blocked():
    from wi.research import scoring
    base = {"title": "t", "type": "flood", "country": "X", "location": "Y", "footage_url": "u",
            "scores": {"human_impact": 0.9, "disaster_activity_on_camera": 0.9, "newsworthiness": 0.8,
                       "verification_confidence": 0.9, "video_quality": 0.8}, "rights_outlook": "contactable"}
    old = scoring.score({**base, "event_date": "2026-01-01", "filmed_date": "unconfirmed"}, [])
    assert any("too old" in b for b in old["blockers"])
    weak = scoring.score({**base, "event_date": "2026-10-18",
                          "scores": {**base["scores"], "disaster_activity_on_camera": 0.1}}, [])
    assert any("impact" in b for b in weak["blockers"])
