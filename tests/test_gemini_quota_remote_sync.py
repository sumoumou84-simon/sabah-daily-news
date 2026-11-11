#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_gemini_quota_remote_sync.py

Comprehensive tests for Gemini Quota Reservation Remote Synchronization:
1. HTTP 200 -> COMPLETED synchronized to remote ledger.
2. HTTP 503 -> FAILED_HTTP_503 synchronized to remote ledger.
3. HTTP 429 -> FAILED_HTTP_429 synchronized to remote ledger.
4. Timeout -> FAILED_TIMEOUT_OR_NETWORK synchronized to remote ledger.
5. Remote sync failure -> retains RESERVED on both local and remote (no fake success).
6. Daily count never refunded across all statuses (strictly monotonic count).
7. Maximum 1 Gemini request per pipeline run strictly enforced.
8. Daily quota limit (5) strictly enforced.
9. Git isolation invariants: only quota state file staged, zero clean/reset/stash/checkout.
10. Zero real Gemini API calls made, zero quota consumed.
"""

import os
import sys
import json
import uuid
import unittest
import urllib.error
from unittest.mock import MagicMock, patch
import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.synthesizer import QuotaManager, NewsSynthesizer
from collectors import RawArticle


class TestGeminiQuotaRemoteSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.test_dir, "config", "gemini_quota_state.json")
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        self.config = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "timezone": "Asia/Kuala_Lumpur",
                "fail_closed": True,
                "state_file": self.state_file,
                "execution_mode": "MOCK_TEST"
            },
            "system": {
                "min_headlines_threshold": 1
            }
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_initial_remote_state(self, count=0):
        return {
            "schema_version": "1.0",
            "timezone": "Asia/Kuala_Lumpur",
            "date": "2026-11-11",
            "reserved_count": count,
            "daily_limit": 5,
            "reservations": [],
            "last_updated": "2026-11-11T05:00:00+08:00",
            "status": "IDLE",
            "initialization_mode": "AUTHORIZED_PHASE_N4"
        }

    def test_01_http_200_syncs_completed_remotely(self):
        """Simulate HTTP 200: verify finalize_slot durably syncs COMPLETED remotely."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        persisted_commits = []

        def mock_persist_reservation(state, commit_message=None):
            persisted_commits.append(("RESERVATION", json.loads(json.dumps(state)), commit_message))
            return True

        def mock_persist_finalization(state, res_id, status):
            msg = f"ci: finalize gemini quota reservation {res_id} ({status}) [skip ci]"
            persisted_commits.append(("FINALIZATION", json.loads(json.dumps(state)), msg))
            return True

        qm.persist_remote_reservation = mock_persist_reservation
        qm.persist_remote_finalization = mock_persist_finalization

        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        # Mock HTTP 200 response
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps([{
                            "category": "sabah",
                            "title": "Sabah Test Title",
                            "titleBM": "Tajuk Ujian Sabah",
                            "detail": "Sabah test detail substantif",
                            "detailBM": "Butiran ujian Sabah",
                            "source": "Src",
                            "source_url": "https://x.com"
                        }])
                    }]
                },
                "finishReason": "STOP"
            }],
            "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 200, "totalTokenCount": 300}
        }).encode("utf-8")

        orig_open = open
        def safe_open(file, *args, **kwargs):
            file_str = str(file)
            if "reports" in file_str and any(m in args or kwargs.get("mode", "") for m in ["w", "a"]):
                file_str = os.path.join(self.test_dir, os.path.basename(file_str))
            return orig_open(file_str, *args, **kwargs)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("builtins.open", side_effect=safe_open):
            res = synth.synthesize_track_a_single_batch("test_key", "2026-11-11", test_articles)
            self.assertIsNotNone(res)
            self.assertEqual(len(res), 1)

        # Verify remote commits: exactly 1 reservation then 1 finalization
        self.assertEqual(len(persisted_commits), 2)
        res_step, res_state, res_msg = persisted_commits[0]
        self.assertEqual(res_step, "RESERVATION")
        self.assertEqual(res_state["status"], "RESERVED")
        self.assertEqual(res_state["reserved_count"], 1)

        fin_step, fin_state, fin_msg = persisted_commits[1]
        self.assertEqual(fin_step, "FINALIZATION")
        self.assertEqual(fin_state["status"], "COMPLETED")
        self.assertEqual(fin_state["reservations"][0]["status"], "COMPLETED")
        self.assertEqual(fin_state["reserved_count"], 1)  # Never decremented!
        self.assertIn("COMPLETED", fin_msg)

        # Verify local file matches remote finalization
        local_state = qm.load_and_validate_local_state()
        self.assertEqual(local_state["status"], "COMPLETED")
        self.assertEqual(local_state["reservations"][0]["status"], "COMPLETED")
        self.assertEqual(local_state["reserved_count"], 1)

    def test_02_http_503_syncs_failed_http_503_remotely(self):
        """Simulate HTTP 503: verify finalize_slot syncs FAILED_HTTP_503 remotely."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        persisted_commits = []

        def mock_persist_reservation(state, commit_message=None):
            persisted_commits.append(("RESERVATION", json.loads(json.dumps(state)), commit_message))
            return True

        def mock_persist_finalization(state, res_id, status):
            msg = f"ci: finalize gemini quota reservation {res_id} ({status}) [skip ci]"
            persisted_commits.append(("FINALIZATION", json.loads(json.dumps(state)), msg))
            return True

        qm.persist_remote_reservation = mock_persist_reservation
        qm.persist_remote_finalization = mock_persist_finalization

        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        # Mock HTTP 503 error
        http_err = urllib.error.HTTPError("https://api.gemini", 503, "Service Unavailable", {}, None)
        with patch("urllib.request.urlopen", side_effect=http_err):
            res = synth.synthesize_track_a_single_batch("test_key", "2026-11-11", test_articles)
            self.assertIsNone(res)

        # Verify remote finalization occurred with FAILED_HTTP_503
        self.assertEqual(len(persisted_commits), 2)
        fin_step, fin_state, fin_msg = persisted_commits[1]
        self.assertEqual(fin_step, "FINALIZATION")
        self.assertEqual(fin_state["status"], "FAILED_HTTP_503")
        self.assertEqual(fin_state["reservations"][0]["status"], "FAILED_HTTP_503")
        self.assertEqual(fin_state["reserved_count"], 1)  # Strict: no refunds!
        self.assertIn("FAILED_HTTP_503", fin_msg)

        # Local state is consistent with remote
        local_state = qm.load_and_validate_local_state()
        self.assertEqual(local_state["status"], "FAILED_HTTP_503")
        self.assertEqual(local_state["reservations"][0]["status"], "FAILED_HTTP_503")
        self.assertEqual(local_state["reserved_count"], 1)

    def test_03_http_429_syncs_failed_http_429_remotely(self):
        """Simulate HTTP 429: verify finalize_slot syncs FAILED_HTTP_429 remotely."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        persisted_commits = []

        def mock_persist_reservation(state, commit_message=None):
            persisted_commits.append(("RESERVATION", json.loads(json.dumps(state)), commit_message))
            return True

        def mock_persist_finalization(state, res_id, status):
            msg = f"ci: finalize gemini quota reservation {res_id} ({status}) [skip ci]"
            persisted_commits.append(("FINALIZATION", json.loads(json.dumps(state)), msg))
            return True

        qm.persist_remote_reservation = mock_persist_reservation
        qm.persist_remote_finalization = mock_persist_finalization

        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        http_err = urllib.error.HTTPError("https://api.gemini", 429, "Too Many Requests", {}, None)
        with patch("urllib.request.urlopen", side_effect=http_err):
            res = synth.synthesize_track_a_single_batch("test_key", "2026-11-11", test_articles)
            self.assertIsNone(res)

        self.assertEqual(len(persisted_commits), 2)
        fin_step, fin_state, fin_msg = persisted_commits[1]
        self.assertEqual(fin_state["status"], "FAILED_HTTP_429")
        self.assertEqual(fin_state["reservations"][0]["status"], "FAILED_HTTP_429")
        self.assertEqual(fin_state["reserved_count"], 1)
        self.assertIn("FAILED_HTTP_429", fin_msg)

    def test_04_timeout_syncs_failed_timeout_remotely(self):
        """Simulate Timeout: verify finalize_slot syncs FAILED_TIMEOUT_OR_NETWORK remotely."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        persisted_commits = []

        def mock_persist_reservation(state, commit_message=None):
            persisted_commits.append(("RESERVATION", json.loads(json.dumps(state)), commit_message))
            return True

        def mock_persist_finalization(state, res_id, status):
            msg = f"ci: finalize gemini quota reservation {res_id} ({status}) [skip ci]"
            persisted_commits.append(("FINALIZATION", json.loads(json.dumps(state)), msg))
            return True

        qm.persist_remote_reservation = mock_persist_reservation
        qm.persist_remote_finalization = mock_persist_finalization

        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Test", url="https://x.com", source="Src", category="sabah")]

        timeout_err = urllib.error.URLError("Connection timed out")
        with patch("urllib.request.urlopen", side_effect=timeout_err):
            res = synth.synthesize_track_a_single_batch("test_key", "2026-11-11", test_articles)
            self.assertIsNone(res)

        self.assertEqual(len(persisted_commits), 2)
        fin_step, fin_state, fin_msg = persisted_commits[1]
        self.assertEqual(fin_state["status"], "FAILED_TIMEOUT_OR_NETWORK")
        self.assertEqual(fin_state["reservations"][0]["status"], "FAILED_TIMEOUT_OR_NETWORK")
        self.assertEqual(fin_state["reserved_count"], 1)
        self.assertIn("FAILED_TIMEOUT_OR_NETWORK", fin_msg)

    def test_05_remote_sync_failure_retains_reserved(self):
        """If remote synchronization fails, local state retains RESERVED and does NOT pretend success."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        # Reservation push succeeds
        qm.persist_remote_reservation = MagicMock(return_value=True)

        # Finalization remote push FAILS (simulating network cut or git push reject)
        qm.persist_remote_finalization = MagicMock(return_value=False)

        res_record = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNotNone(res_record)
        res_id = res_record["reservation_id"]

        # Call finalize_slot with FAILED_HTTP_503
        sync_ok = qm.finalize_slot(res_id, "FAILED_HTTP_503")
        self.assertFalse(sync_ok, "Must return False when remote sync fails")

        # Crucial invariant: State must retain RESERVED, NOT fake FAILED_HTTP_503 or COMPLETED!
        local_state = qm.load_and_validate_local_state()
        self.assertEqual(local_state["status"], "RESERVED")
        self.assertEqual(local_state["reservations"][0]["status"], "RESERVED")
        self.assertEqual(local_state["reserved_count"], 1)  # Never decremented!

    def test_06_daily_count_never_refunded_across_all_statuses(self):
        """Verify that reserved_count is strictly monotonic and never refunded."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(2)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
        qm.persist_remote_reservation = MagicMock(return_value=True)
        qm.persist_remote_finalization = MagicMock(return_value=True)

        res_record = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertEqual(res_record["status"], "RESERVED")
        res_id = res_record["reservation_id"]

        state_after_reserve = qm.load_and_validate_local_state()
        self.assertEqual(state_after_reserve["reserved_count"], 3)

        for test_status in ["COMPLETED", "FAILED_HTTP_503", "FAILED_HTTP_429", "FAILED_TIMEOUT_OR_NETWORK", "FAILED_TRUNCATED", "FAILED_UNEXPECTED"]:
            qm.finalize_slot(res_id, test_status)
            state = qm.load_and_validate_local_state()
            self.assertEqual(state["reserved_count"], 3, f"Count refunded for status {test_status}!")

    def test_07_per_run_limit_strictly_enforced_single_call(self):
        """Verify that only 1 Gemini request is allowed per pipeline run."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))
        qm.persist_remote_reservation = MagicMock(return_value=True)
        qm.persist_remote_finalization = MagicMock(return_value=True)

        # First reservation succeeds
        res1 = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNotNone(res1)
        self.assertEqual(qm.run_requests_count, 1)

        # Second reservation in same run is blocked fail-closed
        res2 = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNone(res2, "Second reservation in same pipeline run must be rejected")
        self.assertEqual(qm.run_requests_count, 1)

    def test_08_daily_limit_five_enforced(self):
        """Verify that daily quota limit (5) blocks reservation when exhausted."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(5)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        res = qm.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNone(res, "Reservation must be rejected when daily limit of 5 is reached")

    def test_09_git_isolation_forbidden_commands_never_called(self):
        """Verify that git clean, reset, stash, checkout, --force are NEVER called during reservation or finalization."""
        qm = QuotaManager(self.config, state_file_override=self.state_file)
        state = self._create_initial_remote_state(0)
        norm_path = self.state_file.replace("\\", "/").lstrip("./")

        recorded_commands = []

        def intercept_sub(cmd, *args, **kwargs):
            recorded_commands.append(cmd)
            if cmd == ["git", "diff", "--cached", "--name-only"]:
                if len([c for c in recorded_commands if c == cmd]) % 2 == 1:
                    return MagicMock(stdout="", returncode=0)
                else:
                    return MagicMock(stdout=f"{norm_path}\n", returncode=0)
            return MagicMock(stdout="", returncode=0)

        with patch("subprocess.run", side_effect=intercept_sub):
            qm.persist_remote_reservation(state)
            qm.persist_remote_finalization(state, "res_test_1", "COMPLETED")

        for cmd in recorded_commands:
            self.assertNotIn("clean", cmd)
            self.assertNotIn("reset", cmd)
            self.assertNotIn("stash", cmd)
            self.assertNotIn("checkout", cmd)
            self.assertNotIn("--force", cmd)

    def _setup_real_git_repos(self):
        """Helper to create a temporary bare remote and a cloned/initialized working repo."""
        import subprocess
        remote_dir = os.path.join(self.test_dir, f"remote_{uuid.uuid4().hex[:6]}.git")
        repo_dir = os.path.join(self.test_dir, f"repo_{uuid.uuid4().hex[:6]}")
        subprocess.run(["git", "init", "--bare", remote_dir], check=True, capture_output=True)
        subprocess.run(["git", "-C", remote_dir, "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        subprocess.run(["git", "init", repo_dir], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo_dir, "config", "user.name", "Sabah Daily News Bot"], check=True)
        subprocess.run(["git", "-C", repo_dir, "config", "user.email", "sumoumou84-simon@users.noreply.github.com"], check=True)

        cfg_dir = os.path.join(repo_dir, "config")
        os.makedirs(cfg_dir, exist_ok=True)
        state_file = os.path.join(cfg_dir, "gemini_quota_state.json")
        init_state = self._create_initial_remote_state(0)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(init_state, f, indent=2)

        subprocess.run(["git", "-C", repo_dir, "add", "."], check=True)
        subprocess.run(["git", "-C", repo_dir, "commit", "-m", "init remote ledger"], check=True)
        subprocess.run(["git", "-C", repo_dir, "branch", "-M", "main"], check=True)
        subprocess.run(["git", "-C", repo_dir, "remote", "add", "origin", remote_dir], check=True)
        subprocess.run(["git", "-C", repo_dir, "push", "-u", "origin", "main"], check=True)

        return remote_dir, repo_dir, state_file

    def test_10_git_add_failure_leaves_working_tree_and_index_clean(self):
        """Requirement 3: Git add failure cleanly aborts, leaving index, HEAD, and user files clean."""
        import subprocess
        remote_dir, repo_dir, state_file = self._setup_real_git_repos()

        # Create uncommitted user work
        user_file = os.path.join(repo_dir, "user_notes.txt")
        with open(user_file, "w") as f:
            f.write("Important uncommitted work")

        head_before = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()

        cfg = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": state_file,
                "execution_mode": "CI_PRODUCTION"
            }
        }
        qm = QuotaManager(cfg, state_file_override=state_file, execution_mode_override="CI_PRODUCTION", repo_dir=repo_dir)
        state = self._create_initial_remote_state(1)

        # Force git add in isolated index to fail by intercepting subprocess
        orig_run = subprocess.run
        def failing_add(cmd, *args, **kwargs):
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "add" and "tmp_quota" in kwargs.get("env", {}).get("GIT_INDEX_FILE", ""):
                return MagicMock(returncode=1, stderr="fatal: mock git add failure")
            return orig_run(cmd, *args, **kwargs)

        with patch("subprocess.run", side_effect=failing_add):
            ok, reason = qm._persist_remote_state_isolated(state, "test add fail")
            self.assertFalse(ok)
            self.assertIn("GIT_ADD_FAILED", reason)

        # Invariants: HEAD unchanged, zero staged files, user work intact
        head_after = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(head_before, head_after)
        staged = subprocess.run(["git", "-C", repo_dir, "diff", "--cached", "--name-only"], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(staged, "")
        self.assertTrue(os.path.exists(user_file))

    def test_11_git_commit_failure_leaves_head_and_index_clean(self):
        """Requirement 4: Git commit-tree failure leaves HEAD and index clean."""
        import subprocess
        remote_dir, repo_dir, state_file = self._setup_real_git_repos()

        user_file = os.path.join(repo_dir, "user_notes.txt")
        with open(user_file, "w") as f:
            f.write("Important uncommitted work")

        head_before = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()

        cfg = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": state_file,
                "execution_mode": "CI_PRODUCTION"
            }
        }
        qm = QuotaManager(cfg, state_file_override=state_file, execution_mode_override="CI_PRODUCTION", repo_dir=repo_dir)
        state = self._create_initial_remote_state(1)

        orig_run = subprocess.run
        def failing_commit(cmd, *args, **kwargs):
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "commit-tree":
                return MagicMock(returncode=1, stderr="fatal: mock git commit-tree failure")
            return orig_run(cmd, *args, **kwargs)

        with patch("subprocess.run", side_effect=failing_commit):
            ok, reason = qm._persist_remote_state_isolated(state, "test commit fail")
            self.assertFalse(ok)
            self.assertIn("COMMIT_TREE_FAILED", reason)

        head_after = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(head_before, head_after)
        staged = subprocess.run(["git", "-C", repo_dir, "diff", "--cached", "--name-only"], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(staged, "")
        self.assertTrue(os.path.exists(user_file))

    def test_12_git_push_failure_leaves_head_and_index_clean(self):
        """Requirement 5: Push failure leaves HEAD not advanced and index clean without stranded commits."""
        import subprocess
        remote_dir, repo_dir, state_file = self._setup_real_git_repos()

        user_file = os.path.join(repo_dir, "user_notes.txt")
        with open(user_file, "w") as f:
            f.write("Important uncommitted work")

        head_before = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()

        cfg = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": state_file,
                "execution_mode": "CI_PRODUCTION"
            }
        }
        qm = QuotaManager(cfg, state_file_override=state_file, execution_mode_override="CI_PRODUCTION", repo_dir=repo_dir)
        state = self._create_initial_remote_state(1)

        # Break remote URL to guarantee push failure
        subprocess.run(["git", "-C", repo_dir, "remote", "set-url", "origin", "C:/non_existent_path.git"], check=True)

        ok, reason = qm._persist_remote_state_isolated(state, "test push fail")
        self.assertFalse(ok)
        self.assertIn("PUSH_FAILED", reason)

        # Crucial invariants:
        # Local HEAD was NOT moved!
        head_after = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(head_before, head_after)

        # Main index was NOT dirtied!
        staged = subprocess.run(["git", "-C", repo_dir, "diff", "--cached", "--name-only"], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(staged, "")

        # User uncommitted work is completely intact!
        self.assertTrue(os.path.exists(user_file))

    def test_13_push_rejection_reconciles_with_concurrent_reservations(self):
        """Requirements 6 & 7: Concurrent push rejection triggers authoritative reconciliation, preserving other reservations."""
        import subprocess
        remote_dir, repo_dir, state_file = self._setup_real_git_repos()

        # Clone second working repo simulating a concurrent GitHub Actions runner
        repo2_dir = os.path.join(self.test_dir, f"repo2_{uuid.uuid4().hex[:6]}")
        subprocess.run(["git", "clone", remote_dir, repo2_dir], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo2_dir, "config", "user.name", "Runner 2 Bot"], check=True)
        subprocess.run(["git", "-C", repo2_dir, "config", "user.email", "runner2@example.com"], check=True)

        # Runner 1 reserves slot 1
        cfg1 = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": state_file,
                "execution_mode": "CI_PRODUCTION"
            }
        }
        qm1 = QuotaManager(cfg1, state_file_override=state_file, execution_mode_override="CI_PRODUCTION", repo_dir=repo_dir)
        res1 = qm1.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNotNone(res1)
        res1_id = res1["reservation_id"]

        # Runner 2 pulls and reserves slot 2 concurrently!
        subprocess.run(["git", "-C", repo2_dir, "pull", "origin", "main"], check=True, capture_output=True)
        state_file2 = os.path.join(repo2_dir, "config", "gemini_quota_state.json")
        cfg2 = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": state_file2,
                "execution_mode": "CI_PRODUCTION"
            }
        }
        qm2 = QuotaManager(cfg2, state_file_override=state_file2, execution_mode_override="CI_PRODUCTION", repo_dir=repo2_dir)
        res2 = qm2.reserve_slot("gemini-3.5-flash-lite")
        self.assertIsNotNone(res2)
        res2_id = res2["reservation_id"]

        # Now Runner 1 is behind origin/main!
        # Runner 1 finishes request and finalizes slot 1 to COMPLETED
        ok = qm1.finalize_slot(res1_id, "COMPLETED")
        self.assertTrue(ok, "Finalize must succeed via automatic non-fast-forward reconciliation")

        # Inspect origin/main to verify both reservations and exact states:
        res_show = subprocess.run(["git", "-C", repo_dir, "show", "origin/main:config/gemini_quota_state.json"], check=True, capture_output=True, text=True)
        final_remote = json.loads(res_show.stdout)

        # Requirement 7: Concurrent update cannot overwrite other reservations
        self.assertEqual(final_remote["reserved_count"], 2)
        self.assertEqual(len(final_remote["reservations"]), 2)

        res_map = {r["reservation_id"]: r["status"] for r in final_remote["reservations"]}
        self.assertEqual(res_map[res1_id], "COMPLETED")
        self.assertEqual(res_map[res2_id], "RESERVED", "Runner 2's reservation must remain preserved as RESERVED!")

    def test_14_terminal_reservation_never_regresses_to_reserved(self):
        """Requirement 8: Once a reservation reaches a terminal status, reconciliation never regresses it to RESERVED."""
        import subprocess
        remote_dir, repo_dir, state_file = self._setup_real_git_repos()

        # Runner 1 in repo_dir
        cfg1 = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": state_file,
                "execution_mode": "CI_PRODUCTION"
            }
        }
        qm1 = QuotaManager(cfg1, state_file_override=state_file, execution_mode_override="CI_PRODUCTION", repo_dir=repo_dir)
        res = qm1.reserve_slot("gemini-3.5-flash-lite")
        res_id = res["reservation_id"]

        # Runner 2 in repo2 clones and finalizes res_id to COMPLETED
        repo2_dir = os.path.join(self.test_dir, f"repo2_{uuid.uuid4().hex[:6]}")
        subprocess.run(["git", "clone", remote_dir, repo2_dir], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo2_dir, "config", "user.name", "Runner 2 Bot"], check=True)
        subprocess.run(["git", "-C", repo2_dir, "config", "user.email", "runner2@example.com"], check=True)
        state_file2 = os.path.join(repo2_dir, "config", "gemini_quota_state.json")
        cfg2 = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "state_file": state_file2,
                "execution_mode": "CI_PRODUCTION"
            }
        }
        qm2 = QuotaManager(cfg2, state_file_override=state_file2, execution_mode_override="CI_PRODUCTION", repo_dir=repo2_dir)
        self.assertTrue(qm2.finalize_slot(res_id, "COMPLETED"))

        # Runner 1 is now behind origin/main, with local reservation still RESERVED!
        # Runner 1 attempts to finalize / sync with RESERVED status
        qm1.finalize_slot(res_id, "RESERVED")

        # Verify remote did NOT regress to RESERVED!
        res_show = subprocess.run(["git", "-C", repo_dir, "show", "origin/main:config/gemini_quota_state.json"], check=True, capture_output=True, text=True)
        remote_state = json.loads(res_show.stdout)
        target = next(r for r in remote_state["reservations"] if r["reservation_id"] == res_id)
        self.assertEqual(target["status"], "COMPLETED", "Terminal status COMPLETED must never regress to RESERVED")

    def test_15_finalization_failure_stops_production_publishing(self):
        """Requirement 9: If finalization remote sync fails, production publishing MUST abort completely."""
        qm = QuotaManager(self.config, state_file_override=self.state_file, execution_mode_override="MOCK_TEST")
        valid_remote = self._create_initial_remote_state(0)
        qm.fetch_authoritative_remote_state = MagicMock(return_value=(valid_remote, "REMOTE_VALID"))

        # Reservation succeeds
        qm.persist_remote_reservation = MagicMock(return_value=True)

        # Finalization remote push FAILS (simulating remote rejection / sync failure)
        qm.persist_remote_finalization = MagicMock(return_value=False)

        synth = NewsSynthesizer(self.config, quota_mgr=qm)
        test_articles = [RawArticle(title="Valid Test Article", url="https://x.com", source="Official Src", category="sabah")]

        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps([{
                            "category": "sabah",
                            "title": "Sabah Test Title",
                            "titleBM": "Tajuk Ujian Sabah",
                            "detail": "Sabah test detail substantif",
                            "detailBM": "Butiran ujian Sabah",
                            "source": "Official Src",
                            "source_url": "https://x.com"
                        }])
                    }]
                },
                "finishReason": "STOP"
            }],
            "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 200, "totalTokenCount": 300}
        }).encode("utf-8")

        orig_open = open
        def safe_open(file, *args, **kwargs):
            file_str = str(file)
            if "reports" in file_str and any(m in args or kwargs.get("mode", "") for m in ["w", "a"]):
                file_str = os.path.join(self.test_dir, os.path.basename(file_str))
            return orig_open(file_str, *args, **kwargs)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("builtins.open", side_effect=safe_open):
            # 1. Direct single-batch synthesis must return None
            batch_res = synth.synthesize_track_a_single_batch("test_key", "2026-11-11", test_articles)
            self.assertIsNone(batch_res, "Must return None when finalization sync fails, even on HTTP 200")

            # 2. Main synthesize entry point must return [] (fail-closed, zero articles published)
            synth.quota_mgr.run_requests_count = 0  # reset run counter to test entry point
            dispatch_res = synth.synthesize("2026-11-11", test_articles, api_key="test_key")
            self.assertEqual(dispatch_res, [], "synthesize() must return [] when finalization sync fails")


if __name__ == "__main__":
    unittest.main()
