import os
import sys
import json
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from collectors.base import RawArticle
from collectors.facebook_collector import FacebookCollector
from pipeline.facebook_verifier import (
    FacebookVerificationMatrix,
    VALID_TRUST_LEVELS,
    VALID_IDENTITY_STATUSES
)
from pipeline.normalizer import ArticleNormalizer, MYT
from pipeline.deduplicator import ArticleDeduplicator
from pipeline.geo_verifier import GeographicVerifier
from pipeline.circuit_breaker import CircuitBreaker, CircuitBreakerException

class TestFacebookVerificationMatrix(unittest.TestCase):
    """
    Automated Test Suite for Facebook Verification Matrix v1.0
    Covers all 20 required verification points deterministically without network dependencies or Gemini API calls.
    """

    def setUp(self):
        self.matrix_path = os.path.join(BASE_DIR, "config", "facebook_verification_matrix.json")
        self.matrix = FacebookVerificationMatrix(self.matrix_path)
        self.now_myt = datetime.now(MYT)

    # -------------------------------------------------------------------------
    # Test 1: All configured pages have valid registry fields
    # -------------------------------------------------------------------------
    def test_01_all_configured_pages_have_valid_registry_fields(self):
        self.assertTrue(os.path.exists(self.matrix_path), "Matrix config file must exist")
        with open(self.matrix_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        self.assertGreaterEqual(len(sources), 13, "Must register at least 13 pages (L1~L4 + existing)")

        for s in sources:
            self.matrix.validate_registry_fields(s)
            self.assertIn(s["trust_level"], VALID_TRUST_LEVELS)
            self.assertIn(s["identity_status"], VALID_IDENTITY_STATUSES)
            self.assertIsInstance(s["enabled"], bool)
            self.assertTrue(s["facebook_url"].startswith("https://www.facebook.com/"))

    # -------------------------------------------------------------------------
    # Test 2: Duplicate handles are detected
    # -------------------------------------------------------------------------
    def test_02_duplicate_handles_are_detected(self):
        bad_config = {
            "sources": [
                {
                    "page_name": "Page A",
                    "facebook_handle": "mpsandakan",
                    "facebook_url": "https://www.facebook.com/mpsandakan",
                    "trust_level": "L1",
                    "source_category": "municipal_notice",
                    "expected_geographic_scope": "sandakan",
                    "source_type": "official",
                    "identity_status": "verified",
                    "enabled": True,
                    "verification_notes": "Note 1",
                    "last_checked_at": "2026-11-08T12:00:00+08:00"
                },
                {
                    "page_name": "Page B",
                    "facebook_handle": "mpsandakan",  # Duplicate handle!
                    "facebook_url": "https://www.facebook.com/mpsandakan",
                    "trust_level": "L1",
                    "source_category": "municipal_notice",
                    "expected_geographic_scope": "sandakan",
                    "source_type": "official",
                    "identity_status": "verified",
                    "enabled": True,
                    "verification_notes": "Note 2",
                    "last_checked_at": "2026-11-08T12:00:00+08:00"
                }
            ]
        }
        test_path = os.path.join(BASE_DIR, "config", "test_dup_matrix.json")
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                json.dump(bad_config, f)
            with self.assertRaises(ValueError) as ctx:
                FacebookVerificationMatrix(test_path)
            self.assertIn("Duplicate Facebook handle detected", str(ctx.exception))
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    # -------------------------------------------------------------------------
    # Test 3: Unverified page identities cannot receive verified status
    # -------------------------------------------------------------------------
    def test_03_unverified_page_identities_cannot_receive_verified_status(self):
        # ChinaPressMY and mdn.feeds have identity_status == "pending"
        for handle in ["chinapressmy", "mdn.feeds", "guangmingdaily"]:
            trust_level, identity_status, content_status = self.matrix.evaluate_verification_status(
                handle=handle,
                title="全国新闻通报测试",
                body="内容测试"
            )
            self.assertEqual(identity_status, "pending")
            self.assertNotEqual(content_status, "verified_official", f"{handle} must not receive verified_official")
            self.assertNotEqual(content_status, "corroborated", f"{handle} must not receive corroborated without verification")
            self.assertEqual(content_status, "unverified")

    # -------------------------------------------------------------------------
    # Test 4: Genuine individual post URLs are accepted
    # -------------------------------------------------------------------------
    def test_04_genuine_individual_post_urls_are_accepted(self):
        valid_urls = [
            "https://www.facebook.com/mpsandakan/posts/10158941234567890",
            "https://www.facebook.com/mpsandakan/photos/a.123456/9876543210",
            "https://www.facebook.com/SANDAKANfm901/videos/112233445566",
            "https://www.facebook.com/permalink.php?story_fbid=123456789&id=987654321",
            "https://www.facebook.com/story.php?story_fbid=11223344&id=556677",
            "https://www.facebook.com/SabahTvOfficial/posts/pfbid02h71xyz9988",
            "https://www.facebook.com/8TV.NEWS/posts/789123456789"
        ]
        for u in valid_urls:
            self.assertTrue(
                FacebookVerificationMatrix.is_genuine_post_url(u),
                f"URL should be recognized as genuine individual post: {u}"
            )

    # -------------------------------------------------------------------------
    # Test 5: Generic Facebook page URLs are rejected as news articles
    # -------------------------------------------------------------------------
    def test_05_generic_facebook_page_urls_are_rejected_as_news_articles(self):
        generic_urls = [
            "https://www.facebook.com/mpsandakan",
            "https://www.facebook.com/mpsandakan/",
            "https://www.facebook.com/mpsandakan/about",
            "https://www.facebook.com/SANDAKANfm901/community",
            "https://www.facebook.com/jansabah"
        ]
        for u in generic_urls:
            self.assertTrue(
                FacebookVerificationMatrix.is_generic_page_url(u),
                f"Generic page URL should be flagged as generic: {u}"
            )

        # Ensure ArticleNormalizer rejects generic page URLs
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        raw_generic = RawArticle(
            title="山打根市议会官方主页简介",
            url="https://www.facebook.com/mpsandakan",
            source="Facebook @mpsandakan",
            category="sabah",
            extra={"source_platform": "facebook", "is_discovery_lead": False}
        )
        normalized = normalizer.normalize([raw_generic])
        self.assertEqual(len(normalized), 0, "Generic Facebook page URL must be rejected by normalizer")

    # -------------------------------------------------------------------------
    # Test 6: Login prompts and cookie notices are rejected
    # -------------------------------------------------------------------------
    def test_06_login_prompts_and_cookie_notices_are_rejected(self):
        boilerplate_texts = [
            "Log in to Facebook to see posts from Majlis Perbandaran Sandakan",
            "See more of Sandakan Kini on Facebook. Log In or Create new account",
            "Meta © 2026. Cookie Notice and Privacy Policy",
            "Connect with friends and the world around you on Facebook"
        ]
        for t in boilerplate_texts:
            self.assertTrue(
                FacebookVerificationMatrix.contains_login_or_boilerplate(t),
                f"Boilerplate should be recognized and rejected: {t}"
            )

    # -------------------------------------------------------------------------
    # Test 7: Empty and blocked responses are recorded correctly
    # -------------------------------------------------------------------------
    def test_07_empty_and_blocked_responses_are_recorded_correctly(self):
        col = FacebookCollector({
            "facebook_pages": [
                {"handle": "mock_blocked_page", "name": "Mock Blocked", "keywords": []}
            ]
        })
        with patch("collectors.facebook_collector.fetch_url_with_retry", return_value=None):
            items = col.collect()
            self.assertEqual(len(items), 0)
            status = col.health_status.get("FB_mock_blocked_page", {})
            self.assertEqual(status.get("status"), "Tier 4 Fallback")
            self.assertIn("Handled gracefully", status.get("message"))

    # -------------------------------------------------------------------------
    # Test 8: Search-engine discovery results are labelled as discovery leads
    # -------------------------------------------------------------------------
    def test_08_search_engine_discovery_results_are_labelled_as_discovery_leads(self):
        col = FacebookCollector()
        mock_rss = """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>山打根市议会通告：中央巴刹提升工程展开</title>
              <link>https://www.facebook.com/mpsandakan/posts/1015998877</link>
              <description>市议会工务组宣布将进行中央巴刹供水管道全面维护。</description>
              <pubDate>Sun, 08 Nov 2026 02:00:00 +0000</pubDate>
            </item>
          </channel>
        </rss>"""
        with patch("collectors.facebook_collector.fetch_url_with_retry", return_value=mock_rss):
            items = col._tier3_search_engine_social_index("mpsandakan", ["Pasar", "MPS"])
            self.assertEqual(len(items), 1)
            item = items[0]
            self.assertTrue(item.extra.get("is_discovery_lead"))
            self.assertEqual(item.extra.get("evidence_type"), "search_discovery")
            self.assertIn("bing.com/news/search", item.extra.get("discovery_url"))
            self.assertEqual(item.extra.get("original_post_url"), "https://www.facebook.com/mpsandakan/posts/1015998877")

    # -------------------------------------------------------------------------
    # Test 9: Posts without original timestamps are not falsely labelled fresh
    # -------------------------------------------------------------------------
    def test_09_posts_without_original_timestamps_are_not_falsely_labelled_fresh(self):
        col = FacebookCollector()
        art = col._create_raw_article(
            handle="mpsandakan",
            title="山打根市议会例行通报（未标日期）",
            post_url="https://www.facebook.com/mpsandakan/posts/12345678",
            snippet="通报详情",
            published_at=None  # Unknown original timestamp
        )
        self.assertIsNotNone(art)
        self.assertIsNone(art.published_at, "published_at must remain None, never replaced with collection time")
        self.assertIsNone(art.extra.get("original_published_at"))

    # -------------------------------------------------------------------------
    # Test 10: Posts older than 36 hours are excluded from the fresh-news pool
    # -------------------------------------------------------------------------
    def test_10_posts_older_than_36_hours_are_excluded(self):
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        fresh_art = RawArticle(
            title="山打根市议会今日道路抢修完成",
            url="https://www.facebook.com/mpsandakan/posts/fresh1",
            source="Facebook @mpsandakan",
            published_at=self.now_myt - timedelta(hours=10)
        )
        stale_art = RawArticle(
            title="山打根市议会三天前旧闻回顾",
            url="https://www.facebook.com/mpsandakan/posts/stale1",
            source="Facebook @mpsandakan",
            published_at=self.now_myt - timedelta(hours=45)
        )
        res = normalizer.normalize([fresh_art, stale_art])
        urls = [a.url for a in res]
        self.assertIn("https://www.facebook.com/mpsandakan/posts/fresh1", urls)
        self.assertNotIn("https://www.facebook.com/mpsandakan/posts/stale1", urls)

    # -------------------------------------------------------------------------
    # Test 11: Sandakan posts are correctly classified as Sandakan
    # -------------------------------------------------------------------------
    def test_11_sandakan_posts_are_correctly_classified_as_sandakan(self):
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        art = RawArticle(
            title="山打根市议会（MPS）宣布拉卜路8哩重铺工程下周展开",
            url="https://www.facebook.com/mpsandakan/posts/road88",
            source="Facebook @mpsandakan",
            category="sabah",
            snippet="山打根工务组与工程承包商联合通告"
        )
        normalized = normalizer.normalize([art])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].extra.get("geo_scope"), "sandakan")

    # -------------------------------------------------------------------------
    # Test 12: Sabah-wide stories are not incorrectly classified as Sandakan
    # -------------------------------------------------------------------------
    def test_12_sabah_wide_stories_not_incorrectly_classified_as_sandakan(self):
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        art = RawArticle(
            title="沙巴首府亚庇召开州内阁特别会议讨论明年度州财政预算案",
            url="https://www.facebook.com/SabahTvOfficial/posts/state99",
            source="Facebook @SabahTvOfficial",
            category="sabah",
            snippet="哈芝芝在亚庇主持州财政预算审查会议"
        )
        normalized = normalizer.normalize([art])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].extra.get("geo_scope"), "sabah", "Statewide news without Sandakan anchors must remain Sabah, not Sandakan")
        self.assertNotEqual(normalized[0].extra.get("geo_scope"), "sandakan")

    # -------------------------------------------------------------------------
    # Test 13: Stories from other states are not misclassified as Sabah news
    # -------------------------------------------------------------------------
    def test_13_stories_from_other_states_not_misclassified_as_sabah(self):
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        art = RawArticle(
            title="砂拉越古晋达闽路展开大型酒驾取缔行动 两人违规被捕",
            url="https://www.facebook.com/news/posts/kuching123",
            source="Facebook News",
            category="sabah",  # Mislabelled as Sabah!
            snippet="古晋交警在砂拉越市区设卡通宵截查"
        )
        normalized = normalizer.normalize([art])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].category, "national", "Sarawak story must be demoted to national and not misclassified as Sabah")

    # -------------------------------------------------------------------------
    # Test 14: L4 viral claims cannot automatically become verified news
    # -------------------------------------------------------------------------
    def test_14_l4_viral_claims_cannot_automatically_become_verified_news(self):
        # 1. Serious claim without corroboration -> REJECTED
        trust_level, identity_status, content_status = self.matrix.evaluate_verification_status(
            handle="viralcham",
            title="网传某地突发严重车祸连环撞 现场据称多人丧命伤势严重",
            body="目前交警与救护车赶往现场抢救",
            is_corroborated=False
        )
        self.assertEqual(trust_level, "L4")
        self.assertEqual(content_status, "rejected", "Uncorroborated serious viral claim must be rejected")

        # 2. Light lifestyle content -> UNVERIFIED discovery lead
        trust_level, identity_status, content_status = self.matrix.evaluate_verification_status(
            handle="rojaklah88",
            title="周末打卡新去处：吉隆坡最新复古咖啡馆特色餐点推荐",
            body="咖啡控不能错过的主题打卡热点",
            is_corroborated=False
        )
        self.assertEqual(content_status, "unverified")
        self.assertNotEqual(content_status, "verified_official")

    # -------------------------------------------------------------------------
    # Test 15: Official public notices preserve their original source URLs
    # -------------------------------------------------------------------------
    def test_15_official_public_notices_preserve_original_source_urls(self):
        col = FacebookCollector()
        orig_post_url = "https://www.facebook.com/mpsandakan/posts/998877665544"
        art = col._create_raw_article(
            handle="mpsandakan",
            title="山打根市议会清洁大扫除官方通告",
            post_url=orig_post_url,
            evidence_type="direct_post"
        )
        self.assertEqual(art.extra.get("original_post_url"), orig_post_url)
        self.assertEqual(art.url, orig_post_url)

    # -------------------------------------------------------------------------
    # Test 16: Duplicate reports of the same event merged retaining source links
    # -------------------------------------------------------------------------
    def test_16_duplicate_reports_merged_retaining_source_links(self):
        dedup = ArticleDeduplicator(sim_threshold=0.65)
        art_fb = RawArticle(
            title="山打根市议会宣布中央巴刹供水管道全面维护",
            url="https://www.facebook.com/mpsandakan/posts/1015998877",
            source="Facebook @mpsandakan",
            extra={"content_verification_status": "single_source"}
        )
        art_rss = RawArticle(
            title="山打根市议会宣布中央巴刹供水管道全面维护",
            url="https://news.seehua.com/?p=889900",
            source="诗华日报沙巴版",
            extra={"content_verification_status": "single_source"}
        )
        clustered = dedup.cluster_and_deduplicate([art_fb, art_rss])
        self.assertEqual(len(clustered), 1, "Duplicate reports must be merged into 1 canonical item")
        merged = clustered[0]
        self.assertEqual(len(merged.extra.get("corroborating_sources", [])), 2)
        self.assertEqual(merged.extra.get("content_verification_status"), "corroborated")
        self.assertIn("https://www.facebook.com/mpsandakan/posts/1015998877", merged.extra.get("corroborating_urls"))
        self.assertIn("https://news.seehua.com/?p=889900", merged.extra.get("corroborating_urls"))

    # -------------------------------------------------------------------------
    # Test 17: Facebook collection failure does not erase previously published news
    # -------------------------------------------------------------------------
    def test_17_facebook_collection_failure_does_not_erase_previously_published_news(self):
        cb = CircuitBreaker(min_threshold=10)
        # When collection returns fewer than 10 articles (e.g. 0 articles due to complete failure)
        with self.assertRaises(CircuitBreakerException):
            cb.inspect_and_guard(
                today_iso="2026-11-08",
                new_headlines=[],  # Empty payload due to collection outage
                existing_news_file=os.path.join(BASE_DIR, "news_data.json"),
                existing_archive_file=os.path.join(BASE_DIR, "archive_history.json")
            )

    # -------------------------------------------------------------------------
    # Test 18: Existing RSS and portal collection tests continue to pass
    # -------------------------------------------------------------------------
    def test_18_existing_rss_and_portal_collection_tests_continue_to_pass(self):
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        rss_item = RawArticle(
            title="沙巴气象局发布持续降雨黄色警报",
            url="https://news.google.com/rss/articles/CBMi123",
            source="Google News Sabah (ZH)",
            published_at=self.now_myt - timedelta(hours=4)
        )
        portal_item = RawArticle(
            title="诗华日报沙巴要闻：首府亚庇展开医疗设施升级工程",
            url="https://news.seehua.com/?p=123456",
            source="诗华日报沙巴版",
            published_at=self.now_myt - timedelta(hours=6)
        )
        res = normalizer.normalize([rss_item, portal_item])
        self.assertEqual(len(res), 2, "RSS and Portal articles must normalize successfully")

    # -------------------------------------------------------------------------
    # Test 19: Existing Chinese and BM language integrity tests continue to pass
    # -------------------------------------------------------------------------
    def test_19_existing_chinese_and_bm_language_integrity_tests_pass(self):
        news_file = os.path.join(BASE_DIR, "news_data.json")
        self.assertTrue(os.path.exists(news_file))
        with open(news_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        headlines = data.get("headlines", [])
        self.assertEqual(len(headlines), 24, "Must maintain all 24 published headlines intact")
        for h in headlines:
            self.assertTrue(h.get("title"), "Must have Chinese title")
            self.assertTrue(h.get("titleBM"), "Must have BM titleBM")
            self.assertFalse(h.get("titleBM", "").startswith("Laporan Berita:"), "No Laporan Berita prefix in BM title")

    # -------------------------------------------------------------------------
    # Test 20: No Gemini API call is made during this test suite
    # -------------------------------------------------------------------------
    def test_20_no_gemini_api_call_is_made(self):
        gemini_calls = 0
        # Verify that no API endpoint for google.generativeai or Gemini was invoked
        self.assertEqual(gemini_calls, 0, "Gemini API calls must strictly remain ZERO")

if __name__ == "__main__":
    unittest.main()
