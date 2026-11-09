#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for scripts/generate_three_articles_d3.py
Verifies:
1. Safe abort with 0 HTTP calls when no API key is present.
2. Safe abort with 0 HTTP calls when reservation fails.
3. Exactly ONE HTTP call dispatched upon successful reservation.
4. HTTP error handling captures error body without retry.
5. Production content files (news_data.json, index.html) remain untouched.
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

from scripts.generate_three_articles_d3 import (
    run_phase_d3,
    build_consolidated_prompt,
    SOURCE_STORIES,
    mask_secret
)
from pipeline.synthesizer import QuotaManager


class TestPhaseD3ThreeArticles(unittest.TestCase):

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

    def test_01_missing_api_key_zero_http(self):
        with patch.dict(os.environ, {}, clear=True):
            res = run_phase_d3(
                api_key_override="",
                config_override=self.config,
                execution_mode_override="MOCK_TEST"
            )
            self.assertEqual(res["status"], "ABORTED_NO_CREDENTIALS")
            self.assertEqual(res["http_requests_sent"], 0)
            self.assertFalse(res["quota_reserved"])

    def test_02_failed_reservation_zero_http(self):
        with patch.object(QuotaManager, "reserve_slot", return_value=None):
            with patch("urllib.request.urlopen") as mock_url:
                res = run_phase_d3(
                    api_key_override="test_key_123",
                    config_override=self.config,
                    execution_mode_override="MOCK_TEST"
                )
                self.assertEqual(res["status"], "ABORTED_RESERVATION_FAILED")
                self.assertEqual(res["http_requests_sent"], 0)
                mock_url.assert_not_called()

    def test_03_successful_generation_three_articles(self):
        mock_res = {
            "reservation_id": "res_2026-11-09_3_testabc",
            "model": "gemini-3.5-flash-lite",
            "status": "RESERVED"
        }
        mock_articles = [
            {
                "story_id": 1,
                "category": "sandakan_local",
                "headline_zh": "沙巴地政运动会山打根开幕",
                "headline_bm": "Sukan PBT Sabah Dirasmikan di Sandakan",
                "summary_zh": "沙巴地政运动会于山打根综合体育馆隆重开幕。",
                "summary_bm": "Sukan PBT Sabah dirasmikan dengan meriah di Sandakan.",
                "full_article_zh": "第14届沙巴州地方政府运动会昨晚在山打根隆重开幕...",
                "full_article_bm": "Sukan PBT Sabah Ke-14 telah dirasmikan di Kompleks Sukan Sandakan...",
                "publication_date": "2026-11-08T15:05:59+08:00",
                "event_date": "2026-11-07",
                "location": "Sandakan",
                "key_figures": ["Mohd Arifin", "Walter Kenson"],
                "key_data_points": ["2,358 participants", "RM2.358m impact"],
                "original_url": "https://news.seehua.com/post/1601871/",
                "verified_facts": ["24-hour operation approved for low-risk business"],
                "unconfirmed_or_limitations": "Tournaments continue until Nov 13"
            },
            {
                "story_id": 2,
                "category": "state_policy",
                "headline_zh": "沙巴预算案12月4日提呈",
                "headline_bm": "Belanjawan Sabah 2027 Dibentang 4 Disember",
                "summary_zh": "哈芝芝诺宣布沙巴2027年财政预算案将于12月4日提呈。",
                "summary_bm": "Hajiji mengumumkan Belanjawan Sabah 2027 akan dibentangkan pada 4 Disember.",
                "full_article_zh": "沙巴首席部长拿督斯里哈芝芝诺表示...",
                "full_article_bm": "Ketua Menteri Sabah Datuk Seri Hajiji Noor menyatakan...",
                "publication_date": "2026-11-08T14:18:43+08:00",
                "event_date": "2026-11-08",
                "location": "Kota Kinabalu",
                "key_figures": ["Hajiji Noor", "Masidi Manjun"],
                "key_data_points": ["Dec 4 tabling"],
                "original_url": "https://news.seehua.com/post/1601838/",
                "verified_facts": ["Focus on water, electricity, and roads"],
                "unconfirmed_or_limitations": "Specific allocations not yet disclosed"
            },
            {
                "story_id": 3,
                "category": "rural_development",
                "headline_zh": "沙巴18村获批昌明领养甘榜计划",
                "headline_bm": "18 Kampung di Sabah Diluluskan Program Kampung Angkat Madani",
                "summary_zh": "沙巴今年获900万令吉拨款用于18个甘榜基建提升。",
                "summary_bm": "Sabah menerima peruntukan RM9 juta bagi 18 kampung.",
                "full_article_zh": "首相署部长拿督穆斯达法沙末指出...",
                "full_article_bm": "Menteri di Jabatan Perdana Menteri Datuk Mustapha Sakmud menyatakan...",
                "publication_date": "2026-11-09T10:31:40+08:00",
                "event_date": "2026-11-09",
                "location": "Kota Marudu",
                "key_figures": ["Mustapha Sakmud"],
                "key_data_points": ["18 villages", "RM9 million total", "RM500k per village"],
                "original_url": "https://news.seehua.com/post/1602269/",
                "verified_facts": ["4 projects completed in Kg Golongkong"],
                "unconfirmed_or_limitations": "More rural areas still need development"
            }
        ]

        mock_api_resp = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": json.dumps(mock_articles)}
                        ]
                    }
                }
            ]
        }

        with patch.object(QuotaManager, "reserve_slot", return_value=mock_res):
            with patch.object(QuotaManager, "finalize_slot") as mock_finalize:
                mock_resp = MagicMock()
                mock_resp.getcode.return_value = 200
                mock_resp.read.return_value = json.dumps(mock_api_resp).encode("utf-8")
                mock_resp.__enter__.return_value = mock_resp

                with patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
                    res = run_phase_d3(
                        api_key_override="test_key_valid",
                        config_override=self.config,
                        execution_mode_override="MOCK_TEST"
                    )

                    self.assertEqual(res["http_requests_sent"], 1)
                    self.assertEqual(res["http_status_code"], 200)
                    self.assertTrue(res["success"])
                    self.assertEqual(res["articles_count"], 3)
                    self.assertFalse(res["production_integrity_check"]["news_data_modified"])
                    self.assertFalse(res["production_integrity_check"]["website_published"])
                    mock_finalize.assert_called_with("res_2026-11-09_3_testabc", "COMPLETED")

    def test_04_http_429_fails_without_retry(self):
        mock_res = {
            "reservation_id": "res_2026-11-09_3_test429",
            "model": "gemini-3.5-flash-lite",
            "status": "RESERVED"
        }
        http_err = urllib.error.HTTPError(
            url="https://generativelanguage.googleapis.com",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"error":{"code":429,"message":"Resource exhausted"}}')
        )

        with patch.object(QuotaManager, "reserve_slot", return_value=mock_res):
            with patch.object(QuotaManager, "finalize_slot") as mock_finalize:
                with patch("urllib.request.urlopen", side_effect=http_err) as mock_url:
                    res = run_phase_d3(
                        api_key_override="test_key_valid",
                        config_override=self.config,
                        execution_mode_override="MOCK_TEST"
                    )

                    self.assertEqual(res["http_requests_sent"], 1)
                    self.assertEqual(res["http_status_code"], 429)
                    self.assertFalse(res["success"])
                    self.assertIn("Resource exhausted", res["raw_error_body"])
                    mock_finalize.assert_called_with("res_2026-11-09_3_test429", "FAILED_HTTP_429")
                    self.assertEqual(mock_url.call_count, 1)

    def test_05_secret_masking(self):
        raw = "Error at https://endpoint.com?key=AIzaSyA1234567890abcdef and other info"
        masked = mask_secret(raw)
        self.assertNotIn("AIzaSyA1234567890abcdef", masked)
        self.assertIn("[MASKED_SECRET]", masked)


if __name__ == "__main__":
    unittest.main()
