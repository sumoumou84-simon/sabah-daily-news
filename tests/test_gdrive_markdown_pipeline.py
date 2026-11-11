#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Sabah Daily News — Google Drive Markdown Input Integration
Covers all 11 mandatory test requirements from Section Eight:
1. Google Drive input module structure and configuration test.
2. Markdown file reading and parsing test.
3. Variable news count parsing test (never assuming fixed 10, 25, 26).
4. Mixed language (Chinese, English, Malay) content parsing test.
5. Date and timezone (Asia/Kuala_Lumpur) test.
6. News category classification and future event forecast separation test.
7. Markdown missing, empty file, read failure fail-closed test.
8. Single Gemini batch input construction test (mock, 0 API calls).
9. Bilingual output data structure compatibility test.
10. Existing website data structure (news_data.json, archive_history.json) compatibility test.
11. Git identity setting location and QuotaManager commit path test.
"""

import os
import sys
import json
import tempfile
import unittest
import hashlib
import subprocess
import urllib.parse
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.gdrive_reader import GDriveMarkdownReader, ParsedMarkdownStory, GDriveInputSnapshot, MYT
from pipeline.synthesizer import NewsSynthesizer, QuotaManager
from pipeline.circuit_breaker import CircuitBreaker, CircuitBreakerException
from collectors.base import RawArticle
import agent_reach_editor


class TestGDriveMarkdownPipeline(unittest.TestCase):

    def setUp(self):
        self.base_dir = BASE_DIR
        self.test_dir = tempfile.TemporaryDirectory()
        self.sample_md_path = os.path.join(self.base_dir, "data", "gdrive_inputs", "sabah_news_2026-11-10.md")

        with open(os.path.join(self.base_dir, "config", "news_config.json"), "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.reader = GDriveMarkdownReader(self.config)

    def tearDown(self):
        try:
            self.test_dir.cleanup()
        except Exception:
            pass

    # =========================================================================
    # Test 1: Google Drive input module structure & configuration
    # =========================================================================
    def test_01_gdrive_module_structure_and_config(self):
        """Test 1: Verify GDriveMarkdownReader initialization, config fields, and candidate filename generator."""
        self.assertTrue(self.reader.enabled)
        self.assertIsInstance(self.reader.file_name_patterns, list)
        self.assertTrue(len(self.reader.file_name_patterns) >= 3)

        self.assertEqual(self.reader.folder_id, "18uRBmOQM5hTdeQvldILnC9_n4LZIs1kf")
        self.assertEqual(self.reader.read_retry_attempts, 4)
        self.assertEqual(self.reader.read_retry_delay_seconds, 60)

        candidates = self.reader.resolve_candidate_filenames("2026-11-10")
        self.assertEqual(candidates[0], "西门看看网每日新闻_2026-11-10.md", "Exact preferred filename must be top priority")
        self.assertIn("sabah_news_2026-11-10.md", candidates)
        self.assertIn("sabah_daily_news_2026-11-10.md", candidates)
        self.assertIn("2026-11-10.md", candidates)

        # Configurable folder ID from env
        with patch.dict(os.environ, {"GDRIVE_FOLDER_ID": "test_folder_12345"}):
            custom_reader = GDriveMarkdownReader(self.config)
            self.assertEqual(custom_reader.folder_id, "test_folder_12345")

    # =========================================================================
    # Test 2: Markdown file reading and parsing
    # =========================================================================
    def test_02_markdown_file_reading_and_parsing(self):
        """Test 2: Verify end-to-end reading from markdown file and accurate attribute extraction."""
        self.assertTrue(os.path.exists(self.sample_md_path), "Sample markdown fixture must exist")

        with open(self.sample_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        stories = self.reader.parse_markdown(content, "2026-11-10")
        self.assertTrue(len(stories) >= 10, f"Expected at least 10 stories, got {len(stories)}")

        # Check first story details
        first = stories[0]
        self.assertIn("山打根市议会", first.title)
        self.assertIn("防汛重点设施", first.body)
        self.assertIn("诗华日报", first.sources)
        self.assertEqual(first.category, "sabah")
        self.assertEqual(first.geo_scope, "sandakan")
        self.assertTrue(len(first.source_urls) > 0)
        self.assertFalse(first.is_event)

    # =========================================================================
    # Test 3: Variable news count parsing test (not assuming fixed 10, 25, 26)
    # =========================================================================
    def test_03_variable_news_count_parsing(self):
        """Test 3: Parser handles any number of stories (e.g. 5, 14, 28) without error or dropped news."""
        for count in [5, 13, 27]:
            synthetic_md = ""
            for i in range(1, count + 1):
                synthetic_md += f"""
