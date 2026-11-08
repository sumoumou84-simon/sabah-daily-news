import unittest
import json
import re
import os

class TestBMLanguageIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.news_file = "news_data.json"
        cls.index_file = "index.html"
        
        with open(cls.news_file, "r", encoding="utf-8") as f:
            cls.data = json.load(f)
        cls.headlines = cls.data.get("headlines", [])
        cls.utilities = cls.data.get("utilities", [])
        
        with open(cls.index_file, "r", encoding="utf-8") as f:
            cls.html = f.read()

        cls.chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')

    def test_all_24_articles_present(self):
        """Verify exactly 24 articles exist in the published edition."""
        self.assertEqual(len(self.headlines), 24, "Edition must contain exactly 24 articles.")

    def test_complete_bm_headlines(self):
        """Verify all 24 articles have complete, non-empty BM headlines without Chinese characters."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            title_bm = item.get("titleBM", "").strip()
            self.assertTrue(len(title_bm) > 10, f"Article {hid} ({idx+1}) must have a valid titleBM.")
            # Check for Chinese characters
            zh_match = self.chinese_char_pattern.search(title_bm)
            self.assertIsNone(zh_match, f"Article {hid} titleBM contains forbidden Chinese character '{zh_match.group(0) if zh_match else ''}' in: {title_bm}")

    def test_complete_bm_summaries(self):
        """Verify all 24 articles have complete BM detail content without Chinese characters or HTML tags."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            detail_bm = item.get("detailBM", "").strip()
            self.assertTrue(len(detail_bm) > 50, f"Article {hid} ({idx+1}) must have a substantive detailBM.")
            
            # Check for Chinese characters
            zh_match = self.chinese_char_pattern.search(detail_bm)
            self.assertIsNone(zh_match, f"Article {hid} detailBM contains forbidden Chinese character '{zh_match.group(0) if zh_match else ''}'")
            
            # Check for raw leaked HTML tags (<ol>, <li>, <a>)
            self.assertNotIn("<ol>", detail_bm, f"Article {hid} detailBM must not contain raw <ol> tag.")
            self.assertNotIn("<li>", detail_bm, f"Article {hid} detailBM must not contain raw <li> tag.")
            self.assertNotIn("<a href=", detail_bm, f"Article {hid} detailBM must not contain raw <a> tag.")

    def test_required_bm_fields_presence(self):
        """Verify required language-dependent fields exist for every article."""
        for idx, item in enumerate(self.headlines):
            hid = item.get("id")
            self.assertTrue(bool(item.get("sourceBM")), f"Article {hid} missing sourceBM.")
            self.assertTrue(bool(item.get("tagBM")), f"Article {hid} missing tagBM.")
            self.assertTrue(bool(item.get("locationBM")), f"Article {hid} missing locationBM.")
            self.assertTrue(bool(item.get("verifiedBM")), f"Article {hid} missing verifiedBM.")

    def test_factual_immutability_between_languages(self):
        """Verify that bilingual representation preserves identical IDs, dates, categories and URLs."""
        for item in self.headlines:
            hid = item.get("id")
            self.assertTrue(hid.startswith("art_"), f"Invalid ID format: {hid}")
            self.assertIn(item.get("category"), ["sabah", "national", "sports", "general"])
            self.assertTrue(item.get("url").startswith("http"), f"Missing URL for {hid}")
            self.assertTrue(bool(item.get("original_published_at") or item.get("date")))

    def test_utility_cards_bm_integrity(self):
        """Verify all municipal utility cards have complete BM translations."""
        for idx, u in enumerate(self.utilities):
            uid = u.get("id")
            label_bm = u.get("labelBM", "")
            status_bm = u.get("statusBM", "")
            issue_bm = u.get("issueBM", "")
            source_bm = u.get("sourceBM", "")
            
            self.assertTrue(len(label_bm) > 0, f"Utility card {uid} missing labelBM")
            self.assertTrue(len(status_bm) > 0, f"Utility card {uid} missing statusBM")
            self.assertTrue(len(issue_bm) > 0, f"Utility card {uid} missing issueBM")
            self.assertTrue(len(source_bm) > 0, f"Utility card {uid} missing sourceBM")
            
            # Check for Chinese characters in BM fields
            for field_name, val in [("labelBM", label_bm), ("statusBM", status_bm), ("sourceBM", source_bm)]:
                zh_match = self.chinese_char_pattern.search(val)
                self.assertIsNone(zh_match, f"Utility card {uid} {field_name} contains Chinese: {val}")

    def test_index_html_marquee_has_bm(self):
        """Verify index.html marquee track contains dedicated .lang-bm elements."""
        self.assertIn('class="lang-bm hidden"', self.html, "HTML must contain .lang-bm hidden elements.")
        self.assertIn('【FOKUS UTAMA HARI INI】', self.html, "HTML marquee must contain BM focus header.")
        self.assertIn('Naik Taraf ICU Hospital Duchess of Kent Sandakan', self.html, "HTML marquee must contain BM Duchess of Kent news.")

if __name__ == '__main__':
    unittest.main()
