import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from collectors.base import RawArticle, fetch_url_with_retry
from collectors.facebook_collector import FacebookCollector
from pipeline.normalizer import ArticleNormalizer, MYT
from pipeline.deduplicator import ArticleDeduplicator
from pipeline.synthesizer import NewsSynthesizer
from pipeline.circuit_breaker import CircuitBreaker, CircuitBreakerException

class TestPipelineResilience(unittest.TestCase):

    def setUp(self):
        self.now_myt = datetime.now(MYT)

    # -------------------------------------------------------------
    # Test 1: Single & Multi-source Network Failure / Timeout
    # -------------------------------------------------------------
    def test_01_network_timeout_and_failure_resilience(self):
        """Invalid or non-existent URLs should be caught gracefully without crashing."""
        res = fetch_url_with_retry("http://127.0.0.1:59999/non-existent", timeout=1, max_retries=1)
        self.assertIsNone(res, "Invalid URL should return None gracefully")

    # -------------------------------------------------------------
    # Test 2: Facebook 4-Tier Fallback Cascade
    # -------------------------------------------------------------
    def test_02_facebook_4tier_fallback(self):
        """Facebook collector must cascade through tiers and never raise uncaught exceptions."""
        config = {
            "facebook_pages": [
                {"handle": "mpsandakan_test_mock", "keywords": ["Sandakan", "MPS"]}
            ]
        }
        fb_col = FacebookCollector(config)
        items = fb_col.collect()
        self.assertIsInstance(items, list, "Facebook collect must return a list")
        self.assertEqual(fb_col.health_status["status"], "completed")

    # -------------------------------------------------------------
    # Test 3: Date Normalization with 36-Hour Sliding Window
    # -------------------------------------------------------------
    def test_03_sliding_window_filtering(self):
        """Normalizer should retain 24h-old news (e.g. yesterday evening) while discarding 48h-old news."""
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        
        art_fresh = RawArticle(
            title="沙巴气象局发布最新暴雨预警通告",
            url="https://example.com/fresh-news",
            source="Test Source",
            published_at=self.now_myt - timedelta(hours=14)  # 14 hours ago (yesterday evening)
        )
        art_stale = RawArticle(
            title="历史旧闻事件回顾测试",
            url="https://example.com/stale-news",
            source="Test Source",
            published_at=self.now_myt - timedelta(hours=50)  # 50 hours ago (beyond 36h)
        )
        art_undated = RawArticle(
            title="门户首页未标日期的即时新闻",
            url="https://example.com/undated-news",
            source="Test Source",
            published_at=None  # Frontpage live
        )

        filtered = normalizer.normalize([art_fresh, art_stale, art_undated])
        urls = [a.url for a in filtered]
        self.assertIn("https://example.com/fresh-news", urls, "Fresh 14h article must be retained")
        self.assertIn("https://example.com/undated-news", urls, "Undated frontpage article must be retained")
        self.assertNotIn("https://example.com/stale-news", urls, "Stale 50h article must be filtered out")

    # -------------------------------------------------------------
    # Test 4: 5-Source Deduplication & URL Canonicalization
    # -------------------------------------------------------------
    def test_04_five_source_deduplication(self):
        """Articles sharing the same normalized URL or exact title must be merged into one canonical item."""
        normalizer = ArticleNormalizer(sliding_window_hours=36)
        deduplicator = ArticleDeduplicator(sim_threshold=0.65)

        raws = [
            RawArticle(title="山打根拉卜路道路重铺工程展开", url="https://example.com/road?utm_source=fb", source="Source A"),
            RawArticle(title="山打根拉卜路道路重铺工程展开", url="https://example.com/road?utm_medium=rss", source="Source B"),
            RawArticle(title="山打根拉卜路道路重铺工程展开", url="https://example.com/road?ref=share", source="Source C"),
            RawArticle(title="山打根拉卜路道路重铺工程展开", url="https://example.com/road", source="Source D"),
            RawArticle(title="山打根拉卜路道路重铺工程展开", url="https://example.com/road#section", source="Source E"),
        ]

        normalized = normalizer.normalize(raws)
        clustered = deduplicator.cluster_and_deduplicate(normalized)
        
        self.assertEqual(len(clustered), 1, "5 duplicate reports must be merged into 1 canonical item")
        sources = clustered[0].extra.get("corroborating_sources", [])
        self.assertTrue(len(sources) >= 4, f"All unique sources should be recorded: {sources}")

    # -------------------------------------------------------------
    # Test 5: Cross-Lingual Event Clustering (ZH, EN, MS)
    # -------------------------------------------------------------
    def test_05_cross_lingual_clustering(self):
        """Cross-lingual reports of the same event should cluster by entity anchors (Sandakan + Scam)."""
        deduplicator = ArticleDeduplicator(sim_threshold=0.65)

        art_zh = RawArticle(
            title="沙巴移民局在山打根突击电信诈骗窝点逮捕14人",
            url="https://example.com/zh-scam",
            source="沙巴星洲日报",
            language="zh",
            snippet="移民局特警在山打根展开行动逮捕14名涉案男女。"
        )
        art_en = RawArticle(
            title="Sabah Immigration busts online scam syndicate in Sandakan, detains 14",
            url="https://example.com/en-scam",
            source="The Star",
            language="en",
            snippet="Immigration officers detained 14 suspects in a private house in Sandakan."
        )
        art_ms = RawArticle(
            title="Jabatan Imigresen gempur sindiket penipuan di Sandakan, tahan 14 warga asing",
            url="https://example.com/ms-scam",
            source="Bernama",
            language="ms",
            snippet="Serbuan khas di Sandakan berjaya menumpaskan sindiket scam."
        )

        clustered = deduplicator.cluster_and_deduplicate([art_zh, art_en, art_ms])
        self.assertEqual(len(clustered), 1, "ZH, EN, MS reports of the 14-person scam raid should merge into 1 cluster")
        corrob = clustered[0].extra.get("corroborating_sources", [])
        self.assertEqual(len(corrob), 3, "Cluster must cite all 3 language sources")

    # -------------------------------------------------------------
    # Test 6: Track B Standalone Synthesizer (No Gemini Required)
    # -------------------------------------------------------------
    def test_06_track_b_standalone_synthesizer(self):
        """Track B synthesizer must produce fully populated news objects conforming to JSON contract."""
        synthesizer = NewsSynthesizer({})
        test_articles = [
            RawArticle(
                title="沙巴水务局斗湖古哈拉抽水主站抢修顺利完成",
                url="https://example.com/water-1",
                source="沙巴水务局",
                category="sabah",
                snippet="古哈拉抽水站故障修复，今晨全线水压恢复平稳常压。",
                extra={"corroborating_sources": ["沙巴水务局", "诗华日报"]}
            ),
            RawArticle(
                title="气象局发布沙巴季风连续降雨警报",
                url="https://example.com/weather-1",
                source="气象局",
                category="sabah",
                snippet="东北季候风带来持续强降雨，各低洼片区严密防范积水。",
                extra={"corroborating_sources": ["气象局MetMalaysia"]}
            )
        ]

        results = synthesizer.synthesize_track_b_standalone("2026-11-08", test_articles)
        self.assertEqual(len(results), 2)
        for item in results:
            self.assertIn("category", item)
            self.assertIn("title", item)
            self.assertIn("titleBM", item)
            self.assertIn("detail", item)
            self.assertIn("detailBM", item)
            self.assertIn("sources", item)
            self.assertIsNone(item["image_url"], "image_url must strictly be None")
            self.assertTrue(len(item["detail"]) > 50, "Detail text must be substantial")
            self.assertTrue(len(item["detailBM"]) > 30, "detailBM must be substantial")

    # -------------------------------------------------------------
    # Test 7: Circuit Breaker Non-Destructive Activation
    # -------------------------------------------------------------
    def test_07_circuit_breaker_protection(self):
        """Circuit breaker must raise CircuitBreakerException if article count < threshold."""
        cb = CircuitBreaker(min_threshold=10)

        # 0 articles should abort
        with self.assertRaises(CircuitBreakerException):
            cb.inspect_and_guard(
                today_iso="2026-11-08",
                new_headlines=[],
                existing_news_file="non_existent_file.json",
                existing_archive_file="non_existent_archive.json"
            )

        # 5 articles (< 10) should abort
        few_items = [{"title": f"News {i}"} for i in range(5)]
        with self.assertRaises(CircuitBreakerException):
            cb.inspect_and_guard(
                today_iso="2026-11-08",
                new_headlines=few_items,
                existing_news_file="non_existent_file.json",
                existing_archive_file="non_existent_archive.json"
            )

        # 12 articles (>= 10) should pass
        good_items = [{"title": f"News {i}"} for i in range(12)]
        res = cb.inspect_and_guard(
            today_iso="2026-11-08",
            new_headlines=good_items,
            existing_news_file="non_existent_file.json",
            existing_archive_file="non_existent_archive.json"
        )
        self.assertTrue(res, "Circuit breaker should allow >= 10 articles")

if __name__ == "__main__":
    unittest.main()
