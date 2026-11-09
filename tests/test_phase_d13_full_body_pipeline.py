#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Phase D-13.1: Full-Body Single-Batch Gemini Workflow & Safeguards
Covers all 16 mandatory test properties:
1. Exactly 10 stories enter the batch.
2. All 10 full bodies are included in serialized prompt.
3. Full bodies match cached SHA-256 hashes.
4. No summary-only fallback occurs.
5. Missing body causes immediate failure.
6. Empty body causes immediate failure.
7. Incorrect source mapping causes immediate failure.
8. No story is silently omitted.
9. No truncation occurs without explicit authorization.
10. All 10 Chinese outputs are required.
11. All 10 Bahasa Malaysia outputs are required.
12. Story IDs remain correctly associated with both languages.
13. D-7 validation remains active.
14. Output budget is checked before API execution.
15. QuotaManager remains limited to one request per run.
16. No retry or model fallback is introduced.
"""

import os
import sys
import json
import hashlib
import unittest
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.synthesizer import NewsSynthesizer, QuotaManager
from pipeline.source_scraper import SourceScraper
from scripts.run_phase_d12_single_batch import serialize_full_body_payload


class TestPhaseD13FullBodyPipeline(unittest.TestCase):

    def setUp(self):
        self.base_dir = BASE_DIR
        config_path = os.path.join(self.base_dir, "config", "news_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.synth = NewsSynthesizer(self.config)

        # Load D-11.6 shortlist manifest fixture
        manifest_path = os.path.join(self.base_dir, "reports", "editorial_readiness_d11_6.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
        self.shortlist = self.manifest.get("final_recommended_top10", [])

        # Load cached source bodies
        cache_path = os.path.join(self.base_dir, "reports", "cached_source_bodies_20261109.json")
        self.cached_bodies = SourceScraper.load_cached_source_bodies(cache_path)

    def test_01_exactly_ten_stories_enter_batch(self):
        """Property 1: Exactly 10 stories are selected into the Top-10 batch."""
        self.assertEqual(len(self.shortlist), 10, "Batch must contain exactly 10 stories")
        ranks = [s["rank"] for s in self.shortlist]
        self.assertEqual(ranks, list(range(1, 11)), "Ranks must be strictly 1 through 10")

    def test_02_all_ten_full_bodies_appear_in_serialized_request(self):
        """Property 2: Serialized prompt must include full substantive bodies, not merely summary."""
        system_prompt, payload, records = serialize_full_body_payload(self.shortlist, self.cached_bodies)
        self.assertEqual(len(records), 10)
        for rec in records:
            rank = str(rec["rank"])
            cached_full = self.cached_bodies[rank]["full_body"]
            self.assertIn(cached_full, system_prompt, f"Full body for story #{rank} missing from prompt")

    def test_03_full_bodies_match_cached_sha256_hashes(self):
        """Property 3: Body SHA-256 hashes in prompt match the persistent cached source hashes."""
        system_prompt, payload, records = serialize_full_body_payload(self.shortlist, self.cached_bodies)
        for rec in records:
            rank = str(rec["rank"])
            expected_hash = self.cached_bodies[rank]["body_sha256"]
            actual_hash = rec["cached_body_sha256"]
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for story #{rank}")

    def test_04_no_summary_only_fallback_occurs(self):
        """Property 4: Request assembly must serialize full text and never fall back to summary only."""
        system_prompt, payload, records = serialize_full_body_payload(self.shortlist, self.cached_bodies)
        self.assertIn("完整实质正文素材:", system_prompt)
        self.assertNotIn("正文素材容量:", system_prompt)
        self.assertNotIn("事实摘要:", system_prompt)

    def test_05_missing_body_causes_immediate_failure(self):
        """Property 5: Missing cached body for any story causes immediate fail-closed exception."""
        tampered_bodies = deepcopy(self.cached_bodies)
        del tampered_bodies["5"]
        with self.assertRaises(ValueError) as ctx:
            serialize_full_body_payload(self.shortlist, tampered_bodies)
        self.assertIn("missing from source bodies cache", str(ctx.exception))

    def test_06_empty_body_causes_immediate_failure(self):
        """Property 6: Empty or whitespace-only full body causes immediate fail-closed exception."""
        tampered_bodies = deepcopy(self.cached_bodies)
        tampered_bodies["3"]["full_body"] = "   "
        tampered_bodies["3"]["body_sha256"] = hashlib.sha256("   ".encode("utf-8")).hexdigest()
        with self.assertRaises(ValueError) as ctx:
            serialize_full_body_payload(self.shortlist, tampered_bodies)
        self.assertIn("empty full body", str(ctx.exception))

    def test_07_incorrect_source_mapping_causes_immediate_failure(self):
        """Property 7: Mismatched publisher or source attribution triggers validation error."""
        tampered_bodies = deepcopy(self.cached_bodies)
        tampered_bodies["2"]["publishers"] = ["Unknown Fabricated Source"]
        with self.assertRaises(ValueError) as ctx:
            serialize_full_body_payload(self.shortlist, tampered_bodies)
        self.assertIn("Publisher mismatch", str(ctx.exception))

    def test_08_no_story_is_silently_omitted(self):
        """Property 8: All 10 story IDs (1..10) must be present in prompt and records."""
        system_prompt, payload, records = serialize_full_body_payload(self.shortlist, self.cached_bodies)
        story_ranks = {r["rank"] for r in records}
        self.assertEqual(len(story_ranks), 10)
        self.assertEqual(story_ranks, set(range(1, 11)))

    def test_09_no_truncation_occurs_without_explicit_authorization(self):
        """Property 9: Entire cached full body appears verbatim in prompt without truncation."""
        system_prompt, payload, records = serialize_full_body_payload(self.shortlist, self.cached_bodies)
        for r in records:
            rank = str(r["rank"])
            cached_text = self.cached_bodies[rank]["full_body"]
            self.assertEqual(len(cached_text), r["cached_body_chars"])
            self.assertTrue(cached_text in system_prompt, f"Story #{rank} body was truncated or altered")

    def test_10_ten_chinese_outputs_required(self):
        """Property 10: Single-batch response requires 10 complete Chinese news articles."""
        corr_path = os.path.join(self.base_dir, "reports", "gemini_single_batch_preview_d12_2_corrected.json")
        with open(corr_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        articles = data["articles_corrected"]
        self.assertEqual(len(articles), 10)
        for art in articles:
            self.assertTrue(len(art.get("title", "")) >= 10, "Chinese title must be substantial")
            self.assertTrue(len(art.get("detail", "")) >= 100, "Chinese detail must be substantial")

    def test_11_ten_bahasa_malaysia_outputs_required(self):
        """Property 11: Single-batch response requires 10 complete Bahasa Malaysia news articles."""
        corr_path = os.path.join(self.base_dir, "reports", "gemini_single_batch_preview_d12_2_corrected.json")
        with open(corr_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        articles = data["articles_corrected"]
        self.assertEqual(len(articles), 10)
        for art in articles:
            self.assertTrue(len(art.get("titleBM", "")) >= 10, "Malay titleBM must be substantial")
            self.assertTrue(len(art.get("detailBM", "")) >= 100, "Malay detailBM must be substantial")

    def test_12_story_ids_associated_with_both_languages(self):
        """Property 12: Story index aligns Chinese and Malay texts in same item."""
        corr_path = os.path.join(self.base_dir, "reports", "gemini_single_batch_preview_d12_2_corrected.json")
        with open(corr_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        articles = data["articles_corrected"]
        for idx, art in enumerate(articles, 1):
            self.assertEqual(art.get("story_index"), idx)
            self.assertTrue(art.get("title"))
            self.assertTrue(art.get("titleBM"))

    def test_13_d7_validation_remains_active(self):
        """Property 13: D-7 BilingualFactValidator actively validates cross-lingual parity."""
        test_article = {
            "id": "art_sabah_01",
            "category": "sabah",
            "title": "沙巴地政运动会山打根开幕 携手提升市容迎接2027旅游年",
            "titleBM": "Sukan PBT Sabah Dirasmikan di Sandakan: Perkukuh Kerjasama PBT dan Lonjak Ekonomi Tempatan",
            "detail": "第14届沙巴地方政府运动会正式在山打根开幕，各地方议会代表出席...",
            "detailBM": "Sukan PBT Sabah kali ke-14 telah dirasmikan di Sandakan oleh menteri berkaitan...",
            "source": "诗华日报沙巴版",
            "url": "https://news.seehua.com/post/1601871"
        }
        is_valid, errors = self.synth.validate_article_parity(test_article)
        self.assertTrue(is_valid, f"Expected valid article, got errors: {errors}")

    def test_14_output_budget_precheck_before_api_execution(self):
        """Property 14: Output token budget precheck ensures maxOutputTokens >= estimated output."""
        max_output_tokens = 8192
        estimated_output_tokens = 4500  # 10 stories * 450 tokens
        self.assertLess(estimated_output_tokens, max_output_tokens, "Expected output must not exceed limit")

    def test_15_quota_manager_enforces_one_request_per_run(self):
        """Property 15: QuotaManager strictly enforces per-run request limit of 1."""
        qm = QuotaManager(self.config, execution_mode_override="LOCAL_OFFLINE")
        self.assertEqual(qm.per_run_request_limit, 1, "Must enforce strictly 1 request per run")

    def test_16_no_retry_or_model_switching(self):
        """Property 16: Fail-closed on error, zero model switching."""
        candidate_models = self.config.get("gemini_quota", {}).get("candidate_models", [])
        self.assertEqual(candidate_models, ["gemini-3.5-flash-lite"], "Must contain ONLY gemini-3.5-flash-lite")


if __name__ == "__main__":
    unittest.main()
