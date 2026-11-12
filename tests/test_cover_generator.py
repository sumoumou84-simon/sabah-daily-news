#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：杂志风封面动态合成引擎与本地底图库校验 (tests/test_cover_generator.py)
"""

import os
import sys
import unittest
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from pipeline.cover_generator import (
    CoverGenerator,
    generate_covers_for_headlines,
    get_best_font_path,
    load_font,
    clean_old_covers,
    create_bottom_gradient_mask,
    BG_POOL_DIR,
    COVERS_DIR
)

class TestCoverGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = CoverGenerator()

    def test_01_bg_pool_categories_and_dimensions(self):
        """测试 4 个分类底图库完备性与 1200x675 统一分辨率"""
        self.assertTrue(BG_POOL_DIR.exists(), "assets/bg_pool 目录不存在")
        categories = ["sabah", "national", "sports", "general"]
        total_images = 0

        for cat in categories:
            cat_dir = BG_POOL_DIR / cat
            self.assertTrue(cat_dir.exists(), f"分类目录 assets/bg_pool/{cat} 不存在")
            images = list(cat_dir.glob("*.jpg"))
            self.assertGreater(len(images), 0, f"分类 {cat} 底图库为空")
            total_images += len(images)

            # 抽样检查首张图片尺寸
            sample = images[0]
            with Image.open(sample) as img:
                self.assertEqual(img.size, (1200, 675), f"{sample.name} 尺寸不为 1200x675")
                self.assertEqual(img.mode, "RGB", f"{sample.name} 色彩模式不为 RGB")

        self.assertGreaterEqual(total_images, 30, f"底图库总数过少: {total_images}")

    def test_02_font_loading_and_chinese_support(self):
        """测试中文字体成功加载且能正确测量中文字符"""
        font_path = get_best_font_path()
        print(f"\n[*] 当前测试环境加载的中文字体: {font_path}")
        font = load_font(32)
        self.assertIsNotNone(font)
        # 测试中文字符绘制尺寸不为 0
        bbox = font.getbbox("西门看看网 · 每日晨报")
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        self.assertGreater(width, 100, "中文字符测量宽度异常")
        self.assertGreater(height, 10, "中文字符测量高度异常")

    def test_03_smart_category_matching(self):
        """测试智能分类与关键词匹配"""
        gen = CoverGenerator()

        # 羽球关键词匹配
        bg_badminton = gen.select_background("sports", "李梓嘉出战熊本羽球公开赛跳杀得分")
        self.assertTrue(
            "badminton" in bg_badminton.name.lower() or "athlete" in bg_badminton.name.lower(),
            f"羽球新闻未匹配到羽球/运动员底图: {bg_badminton.name}"
        )

        # 足球关键词匹配
        bg_soccer = gen.select_background("sports", "Sabah FC 备战主场赛事足球门票热销")
        self.assertTrue(
            "soccer" in bg_soccer.name.lower(),
            f"足球新闻未匹配到足球底图: {bg_soccer.name}"
        )

        # 司法法庭关键词匹配
        bg_court = gen.select_background("national", "联邦法院审理沙巴40%净税收上诉案开庭")
        self.assertTrue(
            "scales" in bg_court.name.lower() or "gavel" in bg_court.name.lower() or "governmental" in bg_court.name.lower(),
            f"法庭新闻未匹配到天秤/法槌/政府大楼底图: {bg_court.name}"
        )

    def test_04_same_day_collision_prevention(self):
        """测试同日 14 条新闻绝不重复使用相同底图（零撞图）"""
        mock_headlines = [
            {"category": "sabah", "title": "山打根扫荡行动扣留71人"},
            {"category": "sabah", "title": "金凤市集周末关闭消毒"},
            {"category": "sabah", "title": "沙巴水警海上巡逻拦截走私船"},
            {"category": "sabah", "title": "神山雨林步道发现珍稀野生动物"},
            {"category": "sabah", "title": "州政府行政中心召开防灾会议"},
            {"category": "national", "title": "国会辩论财政预算案"},
            {"category": "national", "title": "反贪会提控涉嫌贪腐高官上诉案"},
            {"category": "national", "title": "东海岸季候风潮影响减弱"},
            {"category": "national", "title": "新机场航线扩建推动区域经济"},
            {"category": "sports", "title": "李梓嘉熊本大师赛止步入选赛"},
            {"category": "sports", "title": "Sabah FC 迎战吉打主场球迷呐喊"},
            {"category": "sports", "title": "大马百米飞人短跑健儿夺冠"},
            {"category": "general", "title": "警方发布电信网络诈骗防范预警"},
            {"category": "general", "title": "暴雨导致多地电力变电站抢修"},
        ]

        gen = CoverGenerator()
        matched_files = []
        for h in mock_headlines:
            bg = gen.select_background(h["category"], h["title"])
            matched_files.append(bg.name)

        unique_count = len(set(matched_files))
        self.assertEqual(unique_count, len(mock_headlines), f"存在重复底图！总数 {len(mock_headlines)}，唯一数 {unique_count}")

    def test_05_cover_generation_layout_and_gradient(self):
        """测试杂志风封面实际生成：尺寸、渐变分布与文件完整性"""
        gen = CoverGenerator()
        test_title = "山打根与兰瑙同步扫荡行动，71名涉案人员被依法扣留调查"
        cover_rel = gen.generate_cover(
            category="sabah",
            title=test_title,
            detail="警方依法突击检查",
            date_str="2026.11.12 · MYT",
            article_id="unit_test_01"
        )

        cover_path = BASE_DIR / cover_rel.lstrip("./")
        self.assertTrue(cover_path.exists(), f"生成的封面文件不存在: {cover_path}")

        with Image.open(cover_path) as img:
            self.assertEqual(img.size, (1200, 675))
            self.assertEqual(img.mode, "RGB")

        # 检查渐变遮罩矩阵：上半部分透明（0），下半部分渐增至 225
        gradient = create_bottom_gradient_mask(1200, 675, (10, 25, 47))
        # 50% 处 y = 337 应为完全透明 (alpha == 0)
        p_top = gradient.getpixel((600, 330))
        self.assertEqual(p_top[3], 0, "画面上半部分渐变层未保持 100% 透明")
        # 底部 y = 674 应达到深海蓝且 alpha == 225
        p_bottom = gradient.getpixel((600, 674))
        self.assertEqual(p_bottom[3], 225, "画面底部渐变层透明度未达到 225")

    def test_06_clean_old_covers(self):
        """测试 7 天旧封面自动清理逻辑"""
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        dummy_old = COVERS_DIR / "cover_dummy_old_test.jpg"
        dummy_old.write_bytes(b"dummy")
        # 修改文件时间为 10 天前
        past_ts = (Path(__file__).stat().st_mtime) - (10 * 86400)
        os.utime(dummy_old, (past_ts, past_ts))

        cleaned = clean_old_covers(days=7)
        self.assertGreaterEqual(cleaned, 1)
        self.assertFalse(dummy_old.exists(), "超过 7 天的旧封面未被清理")

if __name__ == "__main__":
    unittest.main()
