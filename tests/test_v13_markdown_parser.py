#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dedicated Unit Tests for Version 1.3 Pure Chinese News Format:
1. Extract Part 1: 【通告类型】【通告标题】【详细内容】【发布机构】【状态】
2. Extract Part 2: (沙巴山打根, 全国新闻, 体育新闻, 综合) + 【正文】【来源】【状态】
   Strictly enforce news_items = news_items[:15]
3. Extract Part 3: 【活动名称】【活动日期】【活动时间】【活动地点】【活动内容】【主办单位】
4. Remove BM splitting and URL extraction, clean backslash escapes.
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.gdrive_reader import GDriveMarkdownReader

class TestVersion13MarkdownParser(unittest.TestCase):

    def setUp(self):
        self.reader = GDriveMarkdownReader()
        
        # Build synthetic Version 1.3 Markdown with backslash escapes, notices, 18 news items, and events
        md_parts = [
            "# 西门看看网 Simon Kankan · 2026-11-12",
            "**版本：Version 1.3 纯中文格式**",
            "",
            "## 第一部分：民生通告",
            "### 1. 道路维修通告",
            r"- \【通告类型\】：市政交通",
            r"- \【通告标题\】：MPS 山打根市议会道路维修",
            r"- \【详细内容\】：Jalan Leila 进行路面修补，预计傍晚竣工。",
            r"- \【发布机构\】：山打根市议会 (MPS)",
            r"- \【状态\】：LIVE 抢修中",
            "",
            "### 2. 水管爆裂抢修",
            "- 【通告类型】：供水维护",
            "- 【通告标题】：JANS 沙巴水务局紧急抢修",
            "- 【详细内容】：Borneo Cove 前大桥主水管爆裂。",
            "- 【发布机构】：沙巴水务局 (JANS)",
            "- 【状态】：LIVE 维护",
            "",
            "## 第二部分：重点新闻",
            "### 沙巴山打根"
        ]
        
        # 6 Sabah Sandakan items
        for i in range(1, 7):
            md_parts.extend([
                f"### {i}. 沙巴山打根重点新闻第 {i} 篇报道标题",
                f"- \\【正文\\】：这是沙巴山打根重点民生新闻正文详情第 {i} 条，内容详实准确。",
                f"- \\【来源\\】：沙巴星洲日报, 诗华日报",
                f"- \\【状态\\】：已核实",
                ""
            ])
            
        md_parts.append("### 全国新闻")
        # 4 National items
        for i in range(7, 11):
            md_parts.extend([
                f"### {i}. 全国政经要闻第 {i} 篇报道标题",
                f"- 【正文】：这是全国政经新闻正文第 {i} 条，报道国会及联邦最新动向。",
                f"- 【来源】：马新社 (Bernama), 东方日报",
                f"- 【状态】：已核实",
                ""
            ])

        md_parts.append("### 体育新闻")
        # 4 Sports items
        for i in range(11, 15):
            md_parts.extend([
                f"### {i}. 体育焦点赛事第 {i} 篇报道标题",
                f"- 【正文】：这是体育比赛焦点新闻第 {i} 条，报道羽球及足球最新赛事战况。",
                f"- 【来源】：每日快报 (Daily Express), 大马足协",
                f"- 【状态】：已核实",
                ""
            ])

        md_parts.append("### 综合")
        # 4 General items (Total news items = 6 + 4 + 4 + 4 = 18 items)
        for i in range(15, 19):
            md_parts.extend([
                f"### {i}. 综合社会百态第 {i} 篇报道标题",
                f"- 【正文】：这是社会百态综合新闻第 {i} 条，记录东马社会民生最新万象。",
                f"- 【来源】：中国报, 光明日报",
                f"- 【状态】：已核实",
                ""
            ])

        md_parts.extend([
            "## 第三部分：活动通告",
            "### 1. 中医药大型公益义诊",
            r"- \【活动名称\】：2026 山打根客家公会中医药义诊与健康科普日",
            r"- \【活动日期\】：2026-11-20",
            r"- \【活动时间\】：08:30 AM - 01:00 PM",
            r"- \【活动地点\】：Dewan Hakka Sandakan",
            r"- \【活动内容\】：为关怀东海岸长者身心健康，举办大型公益义诊，现场设把脉问诊与免费体检。",
            r"- \【主办单位\】：山打根客家公会、山打根卫生局",
            "",
            "### 2. 婆罗洲生态环保开放日",
            "- 【活动名称】：西必洛生态环保公众开放日",
            "- 【活动日期】：2026-11-25",
            "- 【活动时间】：09:00 AM - 04:00 PM",
            "- 【活动地点】：Sepilok Discovery Centre",
            "- 【活动内容】：热带雨林科普开放日，普及侏儒象保护与雨林生态安全。",
            "- 【主办单位】：沙巴野生动物局 (SWD)"
        ])
        
        self.sample_v13_md = "\n".join(md_parts)

    def test_v13_parsing_and_extraction(self):
        stories = self.reader.parse_markdown(self.sample_v13_md, "2026-11-12")
        
        # 1. Verify Part 1 (Utilities)
        self.assertTrue(hasattr(self.reader, "parsed_utilities"))
        self.assertEqual(len(self.reader.parsed_utilities), 2)
        u1 = self.reader.parsed_utilities[0]
        self.assertEqual(u1["notice_type"], "市政交通")
        self.assertIn("MPS 山打根市议会", u1["title"])
        self.assertIn("Jalan Leila", u1["detail"])
        self.assertEqual(u1["publisher"], "山打根市议会 (MPS)")
        self.assertEqual(u1["status"], "LIVE 抢修中")
        
        # Verify conversion to website utilities schema
        web_utils = self.reader.convert_utilities_to_website_format(self.reader.parsed_utilities, "2026-11-12")
        self.assertEqual(len(web_utils), 2)
        self.assertEqual(web_utils[0]["status"], "LIVE 抢修中")
        self.assertTrue(web_utils[0]["is_live"])
        self.assertTrue(web_utils[0]["verified"])

        # 2. Verify Part 2 (News items) - must be truncated to exactly 15 items!
        news_stories = [s for s in stories if not s.is_event]
        self.assertEqual(len(news_stories), 15, "news_items must be strictly truncated to at most 15 items")
        
        # Verify 4 sections present
        categories = {s.category for s in news_stories}
        self.assertIn("sabah", categories)
        self.assertIn("national", categories)
        self.assertIn("sports", categories)
        self.assertIn("general", categories)
        
        # Verify news fields
        for s in news_stories:
            self.assertTrue(len(s.title) > 0)
            self.assertTrue(len(s.body) > 0)
            self.assertTrue(len(s.sources) > 0)
            # Verify no URLs in sources
            for src in s.sources:
                self.assertFalse(src.startswith("http"))
            # Pure Chinese: title_bm equals title
            self.assertEqual(s.title_bm, s.title)

        # 3. Verify Part 3 (Events)
        event_stories = [s for s in stories if s.is_event]
        self.assertEqual(len(event_stories), 2)
        ev1 = event_stories[0]
        self.assertIn("客家公会", ev1.title)
        self.assertEqual(ev1.date, "2026-11-20")
        self.assertEqual(ev1.event_metadata["time"], "08:30 AM - 01:00 PM")
        self.assertEqual(ev1.event_metadata["location"], "Dewan Hakka Sandakan")
        self.assertIn("把脉问诊", ev1.body)
        self.assertIn("客家公会", ev1.sources[0])

        # 4. Verify direct pass-through conversion
        headlines, events = self.reader.convert_stories_to_direct_output(stories, "2026-11-12")
        self.assertEqual(len(headlines), 15)
        self.assertEqual(len(events), 2)
        self.assertEqual(headlines[0]["title"], news_stories[0].title)
        self.assertEqual(headlines[0]["titleBM"], news_stories[0].title)

    def test_gdoc_plain_text_without_hash_headings_20261119(self):
        """
        Verify that Version 1.3 plaintext export from Google Docs without markdown '#' headings
        (like 2026-11-19) correctly extracts utilities, separates all news items,
        truncates dirty status tags, and filters empty event placeholder blocks.
        """
        raw_gdoc_text = (
            "\ufeff西门看看网 2026-11-19\r\n"
            "第一部分 民生通告 仅限山打根地区\r\n"
            "1\r\n"
            "【通告类型】气象提醒 【通告标题】山打根今日午后多雷阵雨，出门带伞注意行车安全 【详细内容】山打根今日白天最高气温约29至30度，最低约25度，上午多云间有阵雨，午后起多地有分散性雷阵雨，降雨概率较高，傍晚至夜间仍有阵雨，湿度较高，户外活动和骑行请留意天气变化，低洼路段注意积水。 【发布机构】气象预报综合整理 【状态】提醒中\r\n"
            "2\r\n"
            "【通告类型】市场民生 【通告标题】金凤市场通风风扇安装工程引关注，摊贩盼市议会提前沟通 【详细内容】位于山打根峇都4的金凤市场近日进行通风风扇安装等提升工程，期间市场内摊位减少、人流受影响，有摊贩反映未提前收到市议会正式通知，盼当局提前说明工程时间、临时安排和复业安排，减少对小贩生意的影响。 【发布机构】山打根市议会及当地州议员跟进整理 【状态】跟进中\r\n"
            "第二部分 重点新闻\r\n"
            "[沙巴][1] 沙砂增国席修宪日期未定，政府称仍需研究\r\n"
            "【正文】首相署部长慕斯达法指出，政府同意提高沙巴和砂拉越在国会的代表比例，但目前尚未敲定提呈联邦宪法修正案的具体日期，仍需从法律、技术和选区划分等方面研究，并与相关方协商。 【来源】光明日报 【状态】已确认\r\n"
            "[沙巴][2] 山打根陆路交通局与伊罗普拉州议员开会，商讨地方交通事务\r\n"
            "【正文】山打根陆路交通局与伊罗普拉州议员张克骏团队在山打根陆路交通局办事处召开工作协调会，重点讨论改进山打根公共交通规划、改善热门路段巴士候车亭设施以及提升交警与陆路局联合执法频率等议题。 【来源】诗华日报 【状态】已确认\r\n"
            "第三部分 未来活动通告\r\n"
            "本板块留空。过去24小时内未核实到山打根最新公布、符合条件的新活动，未用旧活动凑数。\r\n"
        )
        stories = self.reader.parse_markdown(raw_gdoc_text, "2026-11-19")
        self.assertEqual(len(stories), 2)
        self.assertEqual(stories[0].title, "沙砂增国席修宪日期未定，政府称仍需研究")
        self.assertEqual(stories[0].category, "sabah")
        self.assertEqual(stories[1].title, "山打根陆路交通局与伊罗普拉州议员开会，商讨地方交通事务")

        # Verify utilities
        self.assertEqual(len(self.reader.parsed_utilities), 2)
        u1 = self.reader.parsed_utilities[0]
        u2 = self.reader.parsed_utilities[1]
        self.assertEqual(u1["status"], "提醒中")
        self.assertEqual(u2["status"], "跟进中")

        web_utils = self.reader.convert_utilities_to_website_format(self.reader.parsed_utilities, "2026-11-19")
        self.assertEqual(web_utils[0]["status"], "提醒中")
        self.assertEqual(web_utils[0]["recovery"], "通告状态：提醒中")
        self.assertEqual(web_utils[1]["status"], "跟进中")
        self.assertEqual(web_utils[1]["recovery"], "通告状态：跟进中")
        # Ensure no placeholder or subsequent part leak
        self.assertNotIn("第三部分", web_utils[1]["status"])
        self.assertNotIn("本板块留空", web_utils[1]["status"])

    def test_clean_status_tag_robustness(self):
        """Test status tag cleaning against multiline leaks, numbers, and section headers."""
        from pipeline.gdrive_reader import clean_status_tag
        self.assertEqual(clean_status_tag("提醒中\r\n2"), "提醒中")
        self.assertEqual(clean_status_tag("已确认\r\n第三部分 未来活动通告\r\n本板块留空。过去24小时内未核实到山打根最新公布、符合条件的新活动，未用旧活动凑数。"), "已确认")
        self.assertEqual(clean_status_tag("进行中\n2."), "进行中")
        self.assertEqual(clean_status_tag("LIVE 抢修中\n3"), "LIVE 抢修中")
        self.assertEqual(clean_status_tag("本板块留空"), "已确认")
        self.assertEqual(clean_status_tag("通告状态：跟进中"), "跟进中")

    def test_track_b_language_handling(self):
        """Verify Track B prioritizes Chinese articles and translates English/Malay fallbacks."""
        from collectors.base import RawArticle
        from pipeline.synthesizer import NewsSynthesizer
        synth = NewsSynthesizer()

        art_en = RawArticle(
            title="Five seriously injured after tour bus crashes in Sabah",
            snippet="A tour bus crashed in Sabah injuring five passengers.",
            body="A tour bus crashed in Sabah injuring five passengers.",
            url="https://example.com/en1",
            source="The Borneo Post",
            category="sabah",
            extra={"corroborating_sources": ["The Borneo Post"]}
        )
        art_zh = RawArticle(
            title="沙巴州议会召开特别会议讨论财政预算",
            snippet="沙巴州议会今日召开特别会议。",
            body="沙巴州议会今日召开特别会议。",
            url="https://example.com/zh1",
            source="星洲日报",
            category="sabah",
            extra={"corroborating_sources": ["星洲日报"]}
        )

        out = synth.synthesize_track_b_standalone("2026-11-19", [art_en, art_zh])
        self.assertEqual(len(out), 2)
        # Chinese article must come first
        self.assertEqual(out[0]["title"], "沙巴州议会召开特别会议讨论财政预算")
        # English article must have been translated to Chinese title or have Chinese tag
        self.assertTrue(synth._is_chinese_text(out[1]["title"]))
        # BM title should preserve original
        self.assertEqual(out[1]["titleBM"], "Five seriously injured after tour bus crashes in Sabah")

if __name__ == "__main__":
    unittest.main()
