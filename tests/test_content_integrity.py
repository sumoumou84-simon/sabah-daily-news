import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from collectors.base import RawArticle
from pipeline.geo_verifier import GeographicVerifier
from pipeline.utility_verifier import UtilityVerifier
from pipeline.normalizer import ArticleNormalizer, MYT
from pipeline.synthesizer import NewsSynthesizer

class TestContentIntegrity(unittest.TestCase):

    def setUp(self):
        self.geo_verifier = GeographicVerifier()
        self.util_verifier = UtilityVerifier()
        self.normalizer = ArticleNormalizer(sliding_window_hours=36)
        self.synthesizer = NewsSynthesizer({})
        self.now_myt = datetime.now(MYT)

    # -------------------------------------------------------------
    # 1. Sarawak article rejected from Sabah category
    # -------------------------------------------------------------
    def test_01_sarawak_article_rejected_from_sabah(self):
        """Articles concerning Sarawak (Kuching, Miri, Sibu, SUPP) must NEVER be categorized as Sabah."""
        # Case A: Kuching drunk driving raid
        res_a = self.geo_verifier.verify(
            title="古晋达闽路取缔酒驾 2男子落网",
            snippet="古晋交通调查组在达闽路设卡路检...",
            source="诗华日报沙巴版",  # Mislabelled source
            url="https://news.seehua.com/?cat=3",
            proposed_category="sabah"
        )
        self.assertNotEqual(res_a["verified_category"], "sabah", "Kuching article must NOT be classified as Sabah")
        self.assertEqual(res_a["verified_category"], "national", "Kuching article must be reclassified to National")
        self.assertTrue(res_a["is_sarawak"])
        self.assertFalse(res_a["is_sabah"])
        self.assertIn("诗华日报 (砂拉越版)", res_a["corrected_source"], "Source publisher must be corrected to Sarawak edition")

        # Case B: Miri local council & market
        res_b = self.geo_verifier.verify(
            title="舞台设施公厕竣工 美里珠巴5号路巴刹换新貌",
            snippet="美里市政局宣布珠巴巴刹改建工程竣工...",
            source="诗华日报",
            proposed_category="sabah"
        )
        self.assertNotEqual(res_b["verified_category"], "sabah", "Miri article must NOT be classified as Sabah")

        # Case C: Sarawak political figure (Chong Chieng Jen)
        res_c = self.geo_verifier.verify(
            title="张健仁：为民发声 盼选民支持行动党",
            snippet="砂拉越实旦宾区国会议员张健仁指出...",
            source="星洲日报",
            proposed_category="sabah"
        )
        self.assertNotEqual(res_c["verified_category"], "sabah", "Sarawak MP Chong Chieng Jen must NOT be classified as Sabah")

    # -------------------------------------------------------------
    # 2. Sandakan article correctly classified
    # -------------------------------------------------------------
    def test_02_sandakan_article_correctly_classified(self):
        """Articles mentioning Sandakan must be classified as Sabah with geo_scope 'sandakan'."""
        res = self.geo_verifier.verify(
            title="山打根市议会（MPS）展开拉卜路排洪渠清淤防汛行动",
            snippet="山打根工务组与肯特医院附近低洼区展开例行检查...",
            url="https://example.com/sandakan-drainage",
            proposed_category="sabah"
        )
        self.assertEqual(res["verified_category"], "sabah")
        self.assertEqual(res["geo_scope"], "sandakan")
        self.assertTrue(res["is_sabah"])
        self.assertFalse(res["is_sarawak"])

    # -------------------------------------------------------------
    # 3. Sabah article correctly classified
    # -------------------------------------------------------------
    def test_03_sabah_article_correctly_classified(self):
        """Articles concerning Kota Kinabalu, Tawau, or Sabah agencies must be categorized as Sabah."""
        res_kk = self.geo_verifier.verify(
            title="亚庇亿达公路发生车祸 警方派员勘查现场交通",
            snippet="亚庇警区主任证实交通受阻并呼吁目击者提供线索...",
            url="https://news.seehua.com/?cat=8",
            source="诗华日报沙巴版",
            proposed_category="sabah"
        )
        self.assertEqual(res_kk["verified_category"], "sabah")
        self.assertTrue(res_kk["is_sabah"])
        self.assertFalse(res_kk["is_sarawak"])

        res_chief = self.geo_verifier.verify(
            title="沙巴首长哈芝芝宣布拨款提升全州沿海防波堤工程",
            snippet="沙巴州政府今日在州议会提呈防灾特别追加预算...",
            proposed_category="sabah"
        )
        self.assertEqual(res_chief["verified_category"], "sabah")

    # -------------------------------------------------------------
    # 4. Missing source URL rejected
    # -------------------------------------------------------------
    def test_04_missing_source_url_rejected(self):
        """Articles lacking a valid HTTP/HTTPS URL must be rejected by normalizer."""
        art_no_url = RawArticle(
            title="无有效链接的测试要闻",
            url="",
            source="Test"
        )
        art_invalid_url = RawArticle(
            title="本地假路径测试要闻",
            url="javascript:void(0)",
            source="Test"
        )
        art_valid_url = RawArticle(
            title="具有官方有效链接的沙巴新闻",
            url="https://example.com/valid-article",
            source="Test"
        )

        res = self.normalizer.normalize([art_no_url, art_invalid_url, art_valid_url])
        urls = [a.url for a in res]
        self.assertNotIn("", urls)
        self.assertNotIn("javascript:void(0)", urls)
        self.assertIn("https://example.com/valid-article", urls)

    # -------------------------------------------------------------
    # 5. Original date preserved across pipeline
    # -------------------------------------------------------------
    def test_05_original_date_preserved(self):
        """Original published_at must not be replaced with collection or site publication date."""
        orig_dt = self.now_myt - timedelta(hours=8)
        art = RawArticle(
            title="沙巴气象局发布雷暴预警",
            url="https://example.com/weather-test",
            source="气象局",
            category="sabah",
            published_at=orig_dt
        )
        normalized = self.normalizer.normalize([art])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].published_at, orig_dt, "Normalizer must preserve original published_at")

        synthesized = self.synthesizer.synthesize_track_b_standalone("2026-11-08", normalized)
        self.assertEqual(len(synthesized), 1)
        self.assertEqual(synthesized[0]["original_published_at"], orig_dt.isoformat())
        self.assertIn("collected_at", synthesized[0])
        self.assertIn("site_published_at", synthesized[0])
        self.assertIn("updated_at", synthesized[0])

    # -------------------------------------------------------------
    # 6. Unsupported LIVE alert rejected / marked unverified
    # -------------------------------------------------------------
    def test_06_unsupported_live_alert_rejected(self):
        """Utility card without valid official URL or timestamp must not claim LIVE / verified status."""
        unsupported_alert = {
            "id": "X",
            "label": "虚构市政通报",
            "time": "08:00",
            "status": "LIVE 抢修中",
            "official_source_url": "",  # Missing official URL
            "source_timestamp": "",     # Missing timestamp
            "issue": "无依据的突发事件描述"
        }
        res = self.util_verifier.verify_alert(unsupported_alert)
        self.assertFalse(res["verified"], "Alert without official source URL must not be verified")
        self.assertEqual(res["status"], "待核实", "Unverified alert must show '待核实'")
        self.assertEqual(res["statusBM"], "Dalam Pengesahan")

    # -------------------------------------------------------------
    # 7. Contradictory water restoration status rejected / reconciled
    # -------------------------------------------------------------
    def test_07_contradictory_water_status_detected_and_reconciled(self):
        """Contradiction between fully restored supply and future tonight repair must be flagged."""
        contradictory_card = {
            "id": "W",
            "label": "沙巴水务局 (JANS) 斗湖古哈拉抽水",
            "status": "LIVE 供水恢复",
            "issue": "核心机组故障抢修已于昨夜全面竣工，市区供水已恢复常压",
            "recovery": "预计修复：今晚 22:00 前完成调试并逐步恢复常压",  # Contradicts completed status!
            "pressure": "降压供水区：斗湖市区及沿海片区",
            "tanker": "配水应急车：已派驻核心住宅区备勤",
            "official_source_url": "https://water.sabah.gov.my/",
            "time": "08:30"
        }
        has_contra, detail = self.util_verifier.check_contradiction(contradictory_card)
        self.assertTrue(has_contra, "Contradiction between restored supply and 22:00 future repair must be flagged")

        # After reconciliation, the contradiction must be resolved
        reconciled = self.util_verifier.reconcile_utility(contradictory_card)
        has_contra_after, _ = self.util_verifier.check_contradiction(reconciled)
        self.assertFalse(has_contra_after, "Reconciled card must eliminate the contradiction")
        self.assertNotIn("预计修复：今晚 22:00", reconciled["recovery"])

    # -------------------------------------------------------------
    # 8. Advertisements excluded from editorial news counts
    # -------------------------------------------------------------
    def test_08_commercial_ads_excluded_from_editorial_news(self):
        """SAZA RICE and car rental commercial advertisements must be filtered from editorial news."""
        ad_art1 = RawArticle(
            title="SAZA RICE 买大米赢豪车 Jetour Dashing 岁末抽奖进行中",
            url="https://example.com/saza-rice-ad",
            source="广告投放",
            category="sabah",
            snippet="凡购买Saza大米即可参与Peraduan Beli & Menang抽奖大奖豪车..."
        )
        ad_art2 = RawArticle(
            title="Marco Thien 山打根优质租车 010-930 1117 随时接单",
            url="https://example.com/rent-car-ad",
            source="广告投放",
            category="sabah",
            snippet="山打根租车服务提供全新威驰、Alza等多种车型..."
        )
        real_art = RawArticle(
            title="沙巴斗湖农业局举办生态种植技术培训班",
            url="https://example.com/real-agriculture-news",
            source="官方通报",
            category="sabah",
            snippet="斗湖百名农户参与绿色环保种植新规培训..."
        )

        filtered = self.normalizer.normalize([ad_art1, ad_art2, real_art])
        titles = [a.title for a in filtered]
        self.assertNotIn("SAZA RICE 买大米赢豪车 Jetour Dashing 岁末抽奖进行中", titles, "SAZA Rice ad must be filtered")
        self.assertNotIn("Marco Thien 山打根优质租车 010-930 1117 随时接单", titles, "Car rental ad must be filtered")
        self.assertEqual(len(filtered), 1, "Only genuine news article should pass")
        self.assertEqual(self.normalizer.ad_filter_count, 2, "Ad counter must reflect 2 filtered commercial items")

if __name__ == "__main__":
    unittest.main()
