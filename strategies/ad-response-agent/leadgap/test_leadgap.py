"""Tests for leadgap. Run with: python3 -m unittest discover -s . -v"""

import io
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import leadgap  # noqa: E402


T0 = datetime(2026, 8, 16, 18, 0, 0, tzinfo=timezone.utc)


class TestParseWhen(unittest.TestCase):
    def test_now_and_empty(self):
        self.assertEqual(leadgap.parse_when("now", reference=T0), T0)
        self.assertEqual(leadgap.parse_when(None, reference=T0), T0)
        self.assertEqual(leadgap.parse_when("  ", reference=T0), T0)

    def test_relative_offsets(self):
        cases = {
            "-45m": T0 - timedelta(minutes=45),
            "+2h": T0 + timedelta(hours=2),
            "-3d": T0 - timedelta(days=3),
            "-90 sec": T0 - timedelta(seconds=90),
            "2hrs": T0 + timedelta(hours=2),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(leadgap.parse_when(text, reference=T0), expected)

    def test_iso_with_offset_normalises_to_utc(self):
        parsed = leadgap.parse_when("2026-08-16T08:00:00-10:00", reference=T0)
        self.assertEqual(parsed, datetime(2026, 8, 16, 18, 0, tzinfo=timezone.utc))

    def test_iso_with_space_separator(self):
        parsed = leadgap.parse_when("2026-08-16 18:00:00+00:00", reference=T0)
        self.assertEqual(parsed, T0)

    def test_naive_iso_is_read_as_local_time(self):
        parsed = leadgap.parse_when("2026-08-16T12:00:00", reference=T0)
        expected = datetime(2026, 8, 16, 12, 0).astimezone().astimezone(timezone.utc)
        self.assertEqual(parsed, expected)

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            leadgap.parse_when("sometime tuesday", reference=T0)


class TestNormalizeArgv(unittest.TestCase):
    def test_relative_time_is_glued_to_its_flag(self):
        self.assertEqual(
            leadgap.normalize_argv(["probe", "1", "--at", "-48h"]),
            ["probe", "1", "--at=-48h"],
        )

    def test_ordinary_values_are_untouched(self):
        argv = ["probe", "1", "--at", "now", "--via", "form"]
        self.assertEqual(leadgap.normalize_argv(argv), argv)

    def test_trailing_flag_does_not_crash(self):
        self.assertEqual(leadgap.normalize_argv(["probe", "1", "--at"]), ["probe", "1", "--at"])


class TestHumanize(unittest.TestCase):
    def test_scale(self):
        self.assertEqual(leadgap.humanize(None), "never")
        self.assertEqual(leadgap.humanize(4), "4 sec")
        self.assertEqual(leadgap.humanize(90), "1 min 30 sec")
        self.assertEqual(leadgap.humanize(600), "10 min")
        self.assertEqual(leadgap.humanize(3600), "1 hr")
        self.assertEqual(leadgap.humanize(3600 * 5 + 1800), "5 hr 30 min")
        self.assertEqual(leadgap.humanize(86400), "1 day")
        self.assertEqual(leadgap.humanize(86400 * 2 + 3600 * 3), "2 days 3 hr")

    def test_negative_is_flagged_not_crashed(self):
        self.assertEqual(leadgap.humanize(-5), "before the probe")


class TestGrading(unittest.TestCase):
    def probe(self, offset_hours=0):
        return {"probed_at": leadgap.iso(T0), "closed_at": None}

    def reply(self, seconds, channel="sms"):
        return {"channel": channel, "received_at": leadgap.iso(T0 + timedelta(seconds=seconds))}

    def grade(self, replies, *, ref_offset_hours=1, closed_at=None):
        probe = {"probed_at": leadgap.iso(T0), "closed_at": closed_at}
        return leadgap.grade_probe(probe, replies, reference=T0 + timedelta(hours=ref_offset_hours))

    def test_instant_tier_is_the_five_second_bar(self):
        result = self.grade([self.reply(4, "call")])
        self.assertEqual(result["grade"], "INSTANT")
        self.assertEqual(result["verdict"], "skip")
        self.assertEqual(result["first_channel"], "call")

    def test_five_seconds_exactly_is_still_instant(self):
        self.assertEqual(self.grade([self.reply(5)])["grade"], "INSTANT")

    def test_covered_tier(self):
        result = self.grade([self.reply(240)])
        self.assertEqual(result["grade"], "COVERED")
        self.assertEqual(result["verdict"], "skip")

    def test_slow_tier_is_warm(self):
        result = self.grade([self.reply(1800)])
        self.assertEqual(result["grade"], "SLOW")
        self.assertEqual(result["verdict"], "warm")

    def test_tier_boundaries_are_inclusive_upper_bounds(self):
        self.assertEqual(self.grade([self.reply(300)])["grade"], "COVERED")
        self.assertEqual(self.grade([self.reply(301)])["grade"], "SLOW")
        self.assertEqual(self.grade([self.reply(3600)], ref_offset_hours=2)["grade"], "SLOW")
        self.assertEqual(self.grade([self.reply(3601)], ref_offset_hours=2)["grade"], "COLD")

    def test_cold_tier_is_hot(self):
        result = self.grade([self.reply(7200)], ref_offset_hours=4)
        self.assertEqual(result["grade"], "COLD")
        self.assertEqual(result["verdict"], "hot")

    def test_silence_under_a_day_is_pending(self):
        result = self.grade([], ref_offset_hours=6)
        self.assertEqual(result["grade"], "PENDING")
        self.assertEqual(result["verdict"], "pending")
        self.assertIsNone(result["latency"])

    def test_silence_past_a_day_is_ghost(self):
        result = self.grade([], ref_offset_hours=30)
        self.assertEqual(result["grade"], "GHOST")
        self.assertEqual(result["verdict"], "hot")

    def test_earliest_response_wins_regardless_of_log_order(self):
        result = self.grade([self.reply(3600, "email"), self.reply(120, "sms")])
        self.assertEqual(result["grade"], "COVERED")
        self.assertEqual(result["first_channel"], "sms")
        self.assertEqual(result["channels"], ["email", "sms"])

    def test_closing_a_probe_freezes_elapsed_time(self):
        closed = leadgap.iso(T0 + timedelta(hours=48))
        result = self.grade([], ref_offset_hours=500, closed_at=closed)
        self.assertEqual(result["grade"], "GHOST")
        self.assertEqual(result["elapsed"], 48 * 3600)


class CLITestCase(unittest.TestCase):
    def setUp(self):
        handle, self.db = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        os.unlink(self.db)
        self.addCleanup(lambda: os.path.exists(self.db) and os.unlink(self.db))

    def run_cli(self, *argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = leadgap.main(["--db", self.db, *argv])
        self.assertEqual(code, 0)
        return buf.getvalue()

    def seed_ghost(self):
        self.run_cli("add", "--name", "Desert Bloom Med Spa", "--niche", "med spa",
                     "--city", "Albuquerque, NM", "--phone", "505-555-0142",
                     "--active-ads", "7")
        self.run_cli("probe", "1", "--via", "form", "--at", "-48h")
        return 1


class TestCLI(CLITestCase):
    def test_add_creates_a_prospect(self):
        out = self.run_cli("add", "--name", "Acme Roofing", "--niche", "roofing")
        self.assertIn("added #1", out)
        self.assertIn("Acme Roofing", self.run_cli("list"))

    def test_untested_prospect_is_not_callable(self):
        self.run_cli("add", "--name", "Acme Roofing")
        out = self.run_cli("list")
        self.assertIn("UNTESTED", out)
        with self.assertRaises(SystemExit):
            self.run_cli("script", "1")

    def test_probe_then_ghost_grades_hot(self):
        self.seed_ghost()
        out = self.run_cli("show", "1", "--json")
        import json
        data = json.loads(out)
        self.assertEqual(data["grade"], "GHOST")
        self.assertEqual(data["verdict"], "hot")
        self.assertIsNone(data["latency_seconds"])
        self.assertIn("nobody had called", data["evidence"])

    def test_logging_a_response_downgrades_the_verdict(self):
        self.seed_ghost()
        self.run_cli("respond", "1", "--channel", "sms", "--at", "-45h")  # 3 hr after the probe
        out = self.run_cli("show", "1", "--json")
        import json
        data = json.loads(out)
        self.assertEqual(data["grade"], "COLD")
        self.assertEqual(data["verdict"], "hot")
        self.assertEqual(data["first_channel"], "sms")
        self.assertIn("came by SMS 3 hr later", data["evidence"])

    def test_response_before_probe_is_rejected(self):
        self.seed_ghost()
        with self.assertRaises(SystemExit):
            self.run_cli("respond", "1", "--channel", "call", "--at", "-72h")

    def test_respond_without_probe_is_rejected(self):
        self.run_cli("add", "--name", "Acme Roofing")
        with self.assertRaises(SystemExit):
            self.run_cli("respond", "1", "--channel", "call")

    def test_unknown_prospect_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_cli("show", "99")

    def test_close_freezes_the_clock(self):
        self.seed_ghost()
        self.run_cli("close", "1", "--at", "-24h")
        import json
        data = json.loads(self.run_cli("show", "1", "--json"))
        # Both stamps come from separate now() reads, so allow a second of slop.
        self.assertAlmostEqual(data["elapsed_seconds"], 24 * 3600, delta=2)
        self.assertEqual(data["grade"], "GHOST")

    def test_list_sorts_hot_first_and_filters(self):
        self.seed_ghost()
        self.run_cli("add", "--name", "Fast Feet Podiatry", "--niche", "podiatry")
        self.run_cli("probe", "2", "--at", "-10m")
        self.run_cli("respond", "2", "--channel", "call", "--at", "-10m")
        out = self.run_cli("list")
        self.assertLess(out.index("Desert Bloom"), out.index("Fast Feet"))
        self.assertIn("Desert Bloom", self.run_cli("list", "--verdict", "hot"))
        self.assertNotIn("Fast Feet", self.run_cli("list", "--verdict", "hot"))
        self.assertIn("Fast Feet", self.run_cli("list", "--niche", "podi"))

    def test_report_contains_the_evidence(self):
        self.seed_ghost()
        out = self.run_cli("report", "1")
        self.assertIn("Speed-to-Lead Audit — Desert Bloom Med Spa", out)
        self.assertIn("Never responded at all", out)
        self.assertIn("7 active ads", out)
        self.assertIn("| Call | — | no response in 2 days |", out)
        self.assertIn("| SMS | — |", out)   # not "Sms"
        self.assertIn("| DM | — |", out)    # not "Dm"
        self.assertIn("ad response agent", out)

    def test_report_writes_to_a_file(self):
        self.seed_ghost()
        path = self.db + ".md"
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        self.run_cli("report", "1", "--out", path)
        with open(path, encoding="utf-8") as fh:
            self.assertIn("Speed-to-Lead Audit", fh.read())

    def test_script_carries_the_prospect_specifics(self):
        self.seed_ghost()
        out = self.run_cli("script", "1")
        self.assertIn("Desert Bloom Med Spa", out)
        self.assertIn("505-555-0142", out)
        self.assertIn("7 ads", out)
        self.assertIn("Albuquerque, NM", out)
        self.assertIn("Help me understand that", out)   # the source objection line
        self.assertIn("Recommended version", out)       # and the safer rewrite

    def test_stats_reports_hot_rate(self):
        self.seed_ghost()
        import json
        data = json.loads(self.run_cli("stats", "--json"))
        self.assertEqual(data["prospects"], 1)
        self.assertEqual(data["probed"], 1)
        self.assertEqual(data["hot_rate"], 1.0)

    def test_export_csv_and_json(self):
        self.seed_ghost()
        csv_out = self.run_cli("export", "--format", "csv")
        self.assertIn("id,name,niche", csv_out)
        self.assertIn("Desert Bloom Med Spa", csv_out)
        import json
        self.assertEqual(json.loads(self.run_cli("export", "--format", "json"))[0]["grade"], "GHOST")

    def test_multiple_probes_use_the_newest(self):
        self.seed_ghost()
        self.run_cli("probe", "1", "--via", "call", "--at", "-30m")
        import json
        data = json.loads(self.run_cli("show", "1", "--json"))
        self.assertEqual(data["grade"], "PENDING")

    def test_deleting_a_prospect_cascades(self):
        self.seed_ghost()
        conn = leadgap.connect(self.db)
        conn.execute("DELETE FROM prospects WHERE id = 1")
        conn.commit()
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM probes").fetchone()[0], 0)
        conn.close()


if __name__ == "__main__":
    unittest.main()
