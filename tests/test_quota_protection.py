import os
import json
import tempfile
import unittest
import urllib.error
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pipeline.synthesizer import QuotaManager, QuotaCorruptionError, NewsSynthesizer, MYT_TZ
from collectors.base import RawArticle


class TestGeminiQuotaProtection(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.state_file = os.path.join(self.test_dir.name, "test_quota_state.json")
        self.config = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "timezone": "Asia/Kuala_Lumpur",
                "fail_closed": True,
                "state_file": self.state_file,
                "execution_mode": "MOCK_TEST"
            }
        }

    def tearDown(self):
        try:
            self.test_dir.cleanup()
        except Exception:
            pass

    def _create_valid_remote_state(self, reserved_count=0, date_str=None):
        today_str = date_str or datetime.now(MYT_TZ).strftime("%Y-%m-%d")
        return {
            "schema_version": "1.0",
            "timezone": "Asia/Kuala_Lumpur",
            "date": today_str,
            "reserved_count": reserved_count,
            "daily_limit": 5,
            "reservations": [],
            "last_updated": datetime.now(MYT_TZ).isoformat(),
            "status": "IDLE"
        }

    # 1. CI mode requires remote reservation
    def test_01_ci_mode_requires_remote_reservation(self):
        cfg_ci = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": self.state_file
            }
        }
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            qm = QuotaManager(cfg_ci, state_file_override=self.state_file, execution_mode_override=None)
            self.assertEqual(qm.execution_mode, "CI_PRODUCTION")

            valid_remote = self._create_valid_remote_state(0)
            with patch.object(qm, "fetch_authoritative_remote_state", return_value=(valid_remote, "REMOTE_VALID")):
                with patch.object(qm, "persist_remote_reservation", return_value=True) as mock_push:
                    slot = qm.reserve_slot("gemini-3.5-flash-lite")
                    self.assertIsNotNone(slot)
                    mock_push.assert_called_once()

    # 2. Missing remote state fails closed (Condition B)
    def test_02_missing_remote_state_fails_closed(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="CI_PRODUCTION")
        # Simulate origin/main:config/gemini_quota_state.json not found
        with patch("subprocess.run") as mock_sub:
            # git branch -> main
            # git fetch -> returncode 0
            # git show -> returncode 1 (file missing)
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stderr="fatal: path not found", returncode=1)
            ]
            slot = qm.reserve_slot("gemini-3.5-flash-lite")
            self.assertIsNone(slot, "Missing remote state on origin/main must fail closed to Track B")

    # 3. Remote fetch failure fails closed (Condition C)
    def test_03_remote_fetch_failure_fails_closed(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="CI_PRODUCTION")
        with patch("subprocess.run") as mock_sub:
            # git branch -> main
            # git fetch -> returncode 128 (network error / fetch failed)
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stderr="fatal: could not read Username", returncode=128)
            ]
            slot = qm.reserve_slot("gemini-3.5-flash-lite")
            self.assertIsNone(slot, "Remote fetch failure must fail closed to Track B")

    # 4. Corrupted remote state fails closed (Condition D)
    def test_04_corrupted_remote_state_fails_closed(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="CI_PRODUCTION")
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout="{corrupt_json: true", returncode=0)
            ]
            slot = qm.reserve_slot("gemini-3.5-flash-lite")
            self.assertIsNone(slot, "Corrupted remote state must fail closed")

    # 5. Local-only state cannot authorize production Gemini requests
    def test_05_local_only_state_cannot_authorize_gemini(self):
        # Force LOCAL_OFFLINE mode
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="LOCAL_OFFLINE")
        self.assertEqual(qm.execution_mode, "LOCAL_OFFLINE")
        slot = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNone(slot, "Local offline execution must fail closed without remote reservation")

    # 6. Successful remote reservation precedes HTTP
    def test_06_successful_remote_reservation_precedes_http(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        execution_order = []

        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        def mock_push(state):
            execution_order.append("REMOTE_PUSH")
            return True

        qm.persist_remote_reservation = mock_push

        def mock_urlopen(*args, **kwargs):
            execution_order.append("HTTP_CALL")
            raise urllib.error.HTTPError("https://x", 500, "Error", {}, None)

        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            synth.synthesize_track_a_gemini("test_key", "2026-11-08", test_articles)

        self.assertEqual(execution_order, ["REMOTE_PUSH", "HTTP_CALL"], "Remote reservation must precede HTTP call")

    # 7. Failed remote push prevents HTTP
    def test_07_failed_remote_push_prevents_http(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
        qm.persist_remote_reservation = MagicMock(return_value=False)

        with patch("urllib.request.urlopen") as mock_url:
            res = synth.synthesize_track_a_gemini("test_key", "2026-11-08", test_articles)
            self.assertIsNone(res)
            mock_url.assert_not_called()

    # 8. Daily limit of 5 is enforced
    def test_08_daily_limit_five_enforced(self):
        valid_remote = self._create_valid_remote_state(5)
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
        slot = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNone(slot, "When remote reserved_count is 5, further reservations must be rejected")

    # 9. Per-run limit of 1 is enforced
    def test_09_per_run_limit_one_enforced(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
        qm.persist_remote_reservation = MagicMock(return_value=True)

        slot1 = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNotNone(slot1)

        slot2 = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNone(slot2, "Second request in same run must be rejected")

    # 10. HTTP 429 consumes quota and selects Track B
    def test_10_http_429_consumes_quota_and_selects_track_b(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
        qm.persist_remote_reservation = MagicMock(return_value=True)

        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test Article", url="https://x.com", source="Src", category="sabah")]

        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("https://x", 429, "Too Many Requests", {}, None)):
            res = synth.synthesize("2026-11-08", test_articles, api_key="test_key")
            self.assertIsNotNone(res)
            self.assertTrue(len(res) > 0)
            self.assertIn("art_sabah_1", res[0]["id"])

        state = qm.load_and_validate_local_state()
        self.assertEqual(state["reserved_count"], 1)
        self.assertEqual(state["reservations"][0]["status"], "FAILED_HTTP_429")

    # 11. HTTP 401/403/404 consume quota and select Track B
    def test_11_http_fatal_codes_consume_quota_and_select_track_b(self):
        for code in [401, 403, 404]:
            qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
            valid_remote = self._create_valid_remote_state(0)
            qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
            qm.persist_remote_reservation = MagicMock(return_value=True)

            synth = NewsSynthesizer(self.config, quota_mgr=qm)
            test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("https://x", code, f"Error {code}", {}, None)):
                res = synth.synthesize("2026-11-08", test_articles, api_key="test_key")
                self.assertIsNotNone(res)

            state = qm.load_and_validate_local_state()
            self.assertEqual(state["reserved_count"], 1)
            self.assertEqual(state["reservations"][0]["status"], f"FAILED_HTTP_{code}")

    # 12. Timeout consumes quota and selects Track B
    def test_12_timeout_consumes_quota_and_selects_track_b(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
        qm.persist_remote_reservation = MagicMock(return_value=True)

        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timed out")):
            res = synth.synthesize("2026-11-08", test_articles, api_key="test_key")
            self.assertIsNotNone(res)

        state = qm.load_and_validate_local_state()
        self.assertEqual(state["reserved_count"], 1)
        self.assertEqual(state["reservations"][0]["status"], "FAILED_TIMEOUT_OR_NETWORK")

    # 13. Track B works completely without credentials
    def test_13_track_b_works_without_credentials(self):
        synth = NewsSynthesizer(self.config, quota_mgr=QuotaManager(self.config, state_file_override=self.state_file))
        test_articles = [
            RawArticle(title="沙巴基建重大突破", url="https://x.com/1", source="诗华日报", category="sabah", snippet="全州水利管网全面更新"),
            RawArticle(title="山打根市民中心开放", url="https://x.com/2", source="星洲日报", category="sabah", snippet="市民热烈参与活动")
        ]
        with patch("urllib.request.urlopen") as mock_url:
            res = synth.synthesize("2026-11-08", test_articles, api_key=None)
            self.assertEqual(len(res), 2)
            mock_url.assert_not_called()

    # 14. First-time initialization (Condition A) authorized
    def test_14_first_time_init_condition_a_authorized(self):
        cfg = dict(self.config)
        cfg["gemini_quota"] = dict(self.config["gemini_quota"])
        cfg["gemini_quota"]["allow_first_time_init"] = True

        qm = QuotaManager(cfg, state_file_override=self.state_file, execution_mode_override="CI_PRODUCTION")
        with patch("subprocess.run") as mock_sub:
            # git branch -> main
            # git fetch -> returncode 0
            # git show -> returncode 1 (file missing, but allow_first_time_init is True)
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stderr="fatal: path not found", returncode=1)
            ]
            state, cond = qm.fetch_authoritative_remote_state()
            self.assertEqual(cond, "CONDITION_A_FIRST_TIME_INIT")
            self.assertIsNotNone(state)
            self.assertEqual(state["reserved_count"], 0)

    # 15. New Malaysia day resets remote counter
    def test_15_new_malaysia_day_resets_counter(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        yesterday_remote = self._create_valid_remote_state(5, date_str="2026-11-07")
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout=json.dumps(yesterday_remote), returncode=0)
            ]
            state, cond = qm.fetch_authoritative_remote_state()
            self.assertEqual(cond, "REMOTE_VALID")
            today_str = datetime.now(MYT_TZ).strftime("%Y-%m-%d")
            self.assertEqual(state["date"], today_str)
            self.assertEqual(state["reserved_count"], 0)

    # 16. Empty index permits reservation staging
    def test_16_empty_index_permits_reservation_staging(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file)
        state = self._create_valid_remote_state(0)
        norm_path = self.state_file.replace("\\", "/").lstrip("./")

        with patch("subprocess.run") as mock_sub:
            # 1. pre-check -> empty
            # 2. git add -> 0
            # 3. post-check -> exact file
            # 4. git commit -> 0
            # 5. git push -> 0
            mock_sub.side_effect = [
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout=f"{norm_path}\n", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout="", returncode=0),
            ]
            success = qm.persist_remote_reservation(state)
            self.assertTrue(success, "Clean empty index must permit reservation persistence")

    # 17. Pre-staged unrelated file blocks reservation
    def test_17_pre_staged_unrelated_file_blocks_reservation(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file)
        state = self._create_valid_remote_state(0)

        with patch("subprocess.run") as mock_sub:
            # pre-check detects unrelated staged file
            mock_sub.side_effect = [
                MagicMock(stdout="index.html\n", returncode=0)
            ]
            success = qm.persist_remote_reservation(state)
            self.assertFalse(success, "Pre-staged unrelated file must block reservation")
            # Must NOT call git add, commit, or push
            self.assertEqual(mock_sub.call_count, 1)

    # 18. Pre-staged quota file also blocks reservation under strict empty-index rule
    def test_18_pre_staged_quota_file_blocks_reservation(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file)
        state = self._create_valid_remote_state(0)
        norm_path = self.state_file.replace("\\", "/").lstrip("./")

        with patch("subprocess.run") as mock_sub:
            # pre-check detects file already in index
            mock_sub.side_effect = [
                MagicMock(stdout=f"{norm_path}\n", returncode=0)
            ]
            success = qm.persist_remote_reservation(state)
            self.assertFalse(success, "Pre-staged quota file must also abort under strict empty-index rule")
            self.assertEqual(mock_sub.call_count, 1)

    # 19. Unexpected staged file after git add blocks commit
    def test_19_unexpected_staged_file_after_add_blocks_commit(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file)
        state = self._create_valid_remote_state(0)
        norm_path = self.state_file.replace("\\", "/").lstrip("./")

        with patch("subprocess.run") as mock_sub:
            # 1. pre-check -> empty
            # 2. git add -> 0
            # 3. post-check -> unexpected file appeared!
            mock_sub.side_effect = [
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout=f"{norm_path}\nnews_data.json\n", returncode=0),
            ]
            success = qm.persist_remote_reservation(state)
            self.assertFalse(success, "Post-staging index mismatch must abort before commit")
            self.assertEqual(mock_sub.call_count, 3) # Stopped before commit

    # 20. Failed index check sends zero HTTP requests
    def test_20_failed_index_check_sends_zero_http(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        # Pre-check fails
        with patch("subprocess.run", return_value=MagicMock(stdout="unrelated.py\n", returncode=0)):
            with patch("urllib.request.urlopen") as mock_url:
                res = synth.synthesize_track_a_gemini("test_key", "2026-11-08", test_articles)
                self.assertIsNone(res)
                mock_url.assert_not_called()

    # 21. Commit failure sends zero HTTP requests
    def test_21_commit_failure_sends_zero_http(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        norm_path = self.state_file.replace("\\", "/").lstrip("./")
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="", returncode=0), # pre-check
                MagicMock(stdout="", returncode=0), # add
                MagicMock(stdout=f"{norm_path}\n", returncode=0), # post-check
                MagicMock(stderr="error: unable to commit", returncode=1), # commit fails!
            ]
            with patch("urllib.request.urlopen") as mock_url:
                res = synth.synthesize_track_a_gemini("test_key", "2026-11-08", test_articles)
                self.assertIsNone(res)
                mock_url.assert_not_called()

    # 22. Push failure sends zero HTTP requests
    def test_22_push_failure_sends_zero_http(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        norm_path = self.state_file.replace("\\", "/").lstrip("./")
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="", returncode=0), # pre-check
                MagicMock(stdout="", returncode=0), # add
                MagicMock(stdout=f"{norm_path}\n", returncode=0), # post-check
                MagicMock(stdout="", returncode=0), # commit
                MagicMock(stderr="error: failed to push", returncode=1), # push fails!
            ]
            with patch("urllib.request.urlopen") as mock_url:
                res = synth.synthesize_track_a_gemini("test_key", "2026-11-08", test_articles)
                self.assertIsNone(res)
                mock_url.assert_not_called()

    # 23. Successful isolated reservation permits exactly one HTTP request
    def test_23_successful_isolated_reservation_permits_one_http(self):
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        valid_remote = self._create_valid_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        norm_path = self.state_file.replace("\\", "/").lstrip("./")
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps([{
                            "category": "sabah",
                            "title": f"Test Title {i}",
                            "titleBM": f"Tajuk {i}",
                            "detail": f"Detail {i}",
                            "detailBM": f"DetailBM {i}",
                            "sources": ["Src"],
                            "url": "https://x.com"
                        } for i in range(12)])
                    }]
                }
            }]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="", returncode=0), # pre-check
                MagicMock(stdout="", returncode=0), # add
                MagicMock(stdout=f"{norm_path}\n", returncode=0), # post-check
                MagicMock(stdout="", returncode=0), # commit
                MagicMock(stdout="", returncode=0), # push
            ]
            with patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
                res = synth.synthesize_track_a_gemini("test_key", "2026-11-08", test_articles)
                self.assertIsNotNone(res)
                self.assertEqual(len(res), 12)
                self.assertEqual(mock_url.call_count, 1)

    # 24. Existing unstaged user modifications remain untouched
    def test_24_existing_unstaged_user_modifications_untouched(self):
        # Verify that persist_remote_reservation never calls checkout, clean, reset, or stash
        qm = QuotaManager(self.config, state_file_override=self.state_file)
        state = self._create_valid_remote_state(0)
        norm_path = self.state_file.replace("\\", "/").lstrip("./")

        recorded_commands = []
        def intercept_sub(cmd, *args, **kwargs):
            recorded_commands.append(cmd)
            if cmd == ["git", "diff", "--cached", "--name-only"]:
                if len(recorded_commands) == 1:
                    return MagicMock(stdout="", returncode=0)
                else:
                    return MagicMock(stdout=f"{norm_path}\n", returncode=0)
            return MagicMock(stdout="", returncode=0)

        with patch("subprocess.run", side_effect=intercept_sub):
            qm.persist_remote_reservation(state)

        for cmd in recorded_commands:
            self.assertNotIn("clean", cmd)
            self.assertNotIn("reset", cmd)
            self.assertNotIn("stash", cmd)
            self.assertNotIn("checkout", cmd)
            self.assertNotIn("--force", cmd)


if __name__ == "__main__":
    unittest.main()
