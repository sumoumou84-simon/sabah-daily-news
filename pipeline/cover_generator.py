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

# 板块中文标签基础映射
CATEGORY_BADGE_MAP = {
    "sabah": "沙巴要闻",
    "national": "全国要闻",
    "sports": "体育焦点",
    "general": "大马综合",
}

def determine_cover_badge(category: str, title: str, detail: str = "") -> str:
    """
    动态读取该条新闻的实际分类或标题地名：
    - 沙巴本地新闻：根据具体地名显示（如“沙巴 · 山打根”、“沙巴 · 亚庇”、“沙巴 · 斗湖”、“沙巴 · 丹南”等），未指定城市显示“沙巴要闻”；
    - 全国新闻：如果是雪州显示“雪兰莪 · 全国”，森州显示“森美兰 · 全国”，其他显示“全国要闻”；
    - 体育新闻：显示“体育焦点”；
    - 综合新闻：手机/科技显示“科技数码”，水灾/民生显示“大马综合”，其他显示“大马综合”。
    """
    text = f"{title} {detail}".lower()

    if category == "sports":
        return "体育焦点"
    elif category == "national":
        if "雪州" in text or "雪兰莪" in text:
            return "雪兰莪 · 全国"
        elif "森州" in text or "森美兰" in text:
            return "森美兰 · 全国"
        elif "吉隆坡" in text:
            return "吉隆坡 · 全国"
        elif "槟城" in text:
            return "槟城 · 全国"
        elif "柔佛" in text:
            return "柔佛 · 全国"
        elif "砂拉越" in text:
            return "砂拉越 · 全国"
        return "全国要闻"
    elif category == "general":
        if any(k in text for k in ["小米", "手机", "数码", "科技", "5g", "芯片", "ai", "智能"]):
            return "科技数码"
        elif "雪州" in text or "雪兰莪" in text or "水灾" in text:
            return "大马综合"
        return "大马综合"
    elif category == "sabah":
        if any(k in text for k in ["山打根", "巴刹", "mps"]):
            return "沙巴 · 山打根"
        elif any(k in text for k in ["亚庇", "哥打京那巴鲁", "kk"]):
            return "沙巴 · 亚庇"
        elif "斗湖" in text:
            return "沙巴 · 斗湖"
        elif "丹南" in text or "rundum" in text:
            return "沙巴 · 丹南"
        elif "根地咬" in text:
            return "沙巴 · 根地咬"
        elif "仙本那" in text:
            return "沙巴 · 仙本那"
        elif "拿笃" in text:
            return "沙巴 · 拿笃"
        return "沙巴要闻"
    return "大马综合"

