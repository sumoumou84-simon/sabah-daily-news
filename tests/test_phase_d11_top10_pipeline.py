#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Phase D-11 Offline Test Suite:
Comprehensive tests for Daily Top-10 Single-Batch Gemini Workflow.
Tests all 12 criteria specified in Section 11:
1. Existing confirmed multi-source stories remain confirmed.
2. Existing deduplication remains intact.
3. Sandakan and Sabah stories rank highest.
4. Relevant national story qualifies.
5. Unrelated Sarawak story is excluded even with high-impact keyword.
6. Unrelated international story is excluded.
7. Routine low-value ceremony is excluded.
8. Substantive article-body retrieval is reused without downgrading confirmation.
9. One batch results in exactly one mocked Gemini dispatch.
10. No automatic retry and zero Track-B fake-news boilerplate.
11. D-7 validator rejects pseudo-BM and unanchored facts.
12. Preview execution does not modify production files.
"""

import os
import sys
import json
import hashlib
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from collectors.base import RawArticle
from pipeline.deduplicator import ArticleDeduplicator
from pipeline.normalizer import ArticleNormalizer
from pipeline.editorial_ranker import EditorialRanker
from pipeline.source_scraper import SourceScraper
from pipeline.synthesizer import NewsSynthesizer, QuotaManager
from pipeline.fact_verifier import BilingualFactValidator
from pipeline.fact_schema import HeadlineRecord, FactStatus, FactItem, FactCategory, StructuredArticle, ClaimRecord, SemanticLifecycleState

MYT = timezone(timedelta(hours=8))


class TestPhaseD11Top10Pipeline(unittest.TestCase):

    def setUp(self):
        self.now_myt = datetime.now(MYT)
        self.ranker = EditorialRanker()
        self.scraper = SourceScraper()
        self.validator = BilingualFactValidator()
        self.config = {
            "system": {
                "min_headlines_threshold": 10,
                "sliding_window_hours": 36
            },
            "gemini_quota": {
                "daily_request_limit": 5,
                "per_run_request_limit": 1,
                "candidate_models": ["gemini-3.5-flash-lite"],
                "execution_mode": "MOCK_TEST"
            }
        }

    # 1. Existing confirmed multi-source story remains confirmed
    def test_01_confirmed_multi_source_stories_remain_confirmed(self):
        dedup = ArticleDeduplicator()
        art1 = RawArticle(
            title="沙巴地政运动会山打根开幕",
            url="https://news.seehua.com/post/1601871",
            source="诗华日报沙巴版",
            category="sabah",
            published_at=self.now_myt,
            snippet="第14届沙巴州地方政府运动会在山打根综合体育馆隆重开幕"
        )
        art2 = RawArticle(
            title="Sukan PBT Sabah Dirasmikan di Sandakan",
            url="https://www.bernama.com/bm/news.php?id=234567",
            source="Bernama",
            category="sabah",
            published_at=self.now_myt,
            snippet="Sukan PBT Sabah dirasmikan dengan meriah di Sandakan"
        )

        canonical = dedup.cluster_and_deduplicate([art1, art2])
        self.assertEqual(len(canonical), 1)
        primary = canonical[0]
        self.assertEqual(primary.extra.get("content_verification_status"), "corroborated")
        self.assertEqual(len(primary.extra.get("corroborating_sources", [])), 2)
        self.assertIn("Bernama", primary.extra.get("corroborating_sources"))
        self.assertIn("诗华日报沙巴版", primary.extra.get("corroborating_sources"))

    # 2. Existing deduplication remains intact
    def test_02_deduplication_merging_intact(self):
        dedup = ArticleDeduplicator()
        art_a = RawArticle(
            title="山打根水务局抢修包利善路爆裂水管",
            url="https://jans.sabah.gov.my/notis1",
            source="JANS",
            snippet="山打根水务局正在进行抢修"
        )
        art_b = RawArticle(
            title="山打根包利善路水管破裂 JANS抢修中",
            url="https://news.seehua.com/post/1601999",
            source="诗华日报",
            snippet="山打根水务局紧急抢修"
        )
        canonical = dedup.cluster_and_deduplicate([art_a, art_b])
        self.assertEqual(len(canonical), 1)
        self.assertEqual(canonical[0].extra.get("cluster_size"), 2)

    # 3. Sandakan and Sabah stories rank highest
    def test_03_sandakan_and_sabah_stories_rank_highest(self):
        art_sandakan = RawArticle(
            title="山打根市议会宣布低风险商业区24小时营业新政",
            url="https://news.seehua.com/post/1001",
            source="诗华日报沙巴版",
            category="sabah",
            published_at=self.now_myt,
            snippet="山打根市议会主席沃特肯森宣布刺激夜间经济政策"
        )
        art_kk = RawArticle(
            title="沙巴州议会提呈2027年财政预算案 哈芝芝重点解决基建民生",
            url="https://news.seehua.com/post/1002",
            source="诗华日报沙巴版",
            category="sabah",
            published_at=self.now_myt,
            snippet="首长哈芝芝诺宣布沙巴州预算案详情"
        )
        art_national = RawArticle(
            title="交通部宣布全国跨州长途巴士开斋节安全抽检行动",
            url="https://www.thestar.com.my/news/1003",
            source="The Star",
            category="national",
            published_at=self.now_myt,
            snippet="陆路交通局在全马各大主要大道展开抽检"
        )

        ranked = self.ranker.rank_and_select_top_10([art_national, art_kk, art_sandakan])
        self.assertGreaterEqual(len(ranked), 2)
        # Sandakan and Sabah must precede general national news
        self.assertIn("山打根", ranked[0].title)
        self.assertIn("沙巴州议会", ranked[1].title)

    # 4. Relevant national story qualifies
    def test_04_relevant_national_story_qualifies(self):
        art_fed_sabah = RawArticle(
            title="联邦政府批准沙巴东海岸特别防汛紧急拨款5000万令吉",
            url="https://www.bernama.com/bm/news.php?id=3001",
            source="Bernama",
            category="national",
            published_at=self.now_myt,
            snippet="副首相宣布向沙巴东海岸水灾高风险区拨出特别紧急治水款项"
        )
        score, status = self.ranker.score_article(art_fed_sabah)
        self.assertEqual(status, "QUALIFIED")
        self.assertGreater(score, 0)

    # 5. Unrelated Sarawak story is excluded even with high-impact keyword
    def test_05_unrelated_sarawak_story_excluded_even_with_fire_keyword(self):
        art_sarawak_fire = RawArticle(
            title="加拿逸24户长屋凌晨失火 约80%被烧毁 消拯局全力扑救",
            url="https://news.seehua.com/post/sarawak_fire",
            source="诗华日报 (砂拉越版)",
            category="national",
            published_at=self.now_myt,
            snippet="砂拉越加拿逸南甲达博一间24间门长屋今日凌晨发生夺命大火灾"
        )
        score, status = self.ranker.score_article(art_sarawak_fire)
        self.assertEqual(status, "EXCLUDED_SARAWAK_ONLY")
        self.assertLess(score, 0)

    # 6. Unrelated international story is excluded
    def test_06_unrelated_international_story_excluded(self):
        art_foreign = RawArticle(
            title="英伟达CEO黄仁勋出席加州硅谷人工智能峰会发表演讲",
            url="https://www.reuters.com/tech/123",
            source="Reuters",
            category="general",
            published_at=self.now_myt,
            snippet="加州圣何塞科技峰会现场热烈讨论芯片供应链"
        )
        score, status = self.ranker.score_article(art_foreign)
        self.assertEqual(status, "EXCLUDED_UNRELATED_NATIONAL_OR_INTL")

    # 7. Routine low-value ceremony is excluded
    def test_07_routine_ceremony_and_gala_excluded(self):
        art_gala = RawArticle(
            title="山打根某商会举办创会50周年纪念联欢晚宴 乡亲齐聚切蛋糕",
            url="https://news.seehua.com/post/dinner",
            source="诗华日报沙巴版",
            category="sabah",
            published_at=self.now_myt,
            snippet="大会安排传统舞蹈表演与切蛋糕仪式，场面温馨欢腾"
        )
        score, status = self.ranker.score_article(art_gala)
        self.assertEqual(status, "EXCLUDED_ROUTINE_FLUFF")

    # 8. Substantive article-body retrieval is reused without downgrading confirmation
    def test_08_substantive_article_body_retrieval_reused(self):
        art = RawArticle(
            title="沙巴地政运动会开幕",
            url="https://news.seehua.com/post/1601871",
            source="诗华日报沙巴版",
            snippet="运动会在山打根体育馆开幕",
            body="第14届沙巴州地方政府运动会昨晚在山打根综合体育馆隆重开幕，全州25个地方政府代表团参与。\n\n" * 5
        )
        art.extra["content_verification_status"] = "corroborated"
        enriched = self.scraper.retrieve_article_body(art)

        self.assertEqual(enriched.extra["retrieval_status"], "FULL_BODY_EXTRACTED")
        # Confirmation status must remain preserved
        self.assertEqual(enriched.extra["content_verification_status"], "corroborated")

    # 9. One batch results in exactly one mocked Gemini dispatch
    @patch("urllib.request.urlopen")
    def test_09_single_batch_produces_exactly_one_dispatch_mocked(self, mock_urlopen):
        synth = NewsSynthesizer(self.config)
        # Mock QuotaManager reserve_slot to return valid reservation
        mock_res = {
            "reservation_id": "res_2026-11-09_1_testmock",
            "model": "gemini-3.5-flash-lite",
            "status": "RESERVED"
        }
        synth.quota_mgr.reserve_slot = MagicMock(return_value=mock_res)
        synth.quota_mgr.finalize_slot = MagicMock()

        # Mock valid 10-article Gemini JSON response
        sample_headlines = [
            ("亚庇国际机场扩建工程获批全面铺开", "Projek Pembesaran Lapangan Terbang Antarabangsa Kota Kinabalu Diluluskan"),
            ("斗湖中央医院升级医疗救护专科设备", "Hospital Tawau Naik Taraf Kemudahan Rawatan Pakar Demi Rakyat"),
            ("拿笃绿色种植工业园正式启动招商", "Taman Perindustrian Hijau Lahad Datu Mula Tarik Pelaburan"),
            ("古达太阳能光伏发电站正式并网运行", "Stesen Janakuasa Solar Kudat Mula Beroperasi Salur Elektrik"),
            ("根地咬农业局推广耐旱优良水稻品种", "Jabatan Pertanian Keningau Promosi Benih Padi Tahan Kemarau"),
            ("保佛区主要排洪沟渠完成清淤防洪工程", "Projek Tebatan Banjir Parit Utama Beaufort Siap Sepenuhnya"),
            ("仙本那海域生态珊瑚保育项目成效显著", "Program Pemuliharaan Terumbu Karang Semporna Catat Kemajuan Positif"),
            ("丹南高山生态铁路线路完成安全检测", "Landasan Kereta Api Tenom Selesai Pemeriksaan Keselamatan Berkala"),
            ("兵南邦治水大沟第二阶段工程全面铺开", "Fasa Kedua Projek Tebatan Banjir Penampang Dijalankan Lancar"),
            ("吧巴滤水站输水管道完成全面技术改造", "Loji Rawatan Air Papar Selesai Kerja Naik Taraf Saluran")
        ]
        mock_articles = []
        for i, (zh, bm) in enumerate(sample_headlines, 1):
            mock_articles.append({
                "story_index": i,
                "category": "sabah",
                "title": zh,
                "titleBM": bm,
                "detail": f"【权威动态】{zh}。沙巴官方各责任单位今日全面落实该项关键发展与民生举措，确保基础设施与公共服务稳定运行。" * 3,
                "detailBM": f"{bm}. Pihak berkuasa dan agensi berkaitan di Sabah hari ini mengesahkan pelaksanaan projek strategik ini demi manfaat komuniti setempat." * 2,
                "source_url": f"https://news.seehua.com/post/{i}",
                "publisher": "诗华日报沙巴版"
            })

        mock_resp_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(mock_articles)}]
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 2500,
                "candidatesTokenCount": 3800,
                "totalTokenCount": 6300,
                "thoughtsTokenCount": 0
            }
        }

        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = json.dumps(mock_resp_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        batch_stories = [
            RawArticle(
                title=f"沙巴测试新闻{i}",
                url=f"https://news.seehua.com/post/{i}",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt
            )
            for i in range(1, 11)
        ]

        # Dispatch single batch
        res = synth.synthesize_track_a_single_batch(
            api_key="test_mock_api_key",
            today_iso="2026-11-09",
            batch_stories=batch_stories,
            usage_log_path="reports/test_token_usage_mock.jsonl"
        )

        # Invariant: EXACTLY ONE HTTP REQUEST SENT
        self.assertEqual(mock_urlopen.call_count, 1)
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 10)
        synth.quota_mgr.finalize_slot.assert_called_with("res_2026-11-09_1_testmock", "COMPLETED")

        # Cleanup test log if created
        if os.path.exists("reports/test_token_usage_mock.jsonl"):
            os.remove("reports/test_token_usage_mock.jsonl")

    # 10. No automatic retry and zero Track-B fake-news boilerplate
    @patch("urllib.request.urlopen")
    def test_10_no_automatic_retry_and_zero_track_b_boilerplate(self, mock_urlopen):
        synth = NewsSynthesizer(self.config)
        mock_res = {
            "reservation_id": "res_2026-11-09_2_failmock",
            "model": "gemini-3.5-flash-lite",
            "status": "RESERVED"
        }
        synth.quota_mgr.reserve_slot = MagicMock(return_value=mock_res)
        synth.quota_mgr.finalize_slot = MagicMock()

        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api", code=500, msg="Server Error", hdrs={}, fp=None
        )

        # In synthesize(), when Track A fails, it MUST NOT generate boilerplate
        results = synth.synthesize(
            today_iso="2026-11-09",
            articles=[RawArticle(title="测试", url="https://u", source="s")],
            api_key="mock_key"
        )

        # Invariant: 0 articles returned, 1 call attempt, 0 retries, 0 fake news templates
        self.assertEqual(results, [])
        self.assertEqual(mock_urlopen.call_count, 1)
        synth.quota_mgr.finalize_slot.assert_called_with("res_2026-11-09_2_failmock", "FAILED_HTTP_500")

    # 11. D-7 rejects pseudo-BM and unanchored facts
    def test_11_d7_fact_validator_rejects_pseudo_bm_and_unanchored_entities(self):
        # 11a: Test pseudo-BM headline rejection
        pseudo_bm_headline = HeadlineRecord(
            zh_text="沙巴地政运动会山打根开幕",
            bm_text="Laporan Berita: 沙巴地政运动会山打根开幕",
            fact_ids=[]
        )
        is_valid, errs = self.validator.validate_headline(pseudo_bm_headline, {})
        self.assertFalse(is_valid)
        self.assertTrue(any("Pseudo-Bahasa Malaysia headline detected" in e for e in errs))

        # 11b: Test unanchored named person rejection
        unanchored_headline = HeadlineRecord(
            zh_text="首长哈芝芝诺宣布沙巴重大财政预算",
            bm_text="Ketua Menteri Mengumumkan Belanjawan Utama Sabah",
            fact_ids=[]
        )
        is_valid_p, errs_p = self.validator.validate_headline(unanchored_headline, {})
        self.assertFalse(is_valid_p)
        self.assertTrue(any("Headline contains unanchored named person '哈芝芝'" in e for e in errs_p))

    # 12. Preview execution does not modify production files
    def test_12_preview_execution_does_not_modify_production_files(self):
        news_file = os.path.join(BASE_DIR, "news_data.json")
        index_file = os.path.join(BASE_DIR, "index.html")

        with open(news_file, "rb") as f:
            hash_news_before = hashlib.sha256(f.read()).hexdigest()
        with open(index_file, "rb") as f:
            hash_index_before = hashlib.sha256(f.read()).hexdigest()

        # Execute ranking and offline synthesis dry-run
        articles = [
            RawArticle(
                title=f"沙巴测试要闻第{i}条",
                url=f"https://news.seehua.com/post/{i}",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="正规测试摘要内容"
            )
            for i in range(1, 15)
        ]
        top10 = self.ranker.rank_and_select_top_10(articles)
        self.assertEqual(len(top10), 10)

        # Verify hashes after execution
        with open(news_file, "rb") as f:
            hash_news_after = hashlib.sha256(f.read()).hexdigest()
        with open(index_file, "rb") as f:
            hash_index_after = hashlib.sha256(f.read()).hexdigest()

        self.assertEqual(hash_news_before, hash_news_after)
        self.assertEqual(hash_index_before, hash_index_after)

    # 13. Phase D-11.2: Peninsular news excluded from Sandakan and Sabah
    def test_13_peninsular_news_excluded_from_sandakan_and_sabah(self):
        verifier = self.ranker.geo_verifier

        # 13a: Shah Alam / Taman Sri Muda flood must not become Sandakan even if snippet mentions Sandakan query
        res1 = verifier.verify(
            title="Shah Alam dilanda banjir kilat di Taman Sri Muda",
            snippet="Sandakan news update: Selangor hit by flash flood",
            body="Hujan lebat berterusan menyebabkan beberapa kawasan di Shah Alam termasuk Taman Sri Muda dinaiki air.",
            proposed_category="sabah"
        )
        self.assertNotEqual(res1["geo_scope"], "sandakan")
        self.assertEqual(res1["geo_scope"], "national")
        self.assertEqual(res1["verified_category"], "national")
        self.assertFalse(res1["is_sabah"])

        # 13b: Gardenia bread inspection in Peninsular locations
        res2 = verifier.verify(
            title="KPDN periksa kilang roti Gardenia di Shah Alam Selangor",
            snippet="Pemeriksaan mendapati bekalan mencukupi.",
            body="Pegawai KPDN memeriksa operasi pembekalan roti di Shah Alam dan Perak.",
            proposed_category="sabah"
        )
        self.assertEqual(res2["geo_scope"], "national")
        self.assertFalse(res2["is_sabah"])

    # 14. Phase D-11.2: Non-Sabah domestic sports excluded
    def test_14_non_sabah_domestic_sports_excluded(self):
        # 14a: Selangor vs Kuching City FC FA Cup (zero Sabah participation)
        art_sarawak_match = RawArticle(
            title="Piala FA: Selangor tundukkan Kuching City FC mara separuh akhir",
            url="https://stadiumastro.com/bola-sepak/selangor-kuching-city-fa-cup",
            source="Stadium Astro",
            category="sports",
            published_at=self.now_myt,
            snippet="Selangor FC melangkah ke peringkat seterusnya Piala FA selepas menewaskan Kuching City."
        )
        score_swk, status_swk = self.ranker.score_article(art_sarawak_match)
        self.assertLess(score_swk, 0)
        self.assertIn(status_swk, ("EXCLUDED_SARAWAK_ONLY", "EXCLUDED_UNRELATED_NATIONAL_OR_INTL"))

        # 14b: Selangor vs Perak FC (Peninsular domestic match, zero Sabah relevance)
        art_peninsular_match = RawArticle(
            title="Piala FA: Selangor tundukkan Perak FC mara separuh akhir",
            url="https://stadiumastro.com/bola-sepak/selangor-perak-fa-cup",
            source="Stadium Astro",
            category="sports",
            published_at=self.now_myt,
            snippet="Selangor FC melangkah ke peringkat seterusnya Piala FA selepas menewaskan Perak."
        )
        score_pen, status_pen = self.ranker.score_article(art_peninsular_match)
        self.assertLess(score_pen, 0)
        self.assertEqual(status_pen, "EXCLUDED_UNRELATED_NATIONAL_OR_INTL")

        # 14c: Sabah FC match qualifies
        art_sabah_match = RawArticle(
            title="Piala FA: Sabah FC menang bergaya di Stadium Likas",
            url="https://stadiumastro.com/bola-sepak/sabah-fc-menang-likas",
            source="Stadium Astro",
            category="sports",
            published_at=self.now_myt,
            snippet="Sabah FC beraksi cemerlang di hadapan ribuan penyokong di Likas."
        )
        score_s, status_s = self.ranker.score_article(art_sabah_match)
        self.assertGreater(score_s, 0)
        self.assertEqual(status_s, "QUALIFIED")

    # 15. Phase D-11.2: Cross-language deduplication and number normalization
    def test_15_cross_language_deduplication_and_number_normalization(self):
        dedup = ArticleDeduplicator()
        art_en = RawArticle(
            title="14th Sabah Local Government Sports in Sandakan with 2,000 participants",
            url="https://dailyexpress.com.my/news/12345/14th-pbt-sports-sandakan",
            source="Daily Express",
            category="sabah",
            language="en",
            published_at=self.now_myt,
            snippet="The 14th edition of the Sabah Local Government Sports was officiated in Sandakan."
        )
        art_zh = RawArticle(
            title="第14届地方政府运动会 2000健儿齐聚山打根",
            url="https://news.seehua.com/post/1601871",
            source="诗华日报沙巴版",
            category="sabah",
            language="zh",
            published_at=self.now_myt,
            snippet="第14届地方政府运动会在山打根掀开战幔，2000名健儿共襄盛举。"
        )

        self.assertTrue(dedup.is_same_event(art_en, art_zh))
        clustered = dedup.cluster_and_deduplicate([art_en, art_zh])
        self.assertEqual(len(clustered), 1)
        merged = clustered[0]
        self.assertEqual(merged.extra.get("content_verification_status"), "corroborated")
        self.assertIn("Daily Express", merged.extra.get("corroborating_sources"))
        self.assertIn("诗华日报沙巴版", merged.extra.get("corroborating_sources"))
        self.assertEqual(len(merged.extra.get("corroborating_urls")), 2)

    # 16. Phase D-11.2: Safeguard - Shared location alone does not merge unrelated stories
    def test_16_safeguard_shared_location_alone_does_not_merge(self):
        dedup = ArticleDeduplicator()
        art_flood = RawArticle(
            title="山打根发生突发水灾 多个低洼地区受影响",
            url="https://news.seehua.com/post/flood1",
            source="诗华日报",
            snippet="山打根多个地区连续暴雨后水浸"
        )
        art_court = RawArticle(
            title="山打根推事庭提控一名涉嫌诈骗男子",
            url="https://news.seehua.com/post/court1",
            source="诗华日报",
            snippet="被告在山打根推事庭面对指控"
        )
        # Even though both have LOC:SANDAKAN and LOC:SABAH, they have completely different event/topic anchors
        self.assertFalse(dedup.is_same_event(art_flood, art_court))

    # 17. Phase D-11.2: Top-10 Duplicate Suppression
    def test_17_top10_duplicate_suppression(self):
        art_a = RawArticle(
            title="第14届地方政府运动会 2000健儿齐聚山打根",
            url="https://news.seehua.com/post/sports-zh",
            source="诗华日报沙巴版",
            category="sabah",
            published_at=self.now_myt,
            snippet="第14届地方政府运动会隆重举行"
        )
        art_b = RawArticle(
            title="14th Sabah Local Government Sports in Sandakan with 2,000 participants",
            url="https://dailyexpress.com.my/news/sports-en",
            source="Daily Express",
            category="sabah",
            published_at=self.now_myt,
            snippet="14th local government sports in Sandakan"
        )
        distinct_headlines = [
            ("亚庇国际机场扩建工程获内阁批准规划", "亚庇机场将提升容量应对旅客增长"),
            ("斗湖中央医院升级医疗救护设施", "斗湖引入全新透析设备惠及病患"),
            ("拿笃绿色种植工业园正式启动招商", "拿笃吸引高科技农业投资"),
            ("古达太阳能光伏发电站正式并网运行", "古达再生能源发电量提升"),
            ("根地咬农业局推广耐旱优良水稻品种", "根地咬农民获得技术指导"),
            ("保佛区主要排洪沟渠完成清淤防洪工程", "保佛应对雨季防汛准备充分"),
            ("仙本那海域生态珊瑚保育项目成效显著", "仙本那海洋生态得到有效恢复"),
            ("丹南高山生态铁路线路完成安全检测", "丹南铁路线路恢复正常通行"),
            ("兵南邦治水大沟第二阶段工程全面铺开", "兵南邦重点防洪项目加快推进"),
            ("斗亚兰高科技农业培训学院迎来首批学员", "斗亚兰培养现代农业人才"),
            ("吧巴滤水站输水管道完成全面技术改造", "吧巴供水水质及水压显著提升")
        ]
        art_other = [
            RawArticle(
                title=title,
                url=f"https://news.seehua.com/post/infra_{i}",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet=snip
            )
            for i, (title, snip) in enumerate(distinct_headlines, 1)
        ]

        # Put both duplicate articles into candidate pool
        candidates = [art_a, art_b] + art_other
        top10 = self.ranker.rank_and_select_top_10(candidates, target_count=10)

        self.assertEqual(len(top10), 10)
        # Verify only one of the sports articles is in top 10
        sports_in_top10 = [
            x for x in top10
            if "14" in x.title and ("地方政府运动会" in x.title or "Local Government Sports" in x.title)
        ]
        self.assertEqual(len(sports_in_top10), 1)
        selected_sports = sports_in_top10[0]
        # Verify sources were merged
        self.assertIn("Daily Express", selected_sports.extra.get("corroborating_sources", []))
        self.assertIn("诗华日报沙巴版", selected_sports.extra.get("corroborating_sources", []))

    # 18. Phase D-11.3 Correction A: Bilingual Headline Quality Gate
    def test_18_headline_quality_gate_rejects_placeholders_and_validates_natural_bm(self):
        # 18a: Rejects generic placeholder headlines from D-11.2 preview
        placeholder_cases = [
            ("兵南邦马拉昆花园 一间双层排屋发生火灾", "Perkembangan Utama dan Terkini Sabah Nombor 2"),
            ("亚庇甘榜独立式住宅遇火劫 遭大火全数吞噬幸无伤亡", "Perkembangan Utama dan Terkini Sabah Nombor 3"),
            ("CILTM：扩建或搬迁？ 促全面研究庇机场发展", "Perkembangan Utama dan Terkini Sabah Nombor 4"),
            ("摩托失控坠入石沟 41岁骑士丧命", "Perkembangan Utama dan Terkini Sabah Nombor 5"),
            ("测试要闻第1条", "Laporan Berita: 测试要闻第1条"),
            ("", "Berita Penting Sabah"),
            ("沙巴重大新闻", "")
        ]
        for zh, bm in placeholder_cases:
            hl = HeadlineRecord(zh_text=zh, bm_text=bm, fact_ids=[])
            is_valid, errs = self.validator.validate_headline(hl, {})
            self.assertFalse(is_valid, f"Should reject invalid placeholder headline: '{zh}' / '{bm}'")

        # 18b: Rejects contradictory cross-lingual headline (Fatal crash in ZH vs rushed to hospital in BM)
        contradictory_hl = HeadlineRecord(
            zh_text="兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命",
            bm_text="Kemalangan Jalan Raya di Sabah: Pemandu Dikejarkan ke Hospital",
            fact_ids=[]
        )
        is_valid_c, errs_c = self.validator.validate_headline(contradictory_hl, {})
        self.assertFalse(is_valid_c)
        self.assertTrue(any("indicates a fatality" in e for e in errs_c))

        # 18c: Accepts natural, publication-quality bilingual headlines
        valid_cases = [
            # Penampang house fire
            (
                "兵南邦马拉昆花园 一间双层排屋发生火灾",
                "Kebakaran Rumah Dua Tingkat di Taman Malakun Penampang Hangus Terbakar"
            ),
            # Kota Kinabalu house fire
            (
                "亚庇甘榜独立式住宅遇火劫 遭大火全数吞噬幸无伤亡",
                "Rumah Sesebuah di Kampung Kota Kinabalu Musnah Terbakar Dijilat Api, Tiada Kemalangan Jiwa"
            ),
            # CILTM / KKIA airport development debate
            (
                "CILTM：扩建或搬迁？ 促全面研究庇机场发展",
                "Debat Pembangunan KKIA: CILTM Gesa Kajian Menyeluruh Sama Ada Pembesaran atau Pemindahan"
            ),
            # Fatal motorcycle accident
            (
                "兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命",
                "Nahas Motosikal di Penampang: Penunggang Maut Terbabas ke Dalam Parit"
            )
        ]
        for zh, bm in valid_cases:
            hl = HeadlineRecord(zh_text=zh, bm_text=bm, fact_ids=[])
            is_valid, errs = self.validator.validate_headline(hl, {})
            self.assertTrue(is_valid, f"Expected valid headline to pass: '{zh}' / '{bm}'. Errs: {errs}")

    # 19. Phase D-11.3 Correction B: Accident Deduplication Positive, Negative, and Unresolved
    def test_19_accident_deduplication_positive_negative_unresolved(self):
        dedup = ArticleDeduplicator()

        # 19a: Positive test — Same accident with matching district and victim detail
        art_same_1 = RawArticle(
            title="兵南邦凌晨夺命车祸 41岁骑士失控冲石沟当场毙命",
            url="https://news.seehua.com/post/acc1",
            source="诗华日报沙巴版",
            category="sabah",
            published_at=self.now_myt,
            snippet="兵南邦发生一起致命车祸，一名41岁摩托车骑士失控坠入石沟身亡"
        )
        art_same_2 = RawArticle(
            title="Nahas Motosikal Penampang: Penunggang 41 Tahun Maut Terbabas Masuk Parit",
            url="https://dailyexpress.com.my/news/acc2",
            source="Daily Express",
            category="sabah",
            language="ms",
            published_at=self.now_myt,
            snippet="Seorang penunggang motosikal berusia 41 tahun maut di Penampang selepas terbabas"
        )
        self.assertTrue(dedup.is_same_event(art_same_1, art_same_2))

        # 19b: Negative test — Different accidents with conflicting districts
        art_penampang = RawArticle(
            title="兵南邦夺命车祸 骑士失控冲沟渠当场毙命",
            url="https://news.seehua.com/post/acc_penampang",
            source="诗华日报沙巴版",
            category="sabah",
            snippet="兵南邦发生车祸"
        )
        art_tawau = RawArticle(
            title="斗湖夺命车祸 骑士失控冲沟渠当场毙命",
            url="https://news.seehua.com/post/acc_tawau",
            source="诗华日报沙巴版",
            category="sabah",
            snippet="斗湖发生车祸"
        )
        self.assertFalse(dedup.is_same_event(art_penampang, art_tawau))

        # 19c: Unresolved test — Actual D-11.2 entries #1 and #5
        # Story #1 has Penampang but lacks victim age; Story #5 has age 41 but lacks district.
        art_1 = RawArticle(
            title="兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命",
            url="https://news.seehua.com/post/1602304",
            source="诗华日报沙巴版",
            category="sabah",
            published_at=self.now_myt
        )
        art_5 = RawArticle(
            title="摩托失控坠入石沟 41岁骑士丧命",
            url="https://sabah.sinchew.com.my/news/20261109/sabah/8050285",
            source="沙巴星洲日报",
            category="sabah",
            published_at=self.now_myt
        )
        # Because local records lack full body evidence to corroborate district or age, they do not merge
        self.assertFalse(dedup.is_same_event(art_1, art_5))

    # 20. Phase D-11.3 Correction C: Editorial Importance & Diversity Damping
    def test_20_editorial_importance_and_diversity_damping(self):
        # 20a: Major policy, land, border, and infrastructure stories score high
        policy_stories = [
            RawArticle(
                title="积压数十年土地申请有望解决 沙巴5000英亩土地展开测量",
                url="https://news.seehua.com/post/land_5000",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="沙巴5000英亩土地展开测量"
            ),
            RawArticle(
                title="指签证漏洞恐成诈骗通道 曾子文促加强沙巴入境监管",
                url="https://news.seehua.com/post/visa_scam",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="加强沙巴入境监管防范签证漏洞"
            ),
            RawArticle(
                title="沙巴内阁通过2027旅游年特别预算 重点推介海岛与文化遗产",
                url="https://news.seehua.com/post/tourism_budget",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="沙巴旅游年特别预算通过"
            ),
            RawArticle(
                title="CILTM：扩建或搬迁？ 促全面研究庇机场发展",
                url="https://sabah.sinchew.com.my/news/kkia_ciltm",
                source="沙巴星洲日报",
                category="sabah",
                published_at=self.now_myt,
                snippet="研究亚庇国际机场发展规划"
            )
        ]
        for art in policy_stories:
            score, status = self.ranker.score_article(art)
            self.assertEqual(status, "QUALIFIED")
            self.assertGreaterEqual(score, 40, f"Expected high score for major policy story: {art.title}")

        # 20b: Routine incident diversity damping prevents multiple minor fires/accidents from monopolizing Top 10
        minor_incidents = [
            RawArticle(title="兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命", url="https://u1", source="s1", category="sabah", published_at=self.now_myt),
            RawArticle(title="兵南邦马拉昆花园 一间双层排屋发生火灾", url="https://u2", source="s2", category="sabah", published_at=self.now_myt),
            RawArticle(title="亚庇甘榜独立式住宅遇火劫 遭大火全数吞噬幸无伤亡", url="https://u3", source="s3", category="sabah", published_at=self.now_myt),
            RawArticle(title="摩托失控坠入石沟 41岁骑士丧命", url="https://u4", source="s4", category="sabah", published_at=self.now_myt),
            RawArticle(title="疑因杂货赊账起争执 75岁老翁遭割喉杀害", url="https://u5", source="s5", category="sabah", published_at=self.now_myt),
        ]
        pool = minor_incidents + policy_stories
        top_selected = self.ranker.rank_and_select_top_10(pool, target_count=7)

        # All 4 major policy stories should be in the top selected list!
        selected_titles = [s.title for s in top_selected]
        for p in policy_stories:
            self.assertIn(p.title, selected_titles, f"Policy story '{p.title}' should not be crowded out")

    # 21. Phase D-11.4 Correction A: Strict Column & Non-News Feature Exclusion
    def test_21_column_and_opinion_feature_exclusion(self):
        # 21a: Editorial column and feature essay candidates MUST be excluded
        column_candidates = [
            RawArticle(
                title="【小影小憾】分数之外的那一笔",
                url="https://news.seehua.com/post/xyxh_1",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="谈教育随笔与人生感悟"
            ),
            RawArticle(
                title="【小城故事】风之城的一座老桥",
                url="https://news.seehua.com/post/xcgs_1",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="山打根怀旧历史随笔与感怀"
            ),
            RawArticle(
                title="【人在江湖】职场人情冷暖随想",
                url="https://news.seehua.com/post/rzjh_1",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="专栏作家漫谈人生哲理"
            ),
            RawArticle(
                title="专栏：微型华小教育的省思与建议",
                url="https://news.seehua.com/post/column_edu",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="教育专栏随笔，非突发硬新闻"
            )
        ]
        for art in column_candidates:
            score, status = self.ranker.score_article(art)
            self.assertLess(score, 0, f"Column '{art.title}' must receive negative score")
            self.assertEqual(status, "EXCLUDED_ROUTINE_FLUFF", f"Column '{art.title}' must be classified as EXCLUDED_ROUTINE_FLUFF")

        # 21b: Genuine public-interest community, heritage, tourism, and environmental hard news MUST be preserved
        genuine_news = [
            RawArticle(
                title="国内外数千人参与 婆罗洲观鸟节 推动沙巴生态旅游",
                url="https://news.seehua.com/post/borneo_bird_fest",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="婆罗洲观鸟节在山打根雨林探索中心盛大开幕，吸引海内外生态爱好者"
            ),
            RawArticle(
                title="沙巴野生动物保护局于山打根西必洛设立红毛猩猩野外巡护营地",
                url="https://www.theborneopost.com/2026/11/08/sepilok-orangutan-patrol",
                source="Borneo Post",
                category="sabah",
                published_at=self.now_myt,
                snippet="设立智能化反偷猎与栖息地生态巡护营地"
            ),
            RawArticle(
                title="沙巴博物馆启动山打根古迹步道修缮工程 保护二战历史遗址",
                url="https://news.seehua.com/post/sandakan_heritage_trail",
                source="诗华日报沙巴版",
                category="sabah",
                published_at=self.now_myt,
                snippet="拨款修缮历史古迹步道，完善二战文化遗产保护"
            )
        ]
        for art in genuine_news:
            score, status = self.ranker.score_article(art)
            self.assertGreater(score, 0, f"Genuine news '{art.title}' must receive positive score")
            self.assertEqual(status, "QUALIFIED", f"Genuine news '{art.title}' must qualify")

    # 22. Phase D-11.4 Correction B: Stronger Chinese/Malay Headline Correspondence Validation
    def test_22_bilingual_headline_correspondence_strong_validation(self):
        validator = BilingualFactValidator()

        # 22a: Positive correspondence test cases
        positive_cases = [
            # Airport expansion / relocation
            ("CILTM促全面研究亚庇机场发展 探讨扩建或搬迁", "Debat Pembangunan KKIA: CILTM Gesa Kajian Menyeluruh Lapangan Terbang Sama Ada Pembesaran atau Pemindahan"),
            # Fatal motorcycle accident
            ("兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命", "Nahas Motosikal di Penampang: Penunggang Maut Terbabas ke Dalam Parit"),
            # Residential fire
            ("兵南邦马拉昆花园 一间双层排屋失火", "Kebakaran Rumah Dua Tingkat di Taman Malakun Penampang Hangus Terbakar"),
            # Immigration and visa enforcement
            ("指签证漏洞成诈骗通道 曾子文促加强沙入境监管", "Kawalan Imigresen Sabah Perlu Diperketat Elak Ketirisan Visa Jadi Laluan Sindiket Penipuan"),
            # Land administration
            ("已搁置数十年 拟测量沙巴5000英亩地", "Kerja Pengukuran Tanah Seluas 5,000 Ekar di Sabah Bermula Selesaikan Permohonan Tertangguh"),
            # Rural libraries and digital learning
            ("沙图应转数码学习中心 沙图科技学院促沙图配合", "Perpustakaan Desa Sabah Perlu Beralih Jadi Pusat Pembelajaran Digital Perkasa Komuniti")
        ]
        for zh, bm in positive_cases:
            h = HeadlineRecord(fact_ids=[], zh_text=zh, bm_text=bm)
            is_valid, errs = validator.validate_headline(h, {})
            self.assertTrue(is_valid, f"Expected positive validation for ZH='{zh}' and BM='{bm}', but got errors: {errs}")

        # 22b: Deliberate cross-domain mismatch and location contradiction cases
        negative_cases = [
            # Airport development paired with community heritage
            ("CILTM促全面研究亚庇机场发展 探讨扩建或搬迁", "Sorotan Kisah Warisan Sejarah dan Pembangunan Komuniti Tempatan Sandakan"),
            # Fatal motorcycle accident paired with house fire
            ("兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命", "Kebakaran Rumah Dua Tingkat di Taman Malakun Penampang Hangus Terbakar"),
            # Residential fire paired with fatal accident
            ("兵南邦马拉昆花园 一间双层排屋失火", "Penunggang Motosikal 41 Tahun Maut Selepas Terbabas ke Dalam Longkang Konkrit di Sabah"),
            # Immigration visa paired with rural digital library
            ("指签证漏洞成诈骗通道 曾子文促加强沙入境监管", "Perpustakaan Desa Sabah Perlu Beralih Jadi Pusat Pembelajaran Digital Perkasa Komuniti"),
            # Land administration paired with hospital dialysis
            ("已搁置数十年 拟测量沙巴5000英亩地", "Pusat Dialisis Pakar Baharu Hospital Duchess of Kent Sandakan Mula Beroperasi"),
            # Rural library paired with public bus enforcement
            ("沙图应转数码学习中心 沙图科技学院促沙图配合", "JPJ Sabah Nyamar Penumpang Bas Ekspres Pantau Keselamatan Jalan Raya Musim Deepavali"),
            # Location contradiction: Penampang (ZH) paired with Sandakan (BM)
            ("兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命", "Nahas Motosikal di Sandakan: Penunggang Maut Terbabas ke Dalam Parit")
        ]
        for zh, bm in negative_cases:
            h = HeadlineRecord(fact_ids=[], zh_text=zh, bm_text=bm)
            is_valid, errs = validator.validate_headline(h, {})
            self.assertFalse(is_valid, f"Expected mismatch rejection for ZH='{zh}' and BM='{bm}', but validation passed!")
            self.assertGreater(len(errs), 0)

    # 23. Phase D-11.5 Correction A: SourceScraper Robust Extraction & Non-Challenge CF Safety
    def test_23_source_scraper_cloudflare_and_container_extraction(self):
        from pipeline.source_scraper import SourceScraper
        scraper = SourceScraper()

        # 23a: HTML containing CDN cloudflare references must NOT be blocked
        cdn_html = """
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
            <script src="https://news.seehua.com/wp-content/plugins/cloudflare-static/rocket.js"></script>
        </head>
        <body>
            <div class="post-content">
                <p>沙巴州政府今日宣布推出全新水利基础设施提升计划，全面解决多区水荒问题。</p>
                <p>首长哈芝芝诺指出，该计划将覆盖山打根及亚庇等关键重镇，分三阶段实施。</p>
            </div>
            <div class="post-tags">标签：沙巴 水利</div>
        </body>
        </html>
        """
        body, status = scraper.extract_substantive_body(cdn_html, "https://news.seehua.com/post/12345")
        self.assertEqual(status, "FULL_BODY_EXTRACTED")
        self.assertIsNotNone(body)
        self.assertIn("沙巴州政府今日宣布推出全新水利", body)

        # 23b: Authentic Cloudflare challenge page must be correctly classified
        challenge_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Just a moment...</title></head>
        <body>
            <div class="cf-browser-verification">Checking your browser before accessing website...</div>
        </body>
        </html>
        """
        body_cf, status_cf = scraper.extract_substantive_body(challenge_html, "https://example.com/blocked")
        self.assertIsNone(body_cf)
        self.assertEqual(status_cf, "ACCESS_BLOCKED_OR_CHALLENGE")

        # 23c: The Star publisher container pattern extraction
        star_html = """
        <html>
        <body>
            <div id="story-body" class="story">
                <p>Sabah athletes face exceptional travel costs when competing at national tournaments across Malaysia.</p>
                <p>State officials have called for equitable logistics subsidies to support regional sporting development.</p>
            </div>
            <div id="story-recom-div">Related articles</div>
        </body>
        </html>
        """
        body_star, status_star = scraper.extract_substantive_body(star_html, "https://www.thestar.com.my/news/nation/2026/11/09/sports")
        self.assertEqual(status_star, "FULL_BODY_EXTRACTED")
        self.assertIn("Sabah athletes face exceptional travel costs", body_star)

    # 24. Phase D-11.5 Correction B: Deduplication Anti-Chaining & Corroboration Protection
    def test_24_deduplicator_anti_chaining_and_multi_source_corroboration(self):
        dedup = ArticleDeduplicator()

        # 24a: Anti-chaining test: 3 distinct events must NOT collapse into a mega-cluster
        art_water = RawArticle(
            title="山打根水务局抢修包利善路爆裂水管 预计下午恢复供水",
            url="https://jans.sabah.gov.my/water_repair_1",
            source="JANS",
            snippet="JANS抢修水管"
        )
        art_police = RawArticle(
            title="警方在山打根破获跨州电信诈骗集团 逮捕5名嫌犯",
            url="https://news.seehua.com/post/pdrm_scam_sandakan",
            source="诗华日报沙巴版",
            snippet="警方破获诈骗集团"
        )
        art_airport = RawArticle(
            title="亚庇国际机场扩建或搬迁评估报告 交通部预料下月出炉",
            url="https://www.thestar.com.my/news/kkia_expansion",
            source="The Star",
            snippet="交通部评估亚庇机场搬迁或扩建"
        )

        canonical = dedup.cluster_and_deduplicate([art_water, art_police, art_airport])
        self.assertEqual(len(canonical), 3, "Three distinct events must form exactly 3 canonical stories, no chaining")

        # 24b: Multi-source corroboration on same event must merge and upgrade status
        art_kkia_zh = RawArticle(
            title="CILTM促全面研究亚庇机场发展 探讨扩建或搬迁可行性",
            url="https://sabah.sinchew.com.my/news/ciltm_kkia",
            source="星洲日报沙巴版",
            snippet="CILTM建议综合评估亚庇机场扩建或搬迁"
        )
        art_kkia_bm = RawArticle(
            title="Kajian Pembangunan KKIA: CILTM Gesa Kaji Pembesaran atau Pemindahan",
            url="https://www.dailyexpress.com.my/news/kkia_ciltm_study",
            source="Daily Express",
            snippet="CILTM menggesa kajian pembangunan KKIA sama ada pembesaran atau pemindahan"
        )
        canonical_corrob = dedup.cluster_and_deduplicate([art_airport, art_kkia_zh, art_kkia_bm])
        # KKIA CILTM articles should cluster together with multi-source corroboration
        kkia_clusters = [c for c in canonical_corrob if "kkia" in (c.url or '').lower() or "ciltm" in (c.title or '').lower()]
        self.assertGreaterEqual(len(kkia_clusters), 1)
        multi_source_found = any(len(c.extra.get("corroborating_sources", [])) >= 2 for c in canonical_corrob)
        self.assertTrue(multi_source_found, "Corroborated KKIA story must retain multi-source confirmation")


if __name__ == "__main__":
    unittest.main()
