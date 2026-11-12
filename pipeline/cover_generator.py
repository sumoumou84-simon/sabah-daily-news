#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《西门看看网》Pillow 杂志风封面动态合成引擎 (pipeline/cover_generator.py)
特性：
1. 智能分类匹配与同日防撞图（12~15条新闻零重复底图）
2. 画面上半部分（0%~55%）明亮主体避让
3. 画面下半部分（55%~100%）深海蓝渐进遮罩 (RGBA alpha 0 -> 225)
4. 左上角金黄色圆角胶囊徽章（板块标签）
5. 右上角半透明深色圆角日期邮戳 (MYT)
6. 底部 1~2 行超大粗体白色新闻标题 + 金黄色品牌水印《西门看看网 · 每日晨报》
7. 自动清理 7 天前旧封面
"""

import os
import sys
import math
import hashlib
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
BG_POOL_DIR = BASE_DIR / "assets" / "bg_pool"
COVERS_DIR = BASE_DIR / "assets" / "covers"

MYT = timezone(timedelta(hours=8))

def get_myt_now() -> datetime:
    return datetime.now(MYT)

# 板块中文标签映射
CATEGORY_BADGE_MAP = {
    "sabah": "沙巴 · 山打根",
    "national": "全国政经",
    "sports": "体育焦点",
    "general": "综合百态",
}

# 关键词与底图文件名的特征词映射规则（智能加权评分）
KEYWORD_FILENAME_RULES = {
    "sports": [
        (["羽球", "羽毛球", "李梓嘉", "跳杀", "汤杯", "大师赛", "男单", "公开赛"], ["badminton", "jumping_smash"]),
        (["足球", "球赛", "进球", "sabah fc", "射门", "主场", "客场", "联赛"], ["soccer_player", "volley_kick"]),
        (["田径", "短跑", "起跑", "飞人", "金牌", "健儿", "跨栏"], ["sprinters", "starting"]),
    ],
    "sabah": [
        (["水警", "海警", "海事", "巡逻", "快艇", "走私", "偷渡", "截查", "大浪"], ["maritime_patrol_boat", "patrol_boat"]),
        (["夜市", "巴刹", "pasar", "摊贩", "市集", "关闭", "营业", "开市"], ["night_market", "lanterns_glowing_at_night_market"]),
        (["扫荡", "突击", "扣留", "逮捕", "盘查", "调查", "反贪", "落网", "嫌犯"], ["officers_inspecting_bus", "investigators"]),
        (["热带雨林", "雨林", "神山", "森林", "生态", "犀鸟", "保育", "观鸟"], ["rhinoceros_hornbill", "borneo_rainforest", "rainforest"]),
        (["州政府", "行政", "首长", "哈芝芝", "税收", "权益", "判决", "大厦", "议会"], ["sabah_state_administrative_center", "administrative_center"]),
        (["德士", "巴士", "客运", "车站", "枢纽", "司机", "客货车"], ["drivers_conversing", "taxis_lined_up"]),
        (["公路", "工程", "大桥", "泛婆", "大道", "建设", "工程师", "路段"], ["engineers_overlooking_highway"]),
        (["海洋", "潜水", "珊瑚", "海龟", "仙本那", "海岛", "浮潜"], ["underwater_coral_reef", "split_ocean_coral_reef"]),
    ],
    "national": [
        (["法院", "审理", "法官", "司法", "律师", "提控", "上诉", "判决", "反贪会"], ["golden_scales_of_justice", "golden_scales_and_gavel"]),
        (["国会", "首相", "安华", "政府", "解散", "大选", "补选", "竞选", "政党", "内阁", "议席", "国盟", "希盟"], ["governmental_pillars"]),
        (["机场", "航班", "飞机", "列车", "铁道", "高铁", "民航", "航空"], ["train_and_airplane"]),
        (["季候风", "东海岸", "风潮", "暴雨", "海浪"], ["train_and_airplane", "governmental_pillars"]),
    ],
    "general": [
        (["诈骗", "黑客", "网络", "防骗", "数字", "科技", "电诈", "安全", "人工智能"], ["digital_shield", "golden_digital_shield"]),
        (["断电", "停水", "供水", "变电站", "电网", "水务", "电缆", "维修", "电力", "sesb"], ["power_towers", "power_transmission", "utility_workers"]),
        (["暴雨", "水灾", "大雨", "洪灾", "淹水", "救援", "冲走", "积水", "气象局"], ["rainstorm", "tropical_rainstorm", "rescue_boat"]),
    ]
}

# 备选字体查找列表
FONT_CANDIDATES = [
    # Windows
    "C:/Windows/Fonts/msyhbd.ttc",       # 微软雅黑 Bold
    "C:/Windows/Fonts/msyh.ttc",         # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",       # 黑体
    "C:/Windows/Fonts/NotoSansSC-VF.ttf",# Noto Sans SC
    "C:/Windows/Fonts/simsun.ttc",       # 宋体
    # Linux / Ubuntu (GitHub Actions)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

_CACHED_FONT_PATH: Optional[str] = None

def get_best_font_path() -> Optional[str]:
    """探测并缓存最佳中文字体路径"""
    global _CACHED_FONT_PATH
    if _CACHED_FONT_PATH and os.path.exists(_CACHED_FONT_PATH):
        return _CACHED_FONT_PATH

    for fp in FONT_CANDIDATES:
        if os.path.exists(fp):
            _CACHED_FONT_PATH = fp
            return fp
    return None

def load_font(size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    """加载指定字号的中文字体，失败时返回系统默认"""
    fp = get_best_font_path()
    if fp:
        try:
            return ImageFont.truetype(fp, size=size, index=index)
        except Exception:
            try:
                return ImageFont.truetype(fp, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

def clean_old_covers(days: int = 7) -> int:
    """自动清理 covers 目录下超过指定天数的旧图片"""
    if not COVERS_DIR.exists():
        return 0
    now_ts = datetime.now().timestamp()
    limit_ts = now_ts - (days * 86400)
    cleaned = 0
    for f in COVERS_DIR.glob("*.jpg"):
        try:
            if f.stat().st_mtime < limit_ts:
                f.unlink()
                cleaned += 1
        except Exception:
            pass
    return cleaned

def create_bottom_gradient_mask(width: int = 1200, height: int = 675, navy_rgb: Tuple[int, int, int] = (10, 25, 47)) -> Image.Image:
    """
    创建深海蓝渐进遮罩层：
    画面上半部分（0%~55% 高度）完全透明（alpha=0），原图明亮主体 100% 完整展现；
    画面下半部分（55%~100% 高度）平滑过渡叠加深海蓝，RGBA 透明度平滑增至 225。
    """
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    y_start = int(height * 0.55)  # 371px
    span = float(height - 1 - y_start)
    for y in range(y_start, height):
        t = min(1.0, (y - y_start) / span)
        # 使用平滑缓动曲线：保证 55% 处羽化无硬边，底部达到 225
        alpha = int(round((t ** 1.3) * 225))
        draw.line([(0, y), (width, y)], fill=(navy_rgb[0], navy_rgb[1], navy_rgb[2], alpha))

    return gradient

# 全局缓存单例渐变层以提升大批量合成性能
_CACHED_GRADIENT: Optional[Image.Image] = None

def get_gradient_layer() -> Image.Image:
    global _CACHED_GRADIENT
    if _CACHED_GRADIENT is None:
        _CACHED_GRADIENT = create_bottom_gradient_mask(1200, 675, (10, 25, 47))
    return _CACHED_GRADIENT

class CoverGenerator:
    """
    杂志风封面动态合成器
    """
    def __init__(self, bg_pool_dir: Optional[Path] = None, covers_dir: Optional[Path] = None):
        self.bg_pool_dir = bg_pool_dir or BG_POOL_DIR
        self.covers_dir = covers_dir or COVERS_DIR
        self.covers_dir.mkdir(parents=True, exist_ok=True)
        self.used_images_today: Set[str] = set()
        self._load_all_pool_images()

    def _load_all_pool_images(self):
        """扫描并按板块归类所有可用底图"""
        self.pool_map: Dict[str, List[Path]] = {
            "sabah": [],
            "national": [],
            "sports": [],
            "general": []
        }
        if not self.bg_pool_dir.exists():
            return

        for cat in self.pool_map.keys():
            cat_dir = self.bg_pool_dir / cat
            if cat_dir.exists():
                imgs = [p for p in cat_dir.glob("*.jpg") if p.is_file()]
                self.pool_map[cat] = sorted(imgs, key=lambda x: x.name)

    def select_background(self, category: str, title: str, detail: str = "") -> Path:
        """
        智能底图匹配策略：
        1. 优先在对应板块分类中匹配最契合标题关键词的底图；
        2. 结合规则加权评分；
        3. 维护已用集合，同一日内绝不重复使用相同底图；
        4. 当前分类若耗尽，从 general 或其它板块补位；
        5. 终极兜底确保绝不空缺报错。
        """
        cat = category if category in self.pool_map else "general"
        search_text = f"{title} {detail}".lower()

        candidate_images = [img for img in self.pool_map.get(cat, []) if img.name not in self.used_images_today]

        # 如果本板块全部用尽，尝试备选板块中未使用的图片
        if not candidate_images:
            fallback_cats = ["general", "sabah", "national", "sports"]
            for f_cat in fallback_cats:
                unused = [img for img in self.pool_map.get(f_cat, []) if img.name not in self.used_images_today]
                if unused:
                    candidate_images = unused
                    cat = f_cat
                    break

        # 终极兜底：如果整个底图库都被用完（极端情况），放宽重用
        if not candidate_images:
            candidate_images = self.pool_map.get(cat, []) or self.pool_map.get("general", [])

        if not candidate_images:
            raise FileNotFoundError(f"底图库 assets/bg_pool/ 中没有可用图片！请先运行 scripts/import_bg_pool.py。")

        # 评分机制
        best_img = candidate_images[0]
        best_score = -1

        rules = KEYWORD_FILENAME_RULES.get(cat, [])
        for img in candidate_images:
            score = 0
            fname_lower = img.name.lower()

            for kw_list, pattern_list in rules:
                for kw in kw_list:
                    if kw.lower() in search_text:
                        for pat in pattern_list:
                            if pat in fname_lower:
                                score += 10

            # 标题部分直接词根命中
            for word in re.findall(r'[\w]+', fname_lower):
                if len(word) >= 4 and word in search_text:
                    score += 3

            if score > best_score:
                best_score = score
                best_img = img

        self.used_images_today.add(best_img.name)
        return best_img

    def wrap_title(self, text: str, font: ImageFont.FreeTypeFont, max_width: int = 1080) -> List[str]:
        """自适应将标题拆分为 1~2 行"""
        # 清除核实中括号等标签
        clean_text = re.sub(r'\[.*?\]', '', text).strip()

        # 测试单行是否放得下
        bbox = font.getbbox(clean_text)
        if (bbox[2] - bbox[0]) <= max_width:
            return [clean_text]

        # 拆分为 2 行
        total_len = len(clean_text)
        mid = total_len // 2
        # 寻找标点或空格作为优先折行点
        break_point = mid
        for offset in range(total_len // 4):
            for cand in [mid - offset, mid + offset]:
                if 0 < cand < total_len and clean_text[cand] in ["，", "、", " ", "：", "；", "—", "-"]:
                    break_point = cand + (0 if clean_text[cand] == " " else 1)
                    break
            if break_point != mid:
                break

        line1 = clean_text[:break_point].strip()
        line2 = clean_text[break_point:].strip()

        # 校验 line1 和 line2 宽度，若超长加省略号
        def clamp_line(line_str: str) -> str:
            while len(line_str) > 4 and (font.getbbox(line_str + "...")[2] - font.getbbox(line_str + "...")[0]) > max_width:
                line_str = line_str[:-1]
            return line_str + ("..." if len(line_str) < len(clean_text) else "")

        b1 = font.getbbox(line1)
        if (b1[2] - b1[0]) > max_width:
            line1 = clamp_line(line1)

        b2 = font.getbbox(line2)
        if (b2[2] - b2[0]) > max_width:
            line2 = clamp_line(line2)

        return [line1, line2]

    def generate_cover(
        self,
        category: str,
        title: str,
        detail: str = "",
        date_str: Optional[str] = None,
        article_id: Optional[str] = None
    ) -> str:
        """
        动态合成一张 1200x675 杂志风封面并保存为 jpg
        返回相对于仓库根目录的路径，如 './assets/covers/cover_xxx.jpg'
        """
        now = get_myt_now()
        date_display = date_str or now.strftime("%Y.%m.%d · MYT")
        date_file_prefix = now.strftime("%Y%m%d")

        # 1. 挑选底图
        bg_file = self.select_background(category, title, detail)

        # 2. 载入并缩放底图至 1200x675
        with Image.open(bg_file) as raw_img:
            if raw_img.mode != "RGB":
                raw_img = raw_img.convert("RGB")
            if raw_img.size != (1200, 675):
                raw_img = raw_img.resize((1200, 675), Image.Resampling.LANCZOS)
            canvas = raw_img.copy()

        # 3. 叠加底部深海蓝渐进遮罩（55%~100% 高度）
        canvas_rgba = canvas.convert("RGBA")
        gradient_layer = get_gradient_layer()
        canvas_composite = Image.alpha_composite(canvas_rgba, gradient_layer)

        # 创建用于绘制文字和矢量的图层
        draw_layer = Image.new("RGBA", (1200, 675), (0, 0, 0, 0))
        draw = ImageDraw.Draw(draw_layer)

        # 4. 左上角金黄色圆角胶囊徽章
        badge_text = CATEGORY_BADGE_MAP.get(category, "综合百态")
        badge_font = load_font(24)
        bb = badge_font.getbbox(badge_text)
        bw = bb[2] - bb[0]
        bh = bb[3] - bb[1]

        bx0, by0 = 48, 40
        b_pad_x, b_pad_y = 22, 10
        bx1 = bx0 + bw + (b_pad_x * 2)
        by1 = by0 + bh + (b_pad_y * 2)
        badge_radius = (by1 - by0) // 2

        # 绘制胶囊背景与文字
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=badge_radius, fill=(255, 214, 10, 245))
        # 居中文字
        bt_x = bx0 + b_pad_x - bb[0]
        bt_y = by0 + b_pad_y - bb[1]
        draw.text((bt_x, bt_y), badge_text, font=badge_font, fill=(15, 23, 42, 255))

        # 5. 右上角半透明深色圆角日期邮戳
        stamp_font = load_font(20)
        stamp_text = date_display
        sb = stamp_font.getbbox(stamp_text)
        sw = sb[2] - sb[0]
        sh = sb[3] - sb[1]

        s_pad_x, s_pad_y = 18, 10
        sx1 = 1200 - 48
        sx0 = sx1 - (sw + s_pad_x * 2)
        sy0 = 40
        sy1 = sy0 + sh + s_pad_y * 2
        stamp_radius = 12

        draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=stamp_radius, fill=(15, 23, 42, 185), outline=(255, 214, 10, 100), width=1)
        st_x = sx0 + s_pad_x - sb[0]
        st_y = sy0 + s_pad_y - sb[1]
        draw.text((st_x, st_y), stamp_text, font=stamp_font, fill=(248, 250, 252, 240))

        # 6. 底部新闻标题排版（自适应字号，确保 1~2 行内完美排布，无方块乱码）
        target_font_sizes = [50, 46, 42, 38]
        lines = []
        title_font = load_font(target_font_sizes[0])

        for fs in target_font_sizes:
            f_cand = load_font(fs)
            lines_cand = self.wrap_title(title, f_cand, max_width=1080)
            if len(lines_cand) <= 2:
                title_font = f_cand
                lines = lines_cand
                break
        if not lines:
            lines = self.wrap_title(title, title_font, max_width=1080)

        # 计算标题与品牌水印的垂直排版位置
        line_height = int(title_font.size * 1.35)
        total_title_h = len(lines) * line_height

        # 水印字体与文字
        brand_font = load_font(20)
        brand_text = "西门看看网 · 每日晨报"
        brb = brand_font.getbbox(brand_text)

        # 底部基准锚定：让品牌水印距底部约 36px
        brand_y = 675 - 38 - (brb[3] - brb[1])
        title_start_y = brand_y - total_title_h - 18

        # 绘制标题（带柔和阴影，确保在任何背景上极其清晰）
        for idx, line in enumerate(lines):
            ly = title_start_y + (idx * line_height)
            lx = 50
            # 阴影
            draw.text((lx + 2, ly + 2), line, font=title_font, fill=(0, 0, 0, 190))
            # 正文（纯白粗体）
            draw.text((lx, ly), line, font=title_font, fill=(255, 255, 255, 255))

        # 绘制品牌金色小字水印
        draw.text((52 + 1, brand_y + 1), brand_text, font=brand_font, fill=(0, 0, 0, 160))
        draw.text((52, brand_y), brand_text, font=brand_font, fill=(255, 214, 10, 255))

        # 合成最终图层并导出
        final_image = Image.alpha_composite(canvas_composite, draw_layer).convert("RGB")

        # 生成安全唯一文件名
        title_hash = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]
        art_id_str = f"_{article_id}" if article_id else ""
        filename = f"cover_{date_file_prefix}_{category}{art_id_str}_{title_hash}.jpg"
        output_path = self.covers_dir / filename

        final_image.save(output_path, "JPEG", quality=85, optimize=True)
        rel_path = f"./assets/covers/{filename}"
        return rel_path

def generate_covers_for_headlines(headlines: List[Dict[str, Any]], date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    为新闻列表批量生成专属封面，并注入 cover 与 cover_image 字段
    同时清理 7 天前旧封面
    """
    generator = CoverGenerator()
    cleaned = clean_old_covers(days=7)
    if cleaned > 0:
        print(f"[*] 自动清理 {cleaned} 张 7 天前历史旧封面")

    print(f"\n[+] 正在启动杂志风封面动态合成引擎 (共 {len(headlines)} 条新闻)...")
    for idx, item in enumerate(headlines, 1):
        cat = item.get("category", "general")
        title = item.get("title", "")
        detail = item.get("detail", "") or item.get("summary", "")
        art_id = str(item.get("id") or item.get("story_index") or idx)

        cover_path = generator.generate_cover(
            category=cat,
            title=title,
            detail=detail,
            date_str=date_str,
            article_id=art_id
        )
        item["cover"] = cover_path
        item["cover_image"] = cover_path
        print(f"    ✓ [{idx}/{len(headlines)}] [{cat}] {title[:20]}... -> {cover_path}")

    print(f"🎉 封面合成全部完成！当日已用不同底图: {len(generator.used_images_today)} 张（同日防撞图保证）\n")
    return headlines

if __name__ == "__main__":
    test_headlines = [
        {"category": "sports", "title": "李梓嘉止步熊本大师赛入选赛，大马男单调整再战", "detail": "羽球名将李梓嘉遗憾出局"},
        {"category": "sabah", "title": "山打根与兰瑙同步展开扫荡行动，71名涉案人员被扣留调查", "detail": "沙巴警方重拳出击联合盘查行动"},
        {"category": "national", "title": "沙巴40%净税收权益上诉案开审，联邦法院定判决日", "detail": "司法焦点法官合议庭"},
        {"category": "general", "title": "热带雨林生物多样性保育研讨会闭幕，犀鸟保护成重点", "detail": "生态保育"},
    ]
    res = generate_covers_for_headlines(test_headlines)
    print("生成结果:", [r["cover"] for r in res])
