import os
import json
import tempfile
import unittest
import urllib.error
from unittest.mock import patch, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.smoke_test_gemini import run_gemini_smoke_test, CANDIDATE_MODEL
from pipeline.synthesizer import QuotaManager, MYT_TZ


class TestGeminiSmokeTestScript(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.state_file = os.path.join(self.test_dir.name, "test_quota_state.json")
        self.config = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": [CANDIDATE_MODEL],
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

    def _create_valid_remote_state(self, reserved_count=0):
        today_str = datetime.now(MYT_TZ).strftime("%Y-%m-%d")
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

    # 1. Safe default mode sends zero HTTP requests
    def test_01_safe_default_mode_zero_http(self):
        with patch("urllib.request.urlopen") as mock_url:
            res = run_gemini_smoke_test(execute=False, config=self.config)
            self.assertEqual(res["status"], "DRY_RUN_SAFE")
            self.assertFalse(res["http_request_attempted"])
            mock_url.assert_not_called()

    # 2. Missing API key sends zero HTTP requests
    def test_02_missing_api_key_zero_http(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=True):
            with patch("urllib.request.urlopen") as mock_url:
                res = run_gemini_smoke_test(execute=True, config=self.config, api_key_override="")
                self.assertEqual(res["status"], "ABORTED_NO_CREDENTIALS")
                self.assertFalse(res["http_request_attempted"])
                mock_url.assert_not_called()

    # 3. Missing remote quota state sends zero HTTP requests (Condition B)
    def test_03_missing_remote_state_zero_http(self):
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stderr="fatal: path not found", returncode=1)
            ]
            with patch("urllib.request.urlopen") as mock_url:
                res = run_gemini_smoke_test(
                    execute=True,
                    config=self.config,
                    api_key_override="test_key",
                    execution_mode_override="CI_PRODUCTION"
                )
                self.assertEqual(res["status"], "ABORTED_RESERVATION_FAILED")
                self.assertFalse(res["http_request_attempted"])
                mock_url.assert_not_called()

    # 4. Remote fetch failure sends zero HTTP requests (Condition C)
    def test_04_remote_fetch_failure_zero_http(self):
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stderr="fatal: network error", returncode=128)
            ]
            with patch("urllib.request.urlopen") as mock_url:
                res = run_gemini_smoke_test(
                    execute=True,
                    config=self.config,
                    api_key_override="test_key",
                    execution_mode_override="CI_PRODUCTION"
                )
                self.assertEqual(res["status"], "ABORTED_RESERVATION_FAILED")
                self.assertFalse(res["http_request_attempted"])
                mock_url.assert_not_called()

    # 5. Corrupted remote state sends zero HTTP requests (Condition D)
    def test_05_corrupted_remote_state_zero_http(self):
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = [
                MagicMock(stdout="main\n", returncode=0),
                MagicMock(stdout="", returncode=0),
                MagicMock(stdout="{corrupt_json: true", returncode=0)
            ]
            with patch("urllib.request.urlopen") as mock_url:
                res = run_gemini_smoke_test(
                    execute=True,
                    config=self.config,
                    api_key_override="test_key",
                    execution_mode_override="CI_PRODUCTION"
                )
                self.assertEqual(res["status"], "ABORTED_RESERVATION_FAILED")
                self.assertFalse(res["http_request_attempted"])
                mock_url.assert_not_called()

    # 6. Reservation push rejection sends zero HTTP requests
    def test_06_push_rejection_zero_http(self):
        valid_remote = self._create_valid_remote_state(0)
        with patch.object(QuotaManager, "fetch_authoritative_remote_state", return_value=(valid_remote, "REMOTE_VALID")):
            with patch.object(QuotaManager, "persist_remote_reservation", return_value=False):
                with patch("urllib.request.urlopen") as mock_url:
                    res = run_gemini_smoke_test(
                        execute=True,
                        config=self.config,
                        api_key_override="test_key",
                        execution_mode_override="MOCK_TEST"
                    )
                    self.assertEqual(res["status"], "ABORTED_RESERVATION_FAILED")
                    self.assertFalse(res["http_request_attempted"])
                    mock_url.assert_not_called()

    # 7. Successful reservation permits exactly one HTTP request
    def test_07_successful_reservation_permits_exactly_one_http(self):
        valid_remote = self._create_valid_remote_state(0)
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.__enter__.return_value = mock_resp

        with patch.object(QuotaManager, "fetch_authoritative_remote_state", return_value=(valid_remote, "REMOTE_VALID")):
            with patch.object(QuotaManager, "persist_remote_reservation", return_value=True):
                with patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
                    res = run_gemini_smoke_test(
                        execute=True,
                        config=self.config,
                        api_key_override="test_key",
                        execution_mode_override="MOCK_TEST"
                    )
                    self.assertEqual(res["status"], "SUCCESS")
                    self.assertEqual(res["http_code"], 200)
                    self.assertEqual(mock_url.call_count, 1)

    # 8. HTTP 401, 403, 429, 404, and timeout do not trigger retries
    def test_08_error_codes_do_not_retry(self):
        error_cases = [
            urllib.error.HTTPError("https://x", 401, "Unauthorized", {}, None),
            urllib.error.HTTPError("https://x", 403, "Forbidden", {}, None),
            urllib.error.HTTPError("https://x", 429, "Too Many Requests", {}, None),
            urllib.error.HTTPError("https://x", 404, "Not Found", {}, None),
            urllib.error.URLError("timed out")
        ]

        for err in error_cases:
            self.setUp()
            valid_remote = self._create_valid_remote_state(0)
            with patch.object(QuotaManager, "fetch_authoritative_remote_state", return_value=(valid_remote, "REMOTE_VALID")):
                with patch.object(QuotaManager, "persist_remote_reservation", return_value=True):
                    with patch("urllib.request.urlopen", side_effect=err) as mock_url:
                        res = run_gemini_smoke_test(
                            execute=True,
                            config=self.config,
                            api_key_override="test_key",
                            execution_mode_override="MOCK_TEST"
                        )
                        self.assertEqual(mock_url.call_count, 1, f"Error {err} must not trigger retries")

    # 9. Failed requests do not refund quota
    def test_09_failed_requests_do_not_refund_quota(self):
        valid_remote = self._create_valid_remote_state(0)
        with patch.object(QuotaManager, "fetch_authoritative_remote_state", return_value=(valid_remote, "REMOTE_VALID")):
            with patch.object(QuotaManager, "persist_remote_reservation", return_value=True):
                with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("https://x", 429, "Too Many", {}, None)):
                    res = run_gemini_smoke_test(
                        execute=True,
                        config=self.config,
                        api_key_override="test_key",
                        execution_mode_override="MOCK_TEST"
                    )

        # Inspect local state file
        with open(self.state_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        self.assertEqual(state["reserved_count"], 1, "Reserved count must not be decremented on error")
        self.assertEqual(state["reservations"][0]["status"], "FAILED_HTTP_429")

    # 10. No production files are modified
    def test_10_no_production_files_modified(self):
        news_data_path = os.path.join(os.getcwd(), "news_data.json")
        before_mtime = os.path.getmtime(news_data_path) if os.path.exists(news_data_path) else None

        valid_remote = self._create_valid_remote_state(0)
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.__enter__.return_value = mock_resp

        with patch.object(QuotaManager, "fetch_authoritative_remote_state", return_value=(valid_remote, "REMOTE_VALID")):
            with patch.object(QuotaManager, "persist_remote_reservation", return_value=True):
                with patch("urllib.request.urlopen", return_value=mock_resp):
                    run_gemini_smoke_test(
                        execute=True,
                        config=self.config,
                        api_key_override="test_key",
                        execution_mode_override="MOCK_TEST"
                    )

        after_mtime = os.path.getmtime(news_data_path) if os.path.exists(news_data_path) else None
        self.assertEqual(before_mtime, after_mtime, "news_data.json must not be modified by smoke test")

    # 11. API key never appears in logs or error output
    def test_11_api_key_never_leaked(self):
        secret_key = "SECRET_SUPER_SENSITIVE_KEY_12345"
        valid_remote = self._create_valid_remote_state(0)
        with patch.object(QuotaManager, "fetch_authoritative_remote_state", return_value=(valid_remote, "REMOTE_VALID")):
            with patch.object(QuotaManager, "persist_remote_reservation", return_value=True):
                with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("https://x", 401, "Unauthorized", {}, None)):
                    with self.assertLogs("scripts.smoke_test_gemini", level="INFO") as log_cm:
                        res = run_gemini_smoke_test(
                            execute=True,
                            config=self.config,
                            api_key_override=secret_key,
                            execution_mode_override="MOCK_TEST"
                        )
                        for log_msg in log_cm.output:
                            self.assertNotIn(secret_key, log_msg, "Secret API key must NEVER appear in log output")
                        self.assertNotIn(secret_key, str(res), "Secret API key must NEVER appear in result dictionary")


if __name__ == "__main__":
    unittest.main()