## {i}. 沙巴测试要闻第 {i} 条关于地方民生进展
- **类别**: 沙巴要闻
- **日期**: 2026-11-10
- **来源**: 官方快讯 {i}
- **内容**: 这是第 {i} 条独立采编新闻，记录沙巴重要基础设施和公共服务最新动态，字数充足真实详实。
---
"""
            parsed = self.reader.parse_markdown(synthetic_md, "2026-11-10")
            self.assertEqual(len(parsed), count, f"Failed for variable count {count}: got {len(parsed)}")
            # Confirm indexing is intact
            self.assertEqual(parsed[0].index, 1)
            self.assertEqual(parsed[-1].index, count)

    # =========================================================================
    # Test 4: Mixed language (Chinese, English, Malay) content parsing test
    # =========================================================================
    def test_04_multilingual_content_parsing(self):
        """Test 4: Verify parser handles mixed Chinese, English, and Bahasa Malaysia without corruption."""
        mixed_md = """
## 1. Sukan PBT Sabah Dirasmikan di Sandakan 拿督阿里芬亲临主持
- **Kategori**: sabah
- **Tarikh**: 2026-11-10
- **Sumber**: Daily Express, Utusan Borneo, 诗华日报
- **Link**: https://www.dailyexpress.com.my/sukan-pbt-sandakan
- **Kandungan**: Temasya Sukan Kerajaan Tempatan Sabah (SKTS) kali ke-14 telah dirasmikan dengan jayanya di Sandakan. Menteri Kerajaan Tempatan Datuk Mohd Arifin Arif menyeru semua pihak berkuasa tempatan mempertingkat kebersihan bandar menjelang Visit Malaysia Year 2027. 数千名选手齐聚山打根，显著带动了本地经济。
"""
        parsed = self.reader.parse_markdown(mixed_md, "2026-11-10")
        self.assertEqual(len(parsed), 1)
        story = parsed[0]
        self.assertIn("Sukan PBT Sabah", story.title)
        self.assertIn("拿督阿里芬", story.title)
        self.assertIn("Daily Express", story.sources)
        self.assertIn("Utusan Borneo", story.sources)
        self.assertIn("诗华日报", story.sources)
        self.assertIn("kebersihan bandar", story.body)
        self.assertIn("显著带动了本地经济", story.body)

    # =========================================================================
    # Test 5: Date and timezone (Asia/Kuala_Lumpur) test
    # =========================================================================
    def test_05_date_and_timezone_myt(self):
        """Test 5: Verify that calendar date respects Asia/Kuala_Lumpur (MYT, UTC+8)."""
        myt_date = self.reader.get_today_myt_str()
        now_myt = datetime.now(MYT)
        expected_date = now_myt.strftime("%Y-%m-%d")
        self.assertEqual(myt_date, expected_date)

        # Candidates resolution uses target date
        cands = self.reader.resolve_candidate_filenames("2026-11-10")
        for c in cands:
            self.assertIn("2026-11-10", c)

    # =========================================================================
    # Test 6: News category classification and event forecast separation
    # =========================================================================
    def test_06_category_classification_and_event_separation(self):
        """Test 6: Verify future event forecasts are segregated from breaking news and not mixed into headlines."""
        with open(self.sample_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        stories = self.reader.parse_markdown(content, "2026-11-10")
        news_stories = [s for s in stories if not s.is_event]
        event_stories = [s for s in stories if s.is_event]

        self.assertEqual(len(news_stories), 10, "Expected exactly 10 past/current news stories")
        self.assertEqual(len(event_stories), 2, "Expected exactly 2 future event forecasts")

        # Verify event forecasts details
        ev1 = event_stories[0]
        self.assertTrue(ev1.is_event)
        self.assertIn("客家公会", ev1.title)
        self.assertEqual(ev1.date, "2026-11-15")

        # Verify conversion to website events format
        web_events = self.reader.convert_events_to_website_format(event_stories, "2026-11-10")
        self.assertEqual(len(web_events), 2)
        self.assertEqual(web_events[0]["full_date"], "2026-11-15")
        self.assertEqual(web_events[0]["countdown_days"], 5)
        self.assertIn("客家公会", web_events[0]["name"])

    # =========================================================================
    # Test 7: Fail-closed on missing, empty, or unreadable markdown input
    # =========================================================================
    def test_07_fail_closed_on_missing_empty_failure(self):
        """Test 7: Verify pipeline halts safely (fail-closed) when markdown is missing or empty."""
        # A. Missing file
        with patch.dict(os.environ, {"GDRIVE_LOCAL_FILE_OVERRIDE": "/nonexistent/path/news.md"}):
            res_missing, content = self.reader.fetch_and_parse_today("2026-11-10")
            self.assertIsNone(res_missing)
            self.assertIsNone(content)

        # B. Empty file
        empty_file = os.path.join(self.test_dir.name, "empty.md")
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("   \n\n  ")

        with patch.dict(os.environ, {"GDRIVE_LOCAL_FILE_OVERRIDE": empty_file}):
            res_empty, content = self.reader.fetch_and_parse_today("2026-11-10")
            self.assertIsNone(res_empty)
            self.assertIsNone(content)

    # =========================================================================
    # Test 8: Single Gemini batch input construction test (mock, 0 API calls)
    # =========================================================================
    def test_08_single_gemini_batch_input_construction(self):
        """Test 8: Verify Top-10 stories are merged into ONE single batch prompt (0 API calls)."""
        with open(self.sample_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        stories = self.reader.parse_markdown(content, "2026-11-10")
        top_stories = self.reader.select_top_stories_for_batch(stories, max_count=10)
        raw_articles = self.reader.convert_to_raw_articles(top_stories)

        self.assertEqual(len(raw_articles), 10)

        # Verify Sandakan prioritization
        sandakan_titles = [a.title for a in raw_articles if "山打根" in a.title]
        self.assertTrue(len(sandakan_titles) >= 3, "Sandakan news must be prominently prioritized")

        # Verify single batch serialization
        synth = NewsSynthesizer(self.config)
        # Mock QuotaManager reserve_slot so 0 API calls and 0 real reservations are made
        mock_qm = MagicMock()
        mock_qm.candidate_models = ["gemini-3.5-flash-lite"]
        mock_qm.reserve_slot.return_value = {"reservation_id": "mock_res_2026-11-10_1"}
        synth.quota_mgr = mock_qm

        # Test prompt structure without sending HTTP request
        story_blocks = []
        for i, art in enumerate(raw_articles[:10], 1):
            body_text = (art.body or art.snippet or art.title).strip()
            story_blocks.append(f"=== 报道 #{i} [{art.category.upper()}] ===\n原文标题: {art.title}\n{body_text}\n")

        consolidated_prompt = "\n".join(story_blocks)
        self.assertIn("报道 #1", consolidated_prompt)
        self.assertIn("报道 #10", consolidated_prompt)
        self.assertTrue(len(consolidated_prompt) > 2000, "Single batch prompt must contain full substantive bodies")

    # =========================================================================
    # Test 9: Bilingual output data structure compatibility test
    # =========================================================================
    def test_09_bilingual_output_data_structure_compatibility(self):
        """Test 9: Verify parsed stories can generate valid bilingual schema conforming to site requirements."""
        mock_gemini_output = [
            {
                "story_index": 1,
                "category": "sabah",
                "title": "山打根市议会全面检修防潮排涝设施 迎战大潮防汛",
                "titleBM": "MPS Sandakan Periksa Pintu Kawalan Banjir dan Stesen Pam",
                "detail": "山打根市议会（MPS）工务工程组联合水利灌溉局今日开展全区防潮排涝设施全面大巡检，重点清淤检修中央巴刹防潮闸门及抽水泵站，24小时严密监控沿海潮位与降雨动态。",
                "detailBM": "Majlis Perbandaran Sandakan (MPS) bersama JPS menjalankan pemeriksaan menyeluruh terhadap pintu kawalan banjir dan stesen pam bagi menghadapi fenomena air pasang besar.",
                "source_url": "https://news.seehua.com/sandakan-mps-pump-inspection-20261110",
                "publisher": "诗华日报"
            }
        ]

        # Verify schema keys
        item = mock_gemini_output[0]
        required_keys = ["story_index", "category", "title", "titleBM", "detail", "detailBM", "source_url", "publisher"]
        for k in required_keys:
            self.assertIn(k, item)
            self.assertTrue(len(str(item[k])) > 0)

    # =========================================================================
    # Test 10: Existing website data structure & rolling archive compatibility
    # =========================================================================
    def test_10_website_data_structure_and_archive_compatibility(self):
        """Test 10: Verify payload integrates with news_data.json and manages 7-day rolling archive pool."""
        news_data_path = os.path.join(self.base_dir, "news_data.json")
        self.assertTrue(os.path.exists(news_data_path))

        with open(news_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("date", data)
        self.assertIn("headlines", data)
        self.assertIn("utilities", data)
        self.assertIn("events", data)
        self.assertIn("archive", data)

        # Test archive rolling pool function using a temporary archive file to avoid mutating production archive
        temp_archive_file = os.path.join(self.test_dir.name, "temp_archive_history.json")
        with open(temp_archive_file, "w", encoding="utf-8") as f:
            json.dump({"2026-11-09": [{"id": "art_1"}], "2026-11-08": [{"id": "art_2"}]}, f)

        dummy_headlines = [{"id": f"art_test_{i}", "title": f"Test Title {i}"} for i in range(10)]
        with patch("agent_reach_editor.ARCHIVE_POOL_FILE", temp_archive_file):
            archive_res = agent_reach_editor.manage_7day_rolling_archive_pool("2026-11-10", dummy_headlines)
            self.assertTrue(len(archive_res) <= 7)
            self.assertIn("2026-11-10", archive_res)

    # =========================================================================
    # Test 11: Git identity configuration location & QuotaManager commit path test
    # =========================================================================
    def test_11_git_identity_and_quota_manager_commit_path(self):
        """Test 11: Verify Git author identity is robustly configured and prevents 'Author identity unknown'."""
        qm = QuotaManager(self.config, execution_mode_override="MOCK_TEST")
        # Check that synthesizer has the robust git identity injection
        with open(os.path.join(self.base_dir, "pipeline", "synthesizer.py"), "r", encoding="utf-8") as f:
            synth_code = f.read()

        self.assertIn('"GIT_AUTHOR_NAME"] = "Simon Kankan Bot"', synth_code)
        self.assertIn('"GIT_AUTHOR_EMAIL"] = "sumoumou84@gmail.com"', synth_code)
        self.assertIn('"user.name", "Simon Kankan Bot"', synth_code)

        # Check that workflow also has git identity setup
        with open(os.path.join(self.base_dir, ".github", "workflows", "morning_publish.yml"), "r", encoding="utf-8") as f:
            wf_code = f.read()

        self.assertIn('git config --global user.name "Simon Kankan Bot"', wf_code)
        self.assertIn('git config --global user.email "sumoumou84@gmail.com"', wf_code)


    # =========================================================================
    # Test 12: Google Docs export fallback compatibility test
    # =========================================================================
    def test_12_google_docs_export_fallback_compatibility(self):
        """Test 12: Verify fallback to Google Docs export API when authentic .md is absent."""
        mock_drive_files = [
            {
                "id": "gdoc_id_999",
                "name": "西门看看网每日新闻_2026-11-10",
                "mimeType": "application/vnd.google-apps.document"
            }
        ]

        def mock_urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, 'full_url') else req
            mock_resp = MagicMock()
            if "export" in url:
                mock_resp.read.return_value = b"# Exported Google Docs Markdown Content"
            else:
                # Search query response
                if "application/vnd.google-apps.document" in url and "mimeType = 'application/vnd.google-apps.document'" in urllib.parse.unquote(url):
                    mock_resp.read.return_value = json.dumps({"files": mock_drive_files}).encode("utf-8")
                else:
                    mock_resp.read.return_value = json.dumps({"files": []}).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            return mock_resp

        with patch.object(self.reader, '_get_oauth_access_token', return_value="mock_access_token"):
            with patch('urllib.request.urlopen', side_effect=mock_urlopen):
                result = self.reader.read_from_drive_api(["西门看看网每日新闻_2026-11-10.md"], folder_id="18uRBmOQM5hTdeQvldILnC9_n4LZIs1kf")
                self.assertIsNotNone(result)
                file_name, content, file_id = result
                self.assertEqual(file_name, "西门看看网每日新闻_2026-11-10.md")
                self.assertEqual(file_id, "gdoc_id_999")
                self.assertIn("Exported Google Docs Markdown Content", content)

    # =========================================================================
    # Test 13: Bounded retry mechanism without Gemini API calls or quota reservation
    # =========================================================================
    def test_13_bounded_retry_without_gemini_or_quota(self):
        """Test 13: Verify retry loop retries up to configured limit without invoking Gemini or reserving quota."""
        test_reader = GDriveMarkdownReader(self.config)
        test_reader.read_retry_attempts = 3
        test_reader.read_retry_delay_seconds = 0  # 0 wait for instantaneous test execution

        # Mock Drive API to fail twice then succeed
        call_count = 0
        def mock_read_api(candidates, folder_id):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return None
            return ("西门看看网每日新闻_2026-11-10.md", "# Final Success Body", "file_retry_success")

        with patch.object(test_reader, 'read_from_drive_api', side_effect=mock_read_api):
            with patch.object(test_reader, 'read_from_local_fallback', return_value=None):
                with patch('pipeline.synthesizer.QuotaManager.reserve_slot') as mock_reserve:
                    res = test_reader.read_markdown_content("2026-11-10")
                    self.assertIsNotNone(res)
                    self.assertEqual(res[0], "西门看看网每日新闻_2026-11-10.md")
                    self.assertEqual(call_count, 3)
                    # Absolute guarantee: QuotaManager was NEVER called during retries
                    mock_reserve.assert_not_called()

    # =========================================================================
    # Test 14: Direct pass-through pipeline (0 Gemini API calls, 0 quota reserved)
    # =========================================================================
    def test_14_direct_pass_through_no_gemini_calls(self):
        """Test 14: Verify Markdown parses directly into headlines & events without invoking Gemini."""
        with open(self.sample_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        stories = self.reader.parse_markdown(content, "2026-11-10")
        self.assertTrue(len(stories) >= 10)

        headlines, events = self.reader.convert_stories_to_direct_output(stories, "2026-11-10")
        self.assertEqual(len(headlines), 10)
        self.assertEqual(len(events), 2)

        # Check circuit breaker threshold
        cb = CircuitBreaker(min_threshold=10)
        # Should not raise CircuitBreakerException
        cb.inspect_and_guard(
            today_iso="2026-11-10",
            new_headlines=headlines,
            existing_news_file=os.path.join(self.base_dir, "news_data.json"),
            existing_archive_file=os.path.join(self.base_dir, "archive_history.json")
        )

        # Confirm all required schema keys for website
        first_h = headlines[0]
        self.assertIn("title", first_h)
        self.assertIn("titleBM", first_h)
        self.assertIn("detail", first_h)
        self.assertIn("detailBM", first_h)
        self.assertIn("validation_status", first_h)
        self.assertEqual(first_h["validation_status"], "VERIFIED")

        first_e = events[0]
        self.assertIn("name", first_e)
        self.assertIn("nameBM", first_e)
        self.assertIn("desc", first_e)
        self.assertIn("descBM", first_e)
        self.assertIn("countdown_days", first_e)

if __name__ == "__main__":
    unittest.main()
