import unittest
import json
import re

class TestChineseLanguageIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.news_file = "news_data.json"
        cls.index_file = "index.html"
        
        with open(cls.news_file, "r", encoding="utf-8") as f:
            cls.data = json.load(f)
        cls.headlines = cls.data.get("headlines", [])
        cls.utilities = cls.data.get("utilities", [])
        cls.archive = cls.data.get("archive", {})
        
        with open(cls.index_file, "r", encoding="utf-8") as f:
            cls.html = f.read()

        cls.chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')

        # Known English headline prefixes that previously leaked
        cls.forbidden_english_prefixes = [
            "Malaysian King", "Fahmi says", "Hong Kong airport", "Badminton:",
            "Nottingham Forest", "Lee Chong Wei", "Portugal's", "China MMA"
        ]

        # Common BM editorial sentence fragments that must not appear in Chinese text
        cls.forbidden_bm_markers = [
            "Seorang penunggang", "Kempen derma darah", "Kenyataan rasmi",
            "berjaya ditahan", "telah meninggal dunia", "Kementerian Kewangan",
            "Polis Diraja Malaysia", "mengalami kecederaan"
        ]

    def test_all_24_articles_present(self):
        """Verify edition contains exactly 24 articles."""
        self.assertEqual(len(self.headlines), 24, "Edition must contain exactly 24 articles.")

    def test_all_24_chinese_headlines_complete_and_localized(self):
        """Verify every Chinese headline is complete, natural Chinese and not an English source string."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            zh_title = item.get("title", "").strip()
            self.assertTrue(len(zh_title) >= 10, f"Article {hid} ({idx+1}) Chinese title is too short: {zh_title}")
            
            # Check for Chinese characters
            zh_match = self.chinese_char_pattern.search(zh_title)
            self.assertIsNotNone(zh_match, f"Article {hid} Chinese title contains NO Chinese characters: {zh_title}")
            
            # Check that headline is not primarily English
            ascii_count = sum(1 for c in zh_title if ord(c) < 128)
            self.assertLess(ascii_count, len(zh_title) * 0.5,
                            f"Article {hid} Chinese title has too high ASCII ratio (likely English): {zh_title}")
            
            # Check specifically against previously leaked English headlines
            for prefix in self.forbidden_english_prefixes:
                self.assertFalse(zh_title.startswith(prefix),
                                 f"Article {hid} Chinese title leaked English prefix '{prefix}': {zh_title}")

    def test_all_24_chinese_summaries_complete_and_natural(self):
        """Verify all 24 Chinese summaries are informative, substantive, and free from HTML/boilerplate."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            zh_detail = item.get("detail", "").strip()
            self.assertTrue(len(zh_detail) >= 80, f"Article {hid} Chinese detail must be substantive (>=80 chars): {len(zh_detail)}")
            
            # Must contain Chinese characters
            self.assertIsNotNone(self.chinese_char_pattern.search(zh_detail), f"Article {hid} detail has no Chinese.")
            
            # Must NOT contain raw leaked HTML tags (<ol>, <li>, <a>, <font>)
            for tag in ["<ol>", "<li>", "<a href=", "<font", "</ol>", "</li>", "</a>"]:
                self.assertNotIn(tag, zh_detail, f"Article {hid} Chinese detail contains forbidden raw HTML tag '{tag}'")
                
            # Must NOT contain obsolete placeholder boilerplate
            self.assertNotIn("本项进展直接关系到本地民众切身利益", zh_detail,
                             f"Article {hid} Chinese detail contains canned placeholder boilerplate!")
            self.assertNotIn("【权威动态播报】", zh_detail,
                             f"Article {hid} Chinese detail contains canned header tag!")

    def test_no_unintended_bm_in_chinese_fields(self):
        """Verify Chinese titles and details contain no leaked BM editorial phrases."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            zh_title = item.get("title", "")
            zh_detail = item.get("detail", "")
            for bm_phrase in self.forbidden_bm_markers:
                self.assertNotIn(bm_phrase, zh_title, f"Article {hid} title contains leaked BM phrase: {bm_phrase}")
                self.assertNotIn(bm_phrase, zh_detail, f"Article {hid} detail contains leaked BM phrase: {bm_phrase}")

    def test_chinese_source_labels_and_badges(self):
        """Verify Chinese source labels are localized and clean."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            source_zh = item.get("source", "").strip()
            self.assertTrue(len(source_zh) > 0, f"Article {hid} missing Chinese source label.")
            # Verify source contains Chinese characters
            self.assertIsNotNone(self.chinese_char_pattern.search(source_zh),
                                 f"Article {hid} source label '{source_zh}' should be localized in Chinese.")

    def test_existing_bm_fields_remain_intact(self):
        """Verify newly repaired BM fields (titleBM, detailBM, sourceBM, tagBM, verifiedBM) were preserved without damage."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            title_bm = item.get("titleBM", "").strip()
            detail_bm = item.get("detailBM", "").strip()
            source_bm = item.get("sourceBM", "").strip()
            tag_bm = item.get("tagBM", "").strip()
            verified_bm = item.get("verifiedBM", "").strip()

            self.assertTrue(len(title_bm) > 10, f"Article {hid} BM title was damaged or lost.")
            self.assertTrue(len(detail_bm) > 50, f"Article {hid} BM detail was damaged or lost.")
            self.assertTrue(len(source_bm) > 0, f"Article {hid} BM source was damaged or lost.")
            self.assertTrue(len(tag_bm) > 0, f"Article {hid} BM tag was damaged or lost.")
            self.assertTrue(len(verified_bm) > 0, f"Article {hid} BM verified was damaged or lost.")
            
            # Specific factual fidelity check on art_sabah_1 BM
            if hid == "art_sabah_1":
                self.assertNotIn("Seksyen 41(1)", detail_bm)
                self.assertNotIn("Hospital Queen Elizabeth", detail_bm)

    def test_chinese_and_bm_mode_independence(self):
        """Verify compiled index.html has distinct .lang-zh and .lang-bm spans and no raw unlocalized text."""
        self.assertIn('class="lang-zh"', self.html)
        self.assertIn('class="lang-bm hidden"', self.html)
        
        # Verify Chinese titles are rendered inside .lang-zh in news cards
        for idx in range(1, 25):
            self.assertIn(f'id="news-card-{idx}"', self.html)
            
        # Verify filter badge is localized
        self.assertIn('实时筛选', self.html)
        self.assertIn('Penapis Langsung', self.html)

    def test_utility_cards_chinese_integrity(self):
        """Verify municipal utility cards have complete Chinese texts without leakage."""
        for u in self.utilities:
            uid = u.get("id")
            label_zh = u.get("label", "")
            status_zh = u.get("status", "")
            issue_zh = u.get("issue", "")
            source_zh = u.get("source", "")

            self.assertTrue(len(label_zh) > 0, f"Card {uid} missing Chinese label")
            self.assertTrue(len(status_zh) > 0, f"Card {uid} missing Chinese status")
            self.assertTrue(len(issue_zh) > 0, f"Card {uid} missing Chinese issue")
            self.assertTrue(len(source_zh) > 0, f"Card {uid} missing Chinese source")
            self.assertIsNotNone(self.chinese_char_pattern.search(issue_zh))

if __name__ == '__main__':
    unittest.main()