# 全局高优先级标题语义关键词映射规则 (命中时跨全库 assets/bg_pool/** 4 个子文件夹优先检索与抽取)
GLOBAL_KEYWORD_RULES = [
    # 0.0 智能手机与数码科技 (最高优先级：小米/手机/数码/智能设备/开卖/发布 -> Digital_shield / Golden_digital_shield)
    {
        "name": "智能手机数码科技",
        "keywords": ["小米", "手机", "数码", "开卖", "发布", "xiaomi", "apple", "5g", "芯片", "数码产品", "智能设备", "电子产品", "ai", "人工智能", "科技"],
        "patterns": ["digital_shield_and_circuit_nodes", "golden_digital_shield"],
        "priority": 5.0,
    },
    # 0.1 财政税收与政府经济预算 (最高优先级：财政/突破30亿/收入突破/税收/预算/超额/公账会/拨款/国库 -> Administrative_center_with_econo / Handshake)
    {
        "name": "财政税收经济预算",
        "keywords": ["财政", "突破30亿", "收入突破", "税收", "预算", "超出原定目标", "超额", "公账会", "拨款", "州收入", "国库", "储备金", "投资额", "经贸", "经济增长"],
        "patterns": ["administrative_center_with_econo", "governmental_pillars", "handshake_in_corporate_boardroom"],
        "priority": 5.0,
    },
    # 0.2a 未爆弹与现场排爆警戒 (现场排爆/防暴警戒/空投炸弹 -> officers_inspecting_bus_at_check)
    {
        "name": "未爆弹与现场排爆警戒",
        "keywords": ["未爆弹", "销毁", "千磅", "两枚", "炸弹", "排爆", "爆炸物", "警戒", "弹头", "空投炸弹"],
        "patterns": ["officers_inspecting_bus_at_check"],
        "priority": 5.0,
    },
    # 0.2b 警方斗殴缉捕治安 (斗殴/两派人马/抓捕 -> 现场刑侦调查)
    {
        "name": "警方斗殴缉捕治安",
        "keywords": ["两派人马", "斗殴", "警方", "逮捕", "防暴", "伤亡", "命案", "嫌犯", "扣留", "打架", "械斗", "追捕", "落网"],
        "patterns": ["investigators_outside_tropical", "investigators_at_tropical_villa"],
        "priority": 5.0,
    },
    # 0.3 道路交通基建与泛婆大道 (最高优先级：泛婆大道/泛婆/修路/公路工程/施工 -> Engineers_overlooking_highway)
    {
        "name": "道路基建工程",
        "keywords": ["泛婆大道", "泛婆", "调查泛婆", "公路", "大道", "工程", "修路", "大桥", "施工", "建设", "路线修复", "高架桥"],
        "patterns": ["engineers_overlooking_highway"],
        "priority": 5.0,
    },
    # 0.4 电缆电网与公用工程 (最高优先级：海底电缆/东盟电网/铺设/电网互联/电缆/变电站 -> Power_towers / Power_transmission / Utility_workers)
    {
        "name": "电缆电网公用工程",
        "keywords": ["海底电缆", "铺设", "电缆", "东盟电网", "互联", "电网", "变电站", "电供", "供水", "水槽车", "电力", "断电", "停水"],
        "patterns": ["power_towers_and_water_infrastru", "power_transmission_towers", "utility_workers"],
        "priority": 5.0,
    },
    # 0.5 足球赛事与国际比赛 (最高优先级：足球/马来虎/也门/国际赛/力挫/球赛 -> Soccer_player)
    {
        "name": "足球赛事运动",
        "keywords": ["足球", "马来虎", "也门", "国际赛", "以胜利结束", "2比1", "力挫", "进球", "球赛", "射门", "超级联赛", "联赛", "主场", "客场"],
        "patterns": ["soccer_player_executing_volley_kick", "soccer_player"],
        "priority": 5.0,
    },
    # 0.6 羽球大师赛与世界排名 (最高优先级：羽球/羽毛球/钦庆/跃升/世界排名/连夺两冠/赖沛君/许邦荣 -> Badminton_athlete / Jumping_smash)
    {
        "name": "羽球赛事运动",
        "keywords": ["羽球", "羽毛球", "钦庆", "世界排名", "跃升", "连夺两冠", "大师赛", "公开赛", "总决赛", "赖沛君", "许邦荣", "男双", "混双", "女双", "男单", "李梓嘉"],
        "patterns": ["badminton_athlete", "athlete_performing_jumping_smash"],
        "priority": 5.0,
    },
    # 0.7 历史路线与自然生态景观 (最高优先级：丹南/Rundum/历史路线/自然景观/雨林 -> Borneo_rainforest / Rainforest / Rhinoceros_hornbill)
    {
        "name": "历史路线自然生态",
        "keywords": ["丹南", "rundum", "历史路线", "修复", "景观", "自然景观", "历史与自然", "雨林", "热带雨林", "观鸟", "犀鸟", "生态", "神山"],
        "patterns": ["borneo_rainforest", "rainforest_at_twilight", "rhinoceros_hornbill"],
        "priority": 5.0,
    },
    # 0.8 水灾水患与灾民救援 (最高优先级：水灾/灾黎/灾民/水位/救援单位 -> Rainstorm / Rescue_boat)
    {
        "name": "水灾水患灾情",
        "keywords": ["水灾", "灾黎", "灾民", "水位", "淹水", "救援单位", "避难中心", "暴雨", "洪灾", "积水"],
        "patterns": ["tropical_rainstorm", "rainstorm", "rescue-boat", "image_20261109_210317"],
        "priority": 5.0,
    },
    # 0.9 外交伙伴与战略经贸 (高优先级：马法/战略伙伴/稀土/出口管制/放宽 -> Handshake / Governmental_pillars)
    {
        "name": "外交经贸伙伴",
        "keywords": ["马法", "战略伙伴", "稀土", "出口管制", "放宽", "外交", "双边", "建交", "备忘录", "mou", "签约"],
        "patterns": ["handshake_in_corporate_boardroom", "governmental_pillars"],
        "priority": 4.0,
    },
    # 0.10 内阁改组与政局首长 (高优先级：安华/政府稳固/改组内阁/大臣/辞职信/御准 -> Governmental_pillars / Administrative_center)
    {
        "name": "内阁政局要闻",
        "keywords": ["安华", "政府稳固", "改组内阁", "内阁", "大臣", "辞职信", "御准", "生效", "首长", "首相", "国会", "州务大臣"],
        "patterns": ["governmental_pillars", "golden_scales", "handshake_in_corporate_boardroom", "administrative_center"],
        "priority": 4.0,
    },
    # 0.2 选举投票与选情 (高优先级：州选/大选/补选/投票/选民/选委会/胜选/席位 -> Ballots_cast_in_ballot_box / Casting_ballot_in_civic_hall)
    {
        "name": "选举投票与选情",
        "keywords": ["州选", "大选", "补选", "投票", "选民", "选委会", "胜选", "席位"],
        "patterns": ["ballots_cast_in_ballot_box", "casting_ballot_in_civic_hall"],
        "priority": 3.0,
    },
    # 0.3 海上搜救与海事执法 (高优先级：失踪/寻人/搜救/海警/海上/海域/渔船/溺水 -> Maritime_patrol_boat / Patrol_boat_scanning)
    {
        "name": "海上搜救与海事执法",
        "keywords": ["失踪", "寻人", "搜救", "海警", "海上", "海域", "渔船", "溺水"],
        "patterns": ["maritime_patrol_boat", "patrol_boat_scanning"],
        "priority": 3.0,
    },
    # 0.4 民生福利与社区家庭 (高优先级：福利/主妇/妇女/援助金/津贴/民生/社区/家庭 -> Family_in_community_park)
    {
        "name": "民生福利与社区家庭",
        "keywords": ["福利", "主妇", "妇女", "援助金", "津贴", "民生", "社区", "家庭"],
        "patterns": ["family_in_community_park"],
        "priority": 3.0,
    },
    # 0.5 医疗卫生与医院 (高优先级：医院/医疗/医生/卫生部/病患/诊所/疫苗/骨痛热症 -> Medical_staff_reviewing_digital)
    {
        "name": "医疗卫生与医院",
        "keywords": ["医院", "医疗", "医生", "卫生部", "病患", "诊所", "疫苗", "骨痛热症"],
        "patterns": ["medical_staff_reviewing_digital"],
        "priority": 3.0,
    },
    # 0.6 学校教育与校园 (高优先级：学校/学生/教师/华校/独中/教育部/SPM/校舍 -> Students_raising_hands_in_classroom)
    {
        "name": "学校教育与校园",
        "keywords": ["学校", "学生", "教师", "华校", "独中", "教育部", "SPM", "spm", "校舍"],
        "patterns": ["students_raising_hands_in_classroom"],
        "priority": 3.0,
    },
    # 0.7 油棕种植与农业 (高优先级：油棕/棕油/种植/农业/农民/原产品/出口/园丘 -> Oil_palm_plantation / Sabah_oil_palm_plantation)
    {
        "name": "油棕种植与农业",
        "keywords": ["油棕", "棕油", "种植", "农业", "农民", "原产品", "出口", "园丘"],
        "patterns": ["oil_palm_plantation", "sabah_oil_palm_plantation"],
        "priority": 3.0,
    },
    # 0.8 机场航空与旅游 (高优先级：机场/航班/直飞/航线/航空/游客/旅游/入境 -> Airplane_taxiing)
    {
        "name": "机场航空与旅游",
        "keywords": ["机场", "航班", "直飞", "航线", "航空", "游客", "旅游", "入境"],
        "patterns": ["airplane_taxiing"],
        "priority": 3.0,
    },
    # 0.9 治安与刑事警务 (高优先级：警方/追捕/刺伤/打斗/命案/扣查/扫荡/取缔/嫌犯 -> Investigators)
    {
        "name": "治安与刑事警务",
        "keywords": ["警方", "追捕", "刺伤", "打斗", "命案", "扣查", "扫荡", "取缔", "嫌犯"],
        "patterns": ["investigators_at_tropical_villa", "investigators_outside_tropical"],
        "priority": 3.0,
    },
    # 0.10 陆路交通与事故 (高优先级：车祸/碰撞/路障/JPJ/陆路交通局/长巴/德士/交通 -> Officers_inspecting_bus / Taxis / 交通监控)
    {
        "name": "陆路交通与事故",
        "keywords": ["车祸", "碰撞", "路障", "jpj", "陆路交通局", "长巴", "德士", "交通"],
        "patterns": ["officers_inspecting_bus", "taxis_lined_up", "image_20261109_205524", "image_20261109_205602", "image_20261109_205757"],
        "priority": 3.0,
    },
    # 0.11 水电公用设施 (高优先级：断水/制水/水压/停电/电供/SESB/水务局/JANS -> Utility_workers_ / image_20261109_210654 / 210740)
    {
        "name": "水电公用设施",
        "keywords": ["断水", "制水", "水压", "停电", "电供", "sesb", "水务局", "jans"],
        "patterns": ["utility_workers_", "image_20261109_210654", "image_20261109_210740"],
        "priority": 3.0,
    },
    # 1. 暴雨 / 季候风 / 气象 / 淹水 / 水灾 -> 优先匹配 Rainstorm、Tropical_rainstorm、洪水救援图
    {
        "name": "暴雨气象水灾",
        "keywords": ["暴雨", "季候风", "风潮", "气象", "淹水", "水灾", "大雨", "洪灾", "积水", "救援艇", "救援船", "海浪"],
        "patterns": ["tropical_rainstorm", "rainstorm", "rescue_boat"]
    },
    # 2. 雨林 / 观鸟 / 犀鸟 / 生态 / 保育 / 神山 / 公园 -> 优先匹配 Rhinoceros_Hornbill、Rainforest、Borneo_rainforest
    {
        "name": "生态雨林野生动物",
        "keywords": ["雨林", "热带雨林", "观鸟", "犀鸟", "生态", "保育", "神山", "公园", "森林", "野生动物", "动植物"],
        "patterns": ["rhinoceros_hornbill", "borneo_rainforest", "rainforest"]
    },
    # 3. 竞选 / 政党 / 国会 / 内阁 / 部长 / 州政府 -> 优先匹配 Governmental_pillars、Administrative_center、Sabah_state_administrative
    {
        "name": "政经议会行政",
        "keywords": ["竞选", "助选", "政党", "国会", "内阁", "部长", "州政府", "首相", "首长", "议会", "议席", "解散国会", "提前解散", "执政", "希盟", "国盟", "国阵", "沙盟"],
        "patterns": ["governmental_pillars", "administrative_center", "sabah_state_administrative"]
    },
    # 4. 法庭 / 审讯 / 反贪 / 控状 / 司法 -> 优先匹配 Golden_scales
    {
        "name": "法庭司法反贪",
        "keywords": ["法庭", "审讯", "反贪", "控状", "司法", "法院", "审理", "判决", "上诉", "律师", "提控", "官司", "法官", "合议庭", "净税收"],
        "patterns": ["golden_scales_and_gavel", "golden_scales_of_justice", "golden_scales"]
    },
    # 5. 泛婆大道 / 修路 / 工程 -> 优先匹配 Engineers_overlooking_highway
    {
        "name": "基础设施修路工程",
        "keywords": ["泛婆大道", "泛婆", "修路", "工程", "大桥", "公路工程", "路段维修", "施工", "建设", "公路建设", "桥梁"],
        "patterns": ["engineers_overlooking_highway"]
    },
    # 6. 羽球 / 足球 / 田径 -> 保持原有精准体育匹配
    {
        "name": "羽球运动",
        "keywords": ["羽球", "羽毛球", "李梓嘉", "跳杀", "汤杯", "公开赛", "大师赛", "男单", "女单", "双打"],
        "patterns": ["badminton_athlete", "athlete_performing_jumping_smash"]
    },
    {
        "name": "足球运动",
        "keywords": ["足球", "sabah fc", "联赛", "进球", "球赛", "射门", "主场表现", "客场", "积分榜", "锦标赛", "超级联赛"],
        "patterns": ["soccer_player_executing_volley_kick", "soccer_player"]
    },
    {
        "name": "田径短跑",
        "keywords": ["田径", "短跑", "起跑", "飞人", "金牌", "健儿", "跨栏", "百米", "接力"],
        "patterns": ["sprinters_bursting"]
    },
    # 7. 水警 / 海警 / 海事 / 巡逻 / 快艇
    {
        "name": "水警海事巡逻",
        "keywords": ["水警", "海警", "海事", "巡逻", "快艇", "走私", "偷渡", "截查", "扣留船", "巡逻艇", "非法入境"],
        "patterns": ["maritime_patrol_boat", "patrol_boat"]
    },
    # 8. 扫荡 / 突击 / 扣留 / 逮捕 / 盘查
    {
        "name": "执法盘查扫荡",
        "keywords": ["扫荡", "突击", "扣留", "逮捕", "盘查", "搜查", "抓捕", "警区", "嫌犯", "落网", "联合行动"],
        "patterns": ["officers_inspecting_bus", "investigators"]
    },
    # 9. 夜市 / 巴刹 / pasar / 市集 / 摊贩
    {
        "name": "夜市巴刹市集",
        "keywords": ["夜市", "巴刹", "pasar", "市集", "摊贩", "农贸市场", "小贩", "商户", "开市"],
        "patterns": ["lanterns_glowing_at_night_market", "night_market_street"]
    },
    # 10. 德士 / 巴士 / 客运 / 车站 / 交通枢纽
    {
        "name": "公共交通枢纽",
        "keywords": ["德士", "巴士", "客运", "车站", "交通枢纽", "司机", "公共交通", "客货车"],
        "patterns": ["taxis_lined_up", "drivers_conversing"]
    },
    # 11. 铁道 / 高铁 / 列车 / 火车
    {
        "name": "铁道列车交通",
        "keywords": ["铁道", "高铁", "列车", "火车", "民航"],
        "patterns": ["train_and_airplane"]
    },
    # 12. 诈骗 / 黑客 / 网络 / 数字 / 科技 / 防骗
    {
        "name": "网络科技安全",
        "keywords": ["诈骗", "黑客", "网络安全", "数字", "科技", "防骗", "电诈", "人工智能", "信息安全", "科技教育"],
        "patterns": ["digital_shield", "golden_digital_shield"]
    },
    # 13. 电网 / 供电 / 断电 / 停水 / 变电站 / 维修 / 电力 / SESB
    {
        "name": "公用事业抢修",
        "keywords": ["电网", "供电", "断电", "停水", "供水", "变电站", "电缆", "水务", "电力", "sesb", "抢修", "检修", "电塔"],
        "patterns": ["power_towers", "power_transmission", "utility_workers"]
    },
    # 14. 海洋 / 潜水 / 珊瑚 / 海龟 / 仙本那 / 海岛
    {
        "name": "海洋海岛潜水",
        "keywords": ["海洋", "潜水", "珊瑚", "海龟", "仙本那", "海岛", "浮潜", "海洋公园"],
        "patterns": ["underwater_coral_reef", "split_ocean_coral_reef"]
    },
]

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
        """扫描并按板块归类所有可用底图，同时维护全库列表"""
        self.pool_map: Dict[str, List[Path]] = {
            "sabah": [],
            "national": [],
            "sports": [],
            "general": []
        }
        self.all_images: List[Path] = []
        if not self.bg_pool_dir.exists():
            return

        for cat in self.pool_map.keys():
            cat_dir = self.bg_pool_dir / cat
            if cat_dir.exists():
                imgs = [p for p in cat_dir.glob("*.jpg") if p.is_file()]
                sorted_imgs = sorted(imgs, key=lambda x: x.name)
                self.pool_map[cat] = sorted_imgs
                self.all_images.extend(sorted_imgs)

    def select_background(self, category: str, title: str, detail: str = "") -> Path:
        """
        全局标题语义关键词优先匹配（跨全部 4 个子文件夹检索）：
        1. 优先扫描全局高优先级关键词映射规则：
           若标题（或详情）命中特定高优先级关键词，在全库 (assets/bg_pool/**) 未使用的底图中挑选最契合的底图；
        2. 若未命中全局高优先级关键词，才回退到当前板块子目录 (assets/bg_pool/<category>/) 中抽取未用底图；
        3. 维护已用集合，确保同一日内 12~15 条新闻绝不重复使用同一张底图；
        4. 终极兜底确保绝不空缺报错。
        """
        search_title = title.lower()
        search_detail = detail.lower()

        # 根据分类构建可用底图候选池（严禁体育与非体育混用，全国新闻禁选沙巴特有建筑/动植物）
        if category == "sports":
            available_pool = [img for img in self.pool_map.get("sports", []) if img.name not in self.used_images_today]
            if not available_pool:
                available_pool = self.pool_map.get("sports", [])
        else:
            # 非体育新闻：彻底排除 sports 目录
            available_pool = [img for img in self.all_images if img.parent.name != "sports" and img.name not in self.used_images_today]
            if category == "national":
                # 全国新闻：排除包含 sabah_ 或 borneo_ 的沙巴本土专有底图
                available_pool = [img for img in available_pool if not (img.name.lower().startswith("sabah_") or img.name.lower().startswith("borneo_"))]

        # ------------------------------------------------------------------
        # 步骤 1: 全局高优先级标题语义关键词匹配
        # ------------------------------------------------------------------
        best_candidate: Optional[Path] = None
        best_rule_score = 0

        for rule in GLOBAL_KEYWORD_RULES:
            # 计算命中数：标题命中权重为 10，详情为 1
            title_hits = sum(1 for kw in rule["keywords"] if kw.lower() in search_title)
            detail_hits = sum(1 for kw in rule["keywords"] if kw.lower() in search_detail)

            if title_hits == 0 and detail_hits == 0:
                continue

            # 只有标题实际命中高优先级关键词时，才享受高优先级权重加成；
            # 若仅详情偶发提及而标题未命中，降为常态权重 1.0，避免正文旁支细节抢占稀缺底图
            priority = rule.get("priority", 1.0) if title_hits > 0 else 1.0
            rule_weight = ((title_hits * 10) + detail_hits) * priority
            patterns = rule["patterns"]

            for img in available_pool:
                fname_lower = img.name.lower()
                for pat in patterns:
                    pat_lower = pat.lower()
                    if pat_lower in fname_lower:
                        score = rule_weight * 10
                        if fname_lower.startswith(pat_lower):
                            score += 5
                        # 如果底图所属目录与当前分类一致，给予加分，优先同板块底图
                        if img.parent.name == category:
                            score += 15
                        if score > best_rule_score:
                            best_rule_score = score
                            best_candidate = img

        if best_candidate is not None:
            self.used_images_today.add(best_candidate.name)
            return best_candidate

        # ------------------------------------------------------------------
        # 步骤 2: 回退规则 - 未命中高优先级关键词，回退到对应板块文件夹抽取未用底图
        # ------------------------------------------------------------------
        cat = category if category in self.pool_map else "general"
        cat_unused = [img for img in available_pool if img.parent.name == cat]

        if not cat_unused:
            # 当前板块已用尽，从候选池其他合规底图中找
            cat_unused = available_pool

        if not cat_unused:
            # 极端兜底：全部用尽，从板块全量中允许复用
            cat_unused = self.pool_map.get(cat, []) or self.all_images

        if not cat_unused:
            raise FileNotFoundError(f"底图库 assets/bg_pool/ 中没有可用图片！请先运行 scripts/import_bg_pool.py。")

        fallback_img = cat_unused[0]
        self.used_images_today.add(fallback_img.name)
        return fallback_img

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

        # 4. 左上角金黄色圆角胶囊徽章（根据实际分类与地名动态计算，解决硬编码）
        badge_text = determine_cover_badge(category, title, detail)
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
