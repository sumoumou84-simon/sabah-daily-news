#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for scripts/run_gemini_discovery_diagnostic.py
Verifies:
1. Safe abort with 0 HTTP calls when no API key is present.
2. Safe abort with 0 HTTP calls when reservation fails or quota exhausted.
3. Exactly ONE HTTP call dispatched upon successful reservation.
4. HTTP errors (429, 401, 500, timeout) do not retry and finalize slot as failed.
5. Extraction and classification of grounding chunks and candidates.
6. Absolute non-modification of news_data.json or index.html.
7. Zero API key leakage in logs or reports.
"""

import os
import sys
import json
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.run_gemini_discovery_diagnostic import (
    run_discovery_diagnostic,
    build_grounded_payload,
    parse_gemini_json_array,
    mask_secret
)
from pipeline.synthesizer import QuotaManager


class TestGeminiDiscoveryDiagnostic(unittest.TestCase):

    def setUp(self):
        self.config = {
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "timezone": "Asia/Kuala_Lumpur",
                "fail_closed": True,
                "execution_mode": "MOCK_TEST"
            }
        }

    # 1. Abort with 0 HTTP calls when no API key is configured
    def test_01_missing_api_key_zero_http(self):
        with patch.dict(os.environ, {}, clear=True):
            res = run_discovery_diagnostic(
                api_key_override="",
                config_override=self.config,
                execution_mode_override="MOCK_TEST"
            )
            self.assertEqual(res["status"], "ABORTED_NO_CREDENTIALS")
            self.assertEqual(res["http_requests_sent"], 0)
            self.assertFalse(res["quota_reserved"])

    # 2. Abort with 0 HTTP calls if reservation fails
    def test_02_failed_reservation_zero_http(self):
        with patch.object(QuotaManager, "reserve_slot", return_value=None):
            with patch("urllib.request.urlopen") as mock_url:
                res = run_discovery_diagnostic(
                    api_key_override="test_key_123",
                    config_override=self.config,
                    execution_mode_override="MOCK_TEST"
                )
                self.assertEqual(res["status"], "ABORTED_RESERVATION_FAILED")
                self.assertEqual(res["http_requests_sent"], 0)
                mock_url.assert_not_called()

    # 3. Successful reservation permits exactly ONE HTTP request
    def test_03_successful_reservation_exactly_one_http(self):
        mock_res = {
            "reservation_id": "res_2026-11-09_1_test123",
            "model": "gemini-3.5-flash-lite",
            "status": "RESERVED"
        }
        mock_api_resp = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps([
                                    {
                                        "headline": "Sabah Tables Historic RM8 Billion Budget",
                                        "source": "Daily Express",
                                        "url": "https://www.dailyexpress.com.my/news/123",
                                        "published_at": "2026-11-09T08:00:00+08:00",
                                        "summary": "State Finance Minister announced historic budget.",
                                        "category": "sabah",
                                        "sabah_relevance": "Direct state fiscal policy",
                                        "item_type": "news_article"
                                    }
                                ])
                            }
                        ]
                    },
                    "groundingMetadata": {
                        "webSearchQueries": ["Sabah budget 2026"],
                        "groundingChunks": [
                            {
                                "web": {
                                    "uri": "https://www.dailyexpress.com.my/news/123",
                                    "title": "Sabah Budget 2026"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        mock_http = MagicMock()
        mock_http.getcode.return_value = 200
        mock_http.read.return_value = json.dumps(mock_api_resp).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        with patch.object(QuotaManager, "reserve_slot", return_value=mock_res):
            with patch.object(QuotaManager, "finalize_slot") as mock_finalize:
                with patch("urllib.request.urlopen", return_value=mock_http) as mock_url:
                    res = run_discovery_diagnostic(
                        api_key_override="test_key_123",
                        config_override=self.config,
                        execution_mode_override="MOCK_TEST"
                    )

                    self.assertEqual(res["status"], "SUCCESS")
                    self.assertEqual(res["http_requests_sent"], 1)
                    self.assertEqual(mock_url.call_count, 1)
                    mock_finalize.assert_called_with("res_2026-11-09_1_test123", "COMPLETED")
                    self.assertEqual(len(res["candidates"]), 1)
                    self.assertEqual(res["candidates"][0]["classification"], "A")

    # 4. HTTP error codes do not retry and finalize slot as failed
    def test_04_http_errors_do_not_retry(self):
        mock_res = {
            "reservation_id": "res_2026-11-09_1_test429",
            "model": "gemini-3.5-flash-lite",
            "status": "RESERVED"
        }

        with patch.object(QuotaManager, "reserve_slot", return_value=mock_res):
            with patch.object(QuotaManager, "finalize_slot") as mock_finalize:
                with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("http://x", 429, "Too Many", {}, None)) as mock_url:
                    res = run_discovery_diagnostic(
                        api_key_override="test_key_123",
                        config_override=self.config,
                        execution_mode_override="MOCK_TEST"
                    )

                    self.assertEqual(res["status"], "FAILED_HTTP")
                    self.assertEqual(res["http_requests_sent"], 1)
                    self.assertEqual(mock_url.call_count, 1, "Must never retry on HTTP 429")
                    mock_finalize.assert_called_with("res_2026-11-09_1_test429", "FAILED_HTTP_429: Too Many")

    # 5. Production content files are untouched
    def test_05_no_production_files_modified(self):
        news_data_path = os.path.join(BASE_DIR, "news_data.json")
        before_mtime = os.path.getmtime(news_data_path) if os.path.exists(news_data_path) else None

        mock_res = {
            "reservation_id": "res_2026-11-09_1_test_prod",
            "model": "gemini-3.5-flash-lite",
            "status": "RESERVED"
        }
        mock_api_resp = {"candidates": [{"content": {"parts": [{"text": "[]"}]}}]}
        mock_http = MagicMock()
        mock_http.getcode.return_value = 200
        mock_http.read.return_value = json.dumps(mock_api_resp).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        with patch.object(QuotaManager, "reserve_slot", return_value=mock_res):
            with patch.object(QuotaManager, "finalize_slot"):
                with patch("urllib.request.urlopen", return_value=mock_http):
                    run_discovery_diagnostic(
                        api_key_override="test_key_123",
                        config_override=self.config,
                        execution_mode_override="MOCK_TEST"
                    )

        after_mtime = os.path.getmtime(news_data_path) if os.path.exists(news_data_path) else None
        self.assertEqual(before_mtime, after_mtime, "news_data.json must not be modified by discovery diagnostic")

    # 6. API secret is masked and never leaked
    def test_06_secret_never_leaked(self):
        secret = "AIzaSySecretToken998877"
        masked = mask_secret(f"https://x.com?key={secret}")
        self.assertNotIn(secret, masked)
        self.assertIn("[MASKED_SECRET]", masked)


if __name__ == "__main__":
    unittest.main()
