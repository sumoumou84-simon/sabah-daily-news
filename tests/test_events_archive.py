import os
import sys
import json
import tempfile
import unittest
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.gdrive_reader import (
    sync_events_archive,
    parse_date_range,
    normalize_event_core_title,
    compute_event_similarity,
    is_same_event_record
)
import build_news


class TestEventsArchiveLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.archive_file = os.path.join(self.temp_dir.name, "test_events_archive.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_parse_date_range(self):
        """测试活动起止日期解析引擎"""
        s, e = parse_date_range("2026-11-14", "2026-11-12")
        self.assertEqual(s, "2026-11-14")
        self.assertEqual(e, "2026-11-14")

        s, e = parse_date_range("11月14日到11月26日", "2026-11-12")
        self.assertEqual(s, "2026-11-14")
        self.assertEqual(e, "2026-11-26")

        s, e = parse_date_range("11月14日 - 11月16日", "2026-11-12")
        self.assertEqual(s, "2026-11-14")
        self.assertEqual(e, "2026-11-16")

        s, e = parse_date_range("11月14-18日", "2026-11-12")
        self.assertEqual(s, "2026-11-14")
        self.assertEqual(e, "2026-11-18")

        s, e = parse_date_range("2026-11-14 至 2026-11-20", "2026-11-12")
        self.assertEqual(s, "2026-11-14")
        self.assertEqual(e, "2026-11-20")

    def test_02_new_event_first_seen_date(self):
        """测试首次收录新活动时自动记录 first_seen_date 为今日 (MYT)"""
        today_iso = "2026-11-12"
        events = [
            {
                "name": "山打根国际马拉松赛 2026",
                "full_date": "2026-11-20",
                "desc": "年度马拉松盛事",
                "location": "市区大草场",
                "time": "06:00 AM"
            }
        ]
        res = sync_events_archive(events, today_iso, archive_file=self.archive_file)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["first_seen_date"], "2026-11-12")
        self.assertEqual(res[0]["countdown_days"], 8)
        self.assertTrue(os.path.exists(self.archive_file))

    def test_03_deduplication_and_preserve_first_seen_date(self):
        """测试已存在活动保留原 first_seen_date 并刷新详情"""
        # Day 1: 首次收录于 11-10
        day1 = "2026-11-10"
        initial_events = [
            {
                "name": "山打根客家公会中医药义诊",
                "full_date": "2026-11-15",
                "desc": "初步简述",
                "location": "客家大礼堂",
                "time": "08:30 AM"
            }
        ]
        sync_events_archive(initial_events, day1, archive_file=self.archive_file)

        # Day 2: 11-12 再次解析到该活动，标题微调带有官方标签，详情更新
        day2 = "2026-11-12"
        refreshed_events = [
            {
                "name": "【官方通告】山打根客家公会中医药义诊与健康日",
                "full_date": "2026-11-15",
                "desc": "更新后的更详尽描述，新增免费血压测试",
                "location": "客家公会大礼堂 A 厅",
                "time": "08:30 AM - 01:00 PM",
                "tel": "089-213388"
            }
        ]
        res = sync_events_archive(refreshed_events, day2, archive_file=self.archive_file)
        self.assertEqual(len(res), 1)
        # 必须保留 Day 1 的 first_seen_date
        self.assertEqual(res[0]["first_seen_date"], "2026-11-10")
        # 详情必须被刷新
        self.assertIn("更新后的更详尽描述", res[0]["desc"])
        self.assertEqual(res[0]["location"], "客家公会大礼堂 A 厅")
        self.assertEqual(res[0]["countdown_days"], 3)

    def test_03b_location_and_core_keywords_overlap_dedup(self):
        """测试不同媒体改换标题报道时，起始日期相同且地点关键词（如 Harbour Mall、RDC 等）或核心词重叠即判定为同一活动"""
        # Day 1: 11-10 首次收录 Harbour Mall 市集与 RDC 导览
        day1 = "2026-11-10"
        initial_events = [
            {
                "name": "山打根市区周末市集",
                "full_date": "2026-11-14",
                "desc": "本地美食文创摊位",
                "location": "Harbour Mall，山打根市区",
                "time": "全天"
            },
            {
                "name": "山打根热带雨林探索中心生态导览",
                "full_date": "2026-11-16",
                "desc": "婆罗洲雨林保育讲解",
                "location": "热带雨林探索中心 RDC，Sepilok",
                "time": "09:00 AM"
            }
        ]
        sync_events_archive(initial_events, day1, archive_file=self.archive_file)

        # Day 2: 11-12 其他报社以全新标题报道相同地点与日期的活动
        day2 = "2026-11-12"
        rewritten_events = [
            {
                "name": "港口文创市集周六登场 汇集数十家摊贩",  # 标题彻底重写，但同一天且地点包含 Harbour Mall
                "full_date": "2026-11-14",
                "desc": "欢迎各界前来品尝道地美食",
                "location": "Harbour Mall 广场",
                "time": "10:00 AM - 08:00 PM"
            },
            {
                "name": "西必洛亲子自然雨林探索之旅",  # 标题重写，但同一天且地点包含 RDC
                "full_date": "2026-11-16",
                "desc": "专业向导带队游览",
                "location": "RDC Sepilok",
                "time": "09:00 AM - 04:00 PM"
            }
        ]
        res = sync_events_archive(rewritten_events, day2, archive_file=self.archive_file)
        self.assertEqual(len(res), 2)
        # 两项活动均应成功匹配，保留 Day 1 的 first_seen_date (2026-11-10)，不应被误判为今日新收 (2026-11-12)
        mall_ev = next(e for e in res if "Harbour Mall" in e["location"])
        rdc_ev = next(e for e in res if "RDC" in e["location"])
        self.assertEqual(mall_ev["first_seen_date"], "2026-11-10")
        self.assertEqual(rdc_ev["first_seen_date"], "2026-11-10")
        # 且详情更新为最新内容
        self.assertIn("港口文创市集", mall_ev["name"])
        self.assertIn("西必洛亲子自然雨林", rdc_ev["name"])

    def test_03c_archive_self_deduplication(self):
        """测试加载归档库时对自身历史遗留重复项的内部自我去重与合并"""
        # 模拟归档库中已存在两条重复项（如山打根市区周末市集）
        duplicate_archive = [
            {
                "id": 1,
                "name": "南砂免费义肢最后调试活动",
                "full_date": "2026-11-12",
                "location": "以主办单位公布地点为准",
                "first_seen_date": "2026-11-12"
            },
            {
                "id": 2,
                "name": "山打根市区周末市集",
                "full_date": "2026-11-14",
                "location": "Harbour Mall，山打根市区",
                "desc": "周末市集汇集本地小吃",
                "first_seen_date": "2026-11-10"
            },
            {
                "id": 3,
                "name": "山打根市区周末市集",
                "full_date": "2026-11-14",
                "location": "Harbour Mall，山打根市区",
                "desc": "周末市集汇集本地小吃",
                "first_seen_date": "2026-11-12"
            }
        ]
        with open(self.archive_file, "w", encoding="utf-8") as f:
            json.dump(duplicate_archive, f, ensure_ascii=False)

        today_iso = "2026-11-12"
        # 即使 incoming_events 为空，自我去重也能彻底合并多余重复项并保留最早的 first_seen_date
        res = sync_events_archive([], today_iso, archive_file=self.archive_file)
        self.assertEqual(len(res), 2)
        names = [e["name"] for e in res]
        self.assertEqual(names.count("山打根市区周末市集"), 1)
        market_ev = next(e for e in res if e["name"] == "山打根市区周末市集")
        self.assertEqual(market_ev["first_seen_date"], "2026-11-10")

    def test_04_cleanup_expired_events(self):
        """测试自动清理结束日期早于今日 (MYT) 的已过期活动"""
        # 先在归档库中写入一个已过期的活动 (11-10 结束) 和一个未来的活动 (11-18 结束)
        old_data = [
            {
                "name": "已结束的净滩活动",
                "full_date": "2026-11-09",
                "end_date": "2026-11-10",
                "first_seen_date": "2026-11-05"
            },
            {
                "name": "未来的生态导览活动",
                "full_date": "2026-11-18",
                "end_date": "2026-11-18",
                "first_seen_date": "2026-11-11"
            }
        ]
        with open(self.archive_file, "w", encoding="utf-8") as f:
            json.dump(old_data, f, ensure_ascii=False)

        # 运行于 2026-11-12
        today_iso = "2026-11-12"
        res = sync_events_archive([], today_iso, archive_file=self.archive_file)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "未来的生态导览活动")
        # 验证已结束活动被彻底剔除
        with open(self.archive_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["name"], "未来的生态导览活动")

    def test_05_smart_badge_pinning_and_ordering(self):
        """测试排序：first_seen_date == 今日 置顶，次日自动褪去角标并按倒计时由近及远排列"""
        today_iso = "2026-11-12"
        # 现有活动（昨日收录）：距离今天 2 天 (11-14)
        # 新收录活动（今日收录）：距离今天 5 天 (11-17)
        # 现有活动（前日收录）：距离今天 1 天 (11-13)
        incoming = [
            {
                "name": "昨日旧活动 1",
                "full_date": "2026-11-14",
                "first_seen_date": "2026-11-11"
            },
            {
                "name": "前日旧活动 2",
                "full_date": "2026-11-13",
                "first_seen_date": "2026-11-10"
            }
        ]
        with open(self.archive_file, "w", encoding="utf-8") as f:
            json.dump(incoming, f, ensure_ascii=False)

        # 今日新录入一个举办日期更远的活动
        new_event = [
            {
                "name": "今日最新收录活动",
                "full_date": "2026-11-17"
            }
        ]
        res = sync_events_archive(new_event, today_iso, archive_file=self.archive_file)
        self.assertEqual(len(res), 3)

        # 验证置顶：今日新收录的活动排在第一位（置顶）
        self.assertEqual(res[0]["name"], "今日最新收录活动")
        self.assertEqual(res[0]["first_seen_date"], "2026-11-12")

        # 验证次要排序：旧活动按倒计时由近及远排列 (11-13 在前，11-14 在后)
        self.assertEqual(res[1]["name"], "前日旧活动 2")
        self.assertEqual(res[1]["countdown_days"], 1)
        self.assertEqual(res[2]["name"], "昨日旧活动 1")
        self.assertEqual(res[2]["countdown_days"], 2)


class TestFrontendHeaderAndCardSeparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_news.generate_index_html()
        with open("index.html", "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_01_top_navbar_cleaned(self):
        """测试顶部导航栏旧黄色中文按钮已彻底清除，保留精简3大控件"""
        self.assertNotIn("id=\"btn-lang-zh\"", self.html)
        self.assertNotIn("class=\"lang-switcher-box", self.html)
        self.assertIn("id=\"btn-theme-toggle\"", self.html)
        self.assertIn("wa.me/60109301117", self.html)
        self.assertIn("id=\"translate-dropdown-container\"", self.html)

    def test_02_section_header_single_line_and_compact(self):
        """测试活动板块标题单行不折行，移动端隐藏冗余说明胶囊"""
        self.assertIn("沙巴活动预告与倒计时", self.html)
        # 强制 whitespace-nowrap
        self.assertIn('whitespace-nowrap shrink-0">\n                                <span class="lang-zh">沙巴活动预告与倒计时</span>', self.html)
        # 始终可见说明胶囊在移动端隐藏 (hidden md:inline-flex)
        self.assertIn('hidden md:inline-flex items-center gap-1 px-2 py-[1px] rounded-full border text-[10px] mono sub-meta-text shrink-0', self.html)

    def test_03_card_collapsed_vs_expanded_separation(self):
        """测试卡片折叠态只显示日期+完整标题+角标/倒计时徽章，地点移入展开抽屉"""
        # 折叠态没有 event-subtitle
        self.assertNotIn("class=\"event-subtitle", self.html)
        # 展开抽屉包含地点、时间、主办方
        self.assertIn("活动地点：", self.html)
        self.assertIn("活动时间：", self.html)
        self.assertIn("主办/信源：", self.html)

    def test_04_events_grid_container_items_start(self):
        """测试电脑端网格容器带有 items-start，杜绝卡片展开时折叠卡片被强行拉伸留白"""
        self.assertIn('id="events-grid-container"', self.html)
        self.assertIn('grid grid-cols-1 md:grid-cols-2 gap-2 items-start', self.html)


if __name__ == "__main__":
    unittest.main()
