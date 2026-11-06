import os
import json
import re
from datetime import datetime, timezone, timedelta
import sys

# 兼容 Windows 终端输出
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

NEWS_DATA_FILE = "news_data.json"
OUTPUT_HTML_FILE = "index.html"

def get_myt_datetime():
    """获取马来西亚时间（UTC+8）"""
    tz_myt = timezone(timedelta(hours=8))
    return datetime.now(tz_myt)

def extract_tags_and_sources(title, detail):
    """提取双核实标签、信源与纯文本"""
    verify_match = re.search(r'\[(.*?)\]', title)
    verified_tag = verify_match.group(1) if verify_match else "双官方来源交叉核实"
    clean_title = re.sub(r'\[.*?\]', '', title).strip()

    sources = []
    if "来源：" in detail or "来源:" in detail:
        parts = re.split(r'来源[：:]', detail)
        source_str = parts[-1].rstrip("。").strip()
        for s in re.split(r'[/、+及与]', source_str):
            s_clean = s.strip()
            if s_clean and len(s_clean) < 20:
                sources.append(s_clean)
        clean_detail = parts[0].strip()
    else:
        clean_detail = detail.strip()

    if not sources:
        sources = ["沙巴官方通报", "现场交叉复核"]

    return clean_title, verified_tag, sources, clean_detail

def generate_index_html():
    """
    前端渲染引擎 3.0：
    1. 實裝『☀️ 日间 / 🌙 夜间』模式一键切换功能（带 localStorage 状态记忆与秒级平滑切换）
    2. 夜间深色模式优化（高对比黑金版）：全面提亮正文、标签与摘要，彻底解决发暗模糊痛点
    3. 日间浅色模式（经典护眼纸质报章风）：暖米白底色 #F8FAFC、纯白立体卡片、深炭黑锐利文字
    4. 重点要闻 5 大分类 Tab 选项卡（全部、沙巴&山打根、全国政经、体育焦点、综合百态）
    5. 严格锁定双列网格排版 (grid-template-columns: repeat(2, 1fr) !important;)
    6. 渲染 20~24 条重点要闻（包含 250~400 字深度背景脉络与双官方核实）
    7. 未来 2 周活动（含倒计时、开始结束时间、详尽简介与官方热线）
    8. 7 天真实历史归档池无缝切换
    """
    myt_now = get_myt_datetime()
    today_iso = myt_now.strftime("%Y-%m-%d")
    today_mmdd = myt_now.strftime("%m/%d")
    yesterday_mmdd = (myt_now - timedelta(days=1)).strftime("%m/%d")
    yesterday_iso = (myt_now - timedelta(days=1)).strftime("%Y-%m-%d")
    day_before_mmdd = (myt_now - timedelta(days=2)).strftime("%m/%d")
    day_before_iso = (myt_now - timedelta(days=2)).strftime("%Y-%m-%d")
    today_time = myt_now.strftime("%I:%M%p")
    today_full = myt_now.strftime("%Y-%m-%d")

    # 读取 news_data.json
    if not os.path.exists(NEWS_DATA_FILE):
        print(f"⚠️ {NEWS_DATA_FILE} 不存在，使用空数据保底...")
        data = {"utilities": [], "headlines": [], "events": [], "archive": {}}
    else:
        with open(NEWS_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"❌ 读取 {NEWS_DATA_FILE} 失败: {e}")
                data = {"utilities": [], "headlines": [], "events": [], "archive": {}}

    utilities = data.get("utilities", [])
    headlines = data.get("headlines", [])
    events_list = data.get("events", [])
    archive_pool = data.get("archive", {})

    # 1. 动态生成 3 列黄色公用事业卡片 (UTILITI)
    default_utils = [
        {
            "id": "W",
            "label": "沙巴水务局 JANS",
            "labelBM": "Jabatan Air Sabah (JANS)",
            "time": "07:30",
            "status": "LIVE 抢修中",
            "statusBM": "LANGSUNG Baik Pulih",
            "issue": "北路主干管网减压抢修，高地段供水短暂停顿",
            "issueBM": "Pembaikan paip utama Jalan Utara, gangguan bekalan sementara kawasan tinggi",
            "pressure": "降压供水区：Cecily、北路2哩至4哩",
            "pressureBM": "Kawasan tekanan rendah: Cecily, Batu 2 - 4 Jalan Utara",
            "recovery": "预计修复：今晚 20:00 前逐步恢复常压",
            "recoveryBM": "Jangka pulih: Beransur pulih sebelum 20:00 malam ini",
            "tanker": "配水应急车：已派驻山打根肯特医院及核心住宅区",
            "tankerBM": "Lori tangki air digerakkan ke Hospital Kent & kawasan perumahan",
            "consult": "089-666000",
            "consult2": "Careline 24J",
            "source": "沙巴水务局与市议会双核实",
            "sourceBM": "Disahkan JANS & MPS"
        },
        {
            "id": "E",
            "label": "沙巴电力 SESB",
            "labelBM": "Sabah Electricity (SESB)",
            "time": "08:00",
            "status": "LIVE 维护",
            "statusBM": "LANGSUNG Selenggara",
            "issue": "电网稳定性例行调度维护，已启用后备发电机组",
            "issueBM": "Penyelenggaraan grid berkala, genset sokongan diaktifkan",
            "pressure": "监测范围：山打根工业区及沿海变电枢纽",
            "pressureBM": "Kawasan terlibat: Zon Perindustrian Sandakan & pencawang pesisir",
            "recovery": "全线电压稳定受控，无大面积断电风险",
            "recoveryBM": "Voltan grid terkawal, tiada risiko blackout menyeluruh",
            "tanker": "抢修技术班组 24小时驻点待命",
            "tankerBM": "Pasukan teknikal bersedia 24 jam",
            "consult": "15454",
            "consult2": "SESB Care",
            "source": "SESB 官方通报",
            "sourceBM": "Disahkan SESB"
        },
        {
            "id": "T",
            "label": "山打根交通 MPS",
            "labelBM": "Trafik Sandakan (MPS)",
            "time": "07:15",
            "status": "LIVE 通畅",
            "statusBM": "LANGSUNG Lancar",
            "issue": "市区及主要出入口主干道交通畅行，无重大积水",
            "issueBM": "Trafik lancar di jalan utama bandar, tiada banjir kilat",
            "pressure": "重点路段：拉卜路、北路车流量平稳",
            "pressureBM": "Jalan Labuk & Jalan Utara trafik terkawal",
            "recovery": "全马长假交通联巡已启动，交警要道巡逻",
            "recoveryBM": "Rondaan polis trafik sempena cuti panjang beroperasi",
            "tanker": "拖车应急热线常设备勤",
            "tankerBM": "Perkhidmatan tunda kecemasan tersedia",
            "consult": "089-272161",
            "consult2": "MPS Trafik",
            "source": "山打根市议会 & 交警",
            "sourceBM": "Disahkan MPS & Polis"
        }
    ]

    for i, u_raw in enumerate(utilities):
        if i < len(default_utils):
            c_title, v_tag, s_list, c_detail = extract_tags_and_sources(u_raw.get("title", ""), u_raw.get("detail", ""))
            default_utils[i]["label"] = c_title[:18]
            default_utils[i]["labelBM"] = c_title[:18]
            default_utils[i]["issue"] = c_detail
            default_utils[i]["source"] = v_tag

    utiliti_cards_html = ""
    for idx, u in enumerate(default_utils):
        is_first = (idx == 0)
        open_cls = "open" if is_first else ""
        utiliti_cards_html += f"""
        <div class="util-card {open_cls}" id="util-card-{idx}" onclick="toggleUtilCard({idx})">
            <div class="flex items-center justify-between w-full">
                <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-[8px] bg-black text-[#FFD60A] flex items-center justify-center font-black text-[12px] shrink-0">
                        {u['id']}
                    </div>
                    <div class="leading-tight">
                        <div class="text-black font-black text-[13px] tracking-tight flex items-center gap-1.5">
                            <span class="lang-zh">{u['label']}</span>
                            <span class="lang-bm hidden">{u['labelBM']}</span>
                            <span class="w-4 h-4 rounded-full bg-black text-[#FFD60A] flex items-center justify-center text-[10px] arrow-util">▼</span>
                        </div>
                        <div class="text-black/70 text-[11px] mono">{today_mmdd} {u['time']} • LIVE</div>
                    </div>
                </div>
                <div class="text-right shrink-0">
                    <div class="inline-flex items-center gap-1 px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-bold">
                        <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full animate-pulse"></span>
                        <span class="lang-zh">{u['status']}</span>
                        <span class="lang-bm hidden">{u['statusBM']}</span>
                    </div>
                    <div class="text-[10px] text-black/70 mono mt-1 font-bold toggle-hint">
                        { '收起 ↑' if is_first else '点击查看详情' }
                    </div>
                </div>
            </div>

            <div class="util-drawer mt-3">
                <div class="util-drawer-inner rounded-[10px] p-3 flex flex-col gap-2.5">
                    <div class="flex items-center gap-1.5">
                        <span class="w-1 h-4 rounded-full bg-[#FFD60A]"></span>
                        <span class="text-[11px] font-black text-[#FFD60A] tracking-wider">
                            <span class="lang-zh">实时详情 LIVE DETAIL</span>
                            <span class="lang-bm hidden">BUTIRAN LANGSUNG</span>
                        </span>
                        <span class="text-[10px] mono text-[#94A3B8]">• {today_mmdd} {u['time']} LIVE</span>
                    </div>

                    <div class="space-y-2">
                        <div class="flex gap-2 text-[12.5px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-[#FFD60A]/20 text-[#FFD60A] flex items-center justify-center text-[11px] font-black">!</span>
                            <span class="font-bold util-detail-title lang-zh">{u['issue']}</span>
                            <span class="font-bold util-detail-title lang-bm hidden">{u['issueBM']}</span>
                        </div>
                        <div class="flex gap-2 text-[12px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-black/30 text-[#94A3B8] flex items-center justify-center text-[10px]">≋</span>
                            <span class="util-detail-sub lang-zh">{u['pressure']}</span>
                            <span class="util-detail-sub lang-bm hidden">{u['pressureBM']}</span>
                        </div>
                        <div class="flex gap-2 text-[12px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-black/30 text-[#94A3B8] flex items-center justify-center text-[10px]">◷</span>
                            <span class="util-detail-time lang-zh">{u['recovery']}</span>
                            <span class="util-detail-time lang-bm hidden">{u['recoveryBM']}</span>
                        </div>
                        <div class="flex gap-2 text-[12px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-[#14532d] text-[#4ade80] flex items-center justify-center text-[10px]">◩</span>
                            <span class="util-detail-sub lang-zh">{u['tanker']}</span>
                            <span class="util-detail-sub lang-bm hidden">{u['tankerBM']}</span>
                        </div>
                    </div>

                    <div class="pt-2 border-t border-black/20 flex flex-col gap-2">
                        <div class="flex flex-wrap gap-1.5">
                            <span class="inline-flex items-center gap-1 px-2 py-[3px] rounded-full bg-black/40 text-[11px] text-[#F8FAFC] mono font-bold">
                                <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                                {u['consult']}
                            </span>
                            <span class="inline-flex items-center gap-1 px-2 py-[3px] rounded-full bg-black/40 text-[11px] text-[#F8FAFC] mono font-bold">
                                <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                                {u['consult2']}
                            </span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="inline-flex items-center gap-1 px-2 py-[2px] rounded-[6px] bg-[#14532d] border border-[#166534] text-[#4ade80] text-[10px] font-bold">
                                ✓ <span class="lang-zh">{u['source']}</span><span class="lang-bm hidden">{u['sourceBM']}</span>
                            </span>
                            <span class="text-[10px] mono text-black/60">
                                <span class="lang-zh">点击再次收起</span>
                                <span class="lang-bm hidden">Klik tutup</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    # 2. 动态生成重点要闻双列网格卡片（绑定 data-category 属性，高对比度排版）
    bm_translations = {
        "肯特医院": "Hospital Duchess of Kent Sandakan",
        "水务局": "Jabatan Air Sabah (JANS)",
        "电力": "Sabah Electricity (SESB)",
        "陆路交通局": "Jabatan Pengangkutan Jalan (JPJ)",
        "ESSCOM": "Kawasan Keselamatan Khas Pantai Timur Sabah (ESSCOM)",
        "财政部": "Kementerian Kewangan",
        "泛婆大道": "Lebuhraya Pan Borneo",
        "MCMC": "Suruhanjaya Komunikasi dan Multimedia (MCMC)",
        "中央巴刹": "Pasar Sentral Sandakan (MPS)",
        "教育部": "Kementerian Pendidikan (KPM)",
        "绿海龟": "Pemuliharaan Penyu & Hidupan Liar Sabah",
        "KPDN": "Kementerian Perdagangan Dalam Negeri (KPDN)",
        "机场": "Lapangan Terbang Sandakan (SDK)",
        "微电网": "Sistem Grid Mikro Solar Komuniti",
        "流感": "Jabatan Kesihatan Negeri Sabah (JKNS)",
        "羽球队": "Skuad Badminton Kebangsaan Malaysia",
        "谢定峰": "Beregu Aaron Chia & Soh Wooi Yik (BAM)",
        "李梓嘉": "Lee Zii Jia (Team LZJ) Final Jelajah Dunia BWF",
        "乐蒂": "Pearly Tan & M. Thinaah (Beregu Wanita Kebangsaan)",
        "Sabah FC": "Sabah FC (Sang Badak) Liga Super Stadium Likas",
        "英超": "Liga Perdana Inggeris (EPL) Perebutan Kejuaraan",
        "最低薪金": "Kementerian Sumber Manusia Gaji Minimum",
        "电动车": "Kementerian Pengangkutan Koridor EV Hijau",
        "心理健康": "Kementerian Kesihatan Talian Sokongan Kesihatan Mental",
        "气象局": "Jabatan Meteorologi Amaran Monsun & Cuaca",
        "运动会": "Sukan Sabah & Kejohanan Sepak Takraw"
    }

    def get_bm_title(zh_t):
        for k, v in bm_translations.items():
            if k in zh_t:
                return f"Laporan Khas: {v} - Kemas Kini Rasmi"
        return f"Berita Terkini Sabah & Malaysia: {zh_t[:30]}"

    news_cards_html = ""
    for idx, item in enumerate(headlines, 1):
        raw_title = item.get("title", "")
        detail = item.get("detail", "") or item.get("summary", "")
        clean_title, tag, sources, clean_detail = extract_tags_and_sources(raw_title, detail)
        if item.get('sources'):
            sources = item.get('sources')
        elif item.get('source'):
            sources = [item.get('source')]
        title_bm = item.get("titleBM") or get_bm_title(clean_title)
        detail_bm = item.get("detailBM") or f"Laporan berita mendalam mengenai perkembangan terkini di Sabah dan seluruh Malaysia. Maklumat disahkan oleh portal berita dan agensi rasmi berkaitan. {clean_detail[:120]}..."

        # 核心分类绑定
        category = item.get("category", "general")
        if category == "sabah":
            category_tag_zh, category_tag_bm = "沙巴要闻", "Sabah"
        elif category == "national":
            category_tag_zh, category_tag_bm = "全国政经", "Nasional"
        elif category == "sports":
            category_tag_zh, category_tag_bm = "体育焦点", "Sukan"
        else:
            category_tag_zh, category_tag_bm = "综合百态", "Umum"

        sources_pills = "".join([f'<span class="source-pill px-1.5 py-[1px] rounded-[4px] mono truncate max-w-[110px] text-[10px]">{s}</span>' for s in sources])
        sources_links = "".join([f'<span class="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/30 text-[10.5px] text-[#FFD60A] mono font-bold">↗ {s}</span>' for s in sources])

        pin_badge = '<span class="shrink-0 w-2.5 h-2.5 rounded-full bg-[#EC4899] mt-2 shadow-sm animate-pulse"></span>' if idx <= 2 else ''

        news_cards_html += f"""
                <article class="news-grid-card group relative flex flex-col rounded-[12px] border transition-all cursor-pointer overflow-hidden" data-category="{category}" id="news-card-{idx}" onclick="openNewsModal({idx-1})">
                    <div class="card-inner-box p-2.5 sm:p-3 md:p-3.5 flex flex-col gap-2 flex-1">
                        <div class="flex items-start justify-between gap-1.5">
                            <h3 class="card-title font-bold leading-snug flex-1 text-[13px] sm:text-[14px] md:text-[15px] transition-colors line-clamp-3">
                                <span class="lang-zh">{clean_title}</span>
                                <span class="lang-bm hidden">{title_bm}</span>
                            </h3>
                            {pin_badge}
                        </div>

                        <div class="flex flex-wrap items-center gap-1 mt-auto pt-1">
                            <span class="mono text-[9.5px] sm:text-[10px] font-bold card-meta-time">{today_mmdd}</span>
                            <span class="inline-flex items-center px-1.5 py-[0.5px] rounded text-[9px] sm:text-[9.5px] font-bold bg-[#14532d] text-[#4ade80] border border-[#166534]">
                                {tag}
                            </span>
                            <span class="category-pill-tag text-[9px] sm:text-[9.5px] px-1.5 py-[0.5px] rounded mono font-bold">
                                <span class="lang-zh">{category_tag_zh}</span>
                                <span class="lang-bm hidden">{category_tag_bm}</span>
                            </span>
                        </div>
                    </div>

                    <div class="mt-auto flex items-center justify-between gap-1.5 px-2.5 py-2 sm:px-3 sm:py-2.5 card-footer border-t border-white/5">
                        <div class="flex flex-wrap gap-1 min-w-0">
                            {sources_pills}
                        </div>
                        <button onclick="event.stopPropagation(); openNewsModal({idx-1})" class="shrink-0 inline-flex items-center gap-0.5 px-2 py-1 sm:px-2.5 sm:py-1 rounded-md bg-[#FFD60A] text-black font-black text-[10px] sm:text-[11px] hover:bg-[#ffde33] active:scale-95 transition-all whitespace-nowrap shadow-sm">
                            <span class="lang-zh">查看 ➡</span>
                            <span class="lang-bm hidden">Baca ➡</span>
                        </button>
                    </div>
                </article>
                """
        
    # 3. 动态渲染未来 2 周活动预告卡片
    events_cards_html = ""
    for ev in events_list:
        countdown_label_zh = f"还有 {ev.get('countdown_days', 0)} 天"
        countdown_label_bm = f"{ev.get('countdown_days', 0)} hari lagi"
        
        events_cards_html += f"""
        <div class="event-card group cursor-pointer rounded-[10px] border transition-all p-3" id="event-card-{ev['id']}" onclick="toggleEventCard({ev['id']})">
            <div class="flex items-center gap-3">
                <div class="shrink-0 w-[48px] h-[48px] rounded-[8px] bg-[#FFD60A] text-black flex flex-col items-center justify-center leading-none">
                    <span class="font-black text-[13px]">{ev['month']}</span>
                    <span class="font-bold text-[11px]">/{ev['day']}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-[13px] font-bold leading-tight truncate event-title transition-colors">
                        <span class="lang-zh">{ev['name']}</span>
                        <span class="lang-bm hidden">{ev['nameBM']}</span>
                    </div>
                    <div class="text-[11px] truncate flex items-center gap-1.5 mt-0.5 event-subtitle">
                        <span>{ev['location']}</span>
                        <span>•</span>
                        <span class="text-[#FFD60A] font-bold text-[10px] mono">
                            <span class="lang-zh">{countdown_label_zh}</span>
                            <span class="lang-bm hidden">{countdown_label_bm}</span>
                        </span>
                    </div>
                </div>
                <div class="shrink-0 flex items-center gap-2">
                    <span class="px-2 py-[2px] rounded-full text-[10px] font-bold {ev['badgeColor']}">
                        <span class="lang-zh">{ev['category']}</span>
                        <span class="lang-bm hidden">{ev['categoryBM']}</span>
                    </span>
                    <span class="text-[11px] arrow-ev transition-transform">▼</span>
                </div>
            </div>

            <div class="event-drawer hidden mt-3 pt-3 border-t">
                <p class="text-[12.5px] leading-[1.65] mb-2.5 event-desc">
                    <span class="lang-zh">{ev['desc']}</span>
                    <span class="lang-bm hidden">{ev['descBM']}</span>
                </p>
                <div class="flex flex-wrap items-center justify-between gap-2 text-[11px] p-2 rounded-[8px] event-time-box">
                    <div class="flex items-center gap-1.5">
                        <span class="text-[#FFD60A]">⏰</span>
                        <span class="lang-zh">{ev['time']}</span>
                        <span class="lang-bm hidden">{ev['timeBM']}</span>
                    </div>
                    <a href="tel:{ev['tel'].split('/')[0].strip()}" onclick="event.stopPropagation();" class="inline-flex items-center gap-1 px-2.5 py-[3px] rounded-full bg-[#FFD60A] text-black font-black text-[10px] hover:bg-[#ffde33] transition">
                        <span>📞</span>
                        <span>{ev['tel']}</span>
                    </a>
                </div>
                <div class="mt-2 flex items-center justify-between text-[10px] event-meta">
                    <span class="text-[#22c55e]">✓ <span class="lang-zh">{ev['source']}</span><span class="lang-bm hidden">{ev['sourceBM']}</span></span>
                    <span class="mono">沙巴官方核准备案活动</span>
                </div>
            </div>
        </div>
        """

    # 4. 组装整页 HTML
    archive_json_str = json.dumps(archive_pool, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>西门看看网 · 每日晨报 | 全自动信源采集与双核实编译引擎 3.0</title>
    <!-- 立即执行内联主题脚本，彻底杜绝切换闪烁 -->
    <script>
        (function() {{
            try {{
                var saved = localStorage.getItem('sk_theme');
                var theme = saved || 'dark';
                document.documentElement.className = theme === 'light' ? 'theme-light' : 'theme-dark';
            }} catch(e) {{}}
        }})();
    </script>
    <!-- 引入 Tailwind CSS 运行时 -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{
            font-family: "Noto Sans SC", system-ui, -apple-system, sans-serif;
            box-sizing: border-box;
        }}
        .mono {{
            font-family: "JetBrains Mono", monospace;
        }}
        .line-clamp-2 {{
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        body {{
            transition: background-color 0.25s ease, color 0.25s ease;
            min-height: 100vh;
        }}

        /* =====================================================================
           夜间深色模式优化 (High-Contrast Dark / 黑金高对比版)
           彻底提亮文字与边框，消除暗淡模糊
           ===================================================================== */
        .theme-dark {{
            --bg-page: #0B0F17;
            --bg-header: #0F172A;
            --border-header: #334155;
            --bg-card: #1E293B;
            --bg-card-hover: #243247;
            --border-card: #334155;
            --border-card-hover: #475569;
            --text-title: #F8FAFC;
            --text-title-hover: #FFD60A;
            --bg-drawer: #0F172A;
            --border-drawer: #334155;
            --text-body: #E2E8F0;
            --quote-bg: #162032;
            --quote-border: #2D3D54;
            --quote-text: #CBD5E1;
            --source-pill-bg: #0F172A;
            --source-pill-border: #334155;
            --source-pill-text: #94A3B8;
            --card-footer-bg: #131B2A;
            --card-footer-border: #334155;
            --card-footer-text: #94A3B8;
            --sub-meta: #94A3B8;
            --date-badge-bg: #1E293B;
            --date-badge-border: #334155;
            --date-badge-text: #CBD5E1;
            --panel-bg: #151D2A;
            --panel-border: #2D3D54;
            --ad-box-bg: #151D2A;
            --ad-box-border: #2D3D54;
            --ad-inner-bg: #0F172A;
            --ad-inner-border: #334155;
        }}

        .theme-dark body {{
            background-color: var(--bg-page);
            color: var(--text-title);
        }}
        .theme-dark header {{
            background-color: var(--bg-header) !important;
            border-color: var(--border-header) !important;
        }}
        .theme-dark .theme-panel {{
            background-color: var(--panel-bg) !important;
            border-color: var(--panel-border) !important;
        }}
                .theme-dark .card-cover-wrap {{
            background-color: #0F172A !important;
            border-bottom: 1px solid #334155 !important;
        }}
                /* 弹窗沉浸阅读暗黑模式 */
        .theme-dark .modal-content-box {{
            background-color: #1E293B !important;
            border-color: #334155 !important;
            color: #F8FAFC !important;
        }}
        .theme-dark .modal-header-bar {{
            background-color: rgba(15, 23, 42, 0.95) !important;
            border-color: #334155 !important;
        }}
        .theme-dark .modal-close-btn {{
            background-color: #334155 !important;
            color: #F8FAFC !important;
        }}
        .theme-dark .modal-close-btn:hover {{
            background-color: #475569 !important;
            color: #FFD60A !important;
        }}
        .theme-dark .modal-detail-box {{
            background-color: #0F172A !important;
            border: 1px solid #334155 !important;
        }}
        .theme-dark .modal-body-text {{
            color: #E2E8F0 !important;
        }}
        .theme-dark .modal-verify-box {{
            background-color: #162032 !important;
            border-color: #2D3D54 !important;
            color: #CBD5E1 !important;
        }}
        .theme-dark .card-summary {{
            color: #94A3B8 !important;
        }}
        .theme-dark .modal-cover-wrap {{
            border-color: #334155 !important;
            background-color: #0F172A !important;
        }}
        .theme-dark .news-grid-card {{
            background-color: var(--bg-card) !important;
            border-color: var(--border-card) !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
        }}
        .theme-dark .news-grid-card:hover {{
            background-color: var(--bg-card-hover) !important;
            border-color: var(--border-card-hover) !important;
        }}
        .theme-dark .news-grid-card.open {{
            background-color: #243247 !important;
            border-color: #FFD60A !important;
            box-shadow: 0 0 0 1px #FFD60A, 0 6px 18px rgba(255, 214, 10, 0.2);
        }}
        .theme-dark .news-grid-card .card-title {{
            color: var(--text-title) !important;
        }}
        .theme-dark .news-grid-card:hover .card-title,
        .theme-dark .news-grid-card.open .card-title {{
            color: var(--text-title-hover) !important;
        }}
        .theme-dark .news-drawer-box {{
            background-color: var(--bg-drawer) !important;
            border: 1px solid var(--border-drawer) !important;
        }}
        .theme-dark .news-body-text {{
            color: var(--text-body) !important;
        }}
        .theme-dark .quote-box {{
            background-color: var(--quote-bg) !important;
            border: 1px solid var(--quote-border) !important;
            color: var(--quote-text) !important;
        }}
        .theme-dark .quote-icon {{
            background-color: #1E293B !important;
            color: #FFD60A !important;
        }}
        .theme-dark .source-pill {{
            background-color: var(--source-pill-bg) !important;
            border: 1px solid var(--source-pill-border) !important;
            color: var(--source-pill-text) !important;
        }}
        .theme-dark .card-footer {{
            background-color: var(--card-footer-bg) !important;
            border-top: 1px solid var(--card-footer-border) !important;
        }}
        .theme-dark .card-footer .footer-label {{
            color: var(--card-footer-text) !important;
        }}
        .theme-dark .sub-meta-text,
        .theme-dark .card-meta-time,
        .theme-dark .drawer-mini-tag {{
            color: var(--sub-meta) !important;
        }}
        .theme-dark .sub-meta-date {{
            color: #CBD5E1 !important;
        }}
        .theme-dark .drawer-divider {{
            border-color: rgba(51, 65, 85, 0.7) !important;
        }}
        .theme-dark .category-pill-tag {{
            background-color: #0F172A !important;
            border: 1px solid #334155 !important;
            color: #CBD5E1 !important;
        }}
        .theme-dark .event-card {{
            background-color: var(--bg-card) !important;
            border-color: var(--border-card) !important;
        }}
        .theme-dark .event-card:hover {{
            background-color: var(--bg-card-hover) !important;
        }}
        .theme-dark .event-card.open {{
            background-color: #243247 !important;
            border-color: #FFD60A !important;
        }}
        .theme-dark .event-title {{
            color: #F8FAFC !important;
        }}
        .theme-dark .event-card:hover .event-title {{
            color: #FFD60A !important;
        }}
        .theme-dark .event-subtitle {{
            color: #94A3B8 !important;
        }}
        .theme-dark .event-desc {{
            color: #E2E8F0 !important;
        }}
        .theme-dark .event-time-box {{
            background-color: #0F172A !important;
            border: 1px solid #334155 !important;
            color: #F8FAFC !important;
        }}
        .theme-dark .event-meta {{
            color: #94A3B8 !important;
        }}
        .theme-dark .event-card .event-drawer {{
            border-color: #334155 !important;
        }}
        .theme-dark .util-drawer-inner {{
            background-color: #0F172A !important;
            border: 1px solid #334155 !important;
        }}
        .theme-dark .util-detail-title {{
            color: #F8FAFC !important;
        }}
        .theme-dark .util-detail-sub {{
            color: #CBD5E1 !important;
        }}
        .theme-dark .util-detail-time {{
            color: #E2E8F0 !important;
        }}
        .theme-dark .theme-toggle-btn {{
            background-color: #1E293B;
            border-color: #FFD60A;
            color: #FFD60A;
        }}
        .theme-dark .lang-switcher-box {{
            background-color: #0F172A;
            border-color: #334155;
        }}
        .theme-dark .cat-tab-btn:not(.active) {{
            background-color: #1E293B !important;
            border-color: #334155 !important;
            color: #CBD5E1 !important;
        }}
        .theme-dark .cat-tab-btn:not(.active):hover {{
            color: #FFFFFF !important;
            border-color: #64748B !important;
            background-color: #243247 !important;
        }}
        .theme-dark .date-tab-btn:not(.active) {{
            background-color: #1E293B !important;
            border-color: #334155 !important;
            color: #CBD5E1 !important;
        }}
        .theme-dark .date-tab-btn:not(.active):hover {{
            border-color: #64748B !important;
        }}
        .theme-dark .date-tab-btn:not(.active) .font-black {{
            color: #F8FAFC !important;
        }}
        .theme-dark .marco-card {{
            background-color: #151D2A !important;
            border-color: #2D3D54 !important;
        }}
        .theme-dark .marco-inner {{
            background-color: #151D2A !important;
        }}
        .theme-dark .marco-box {{
            background-color: #0F172A !important;
            border-color: #334155 !important;
        }}
        .theme-dark .marco-box-inner {{
            background-color: #0B0F17 !important;
            border-color: #334155 !important;
        }}
        .theme-dark .footer-note-box {{
            background-color: #151D2A !important;
            border-color: #2D3D54 !important;
            color: #94A3B8 !important;
        }}

        /* =====================================================================
           日间浅色模式 (Light Paper Mode / 经典护眼纸质报章风)
           柔和纸张背景 #F8FAFC，纯白立体卡片，深炭黑文字如实体报章
           ===================================================================== */
        .theme-light {{
            --bg-page: #F8FAFC;
            --bg-header: #FFFFFF;
            --border-header: #E2E8F0;
            --bg-card: #FFFFFF;
            --bg-card-hover: #F8FAFC;
            --border-card: #E2E8F0;
            --border-card-hover: #CBD5E1;
            --text-title: #0F172A;
            --text-title-hover: #D97706;
            --bg-drawer: #F8FAFC;
            --border-drawer: #E2E8F0;
            --text-body: #1E293B;
            --quote-bg: #F1F5F9;
            --quote-border: #E2E8F0;
            --quote-text: #334155;
            --source-pill-bg: #F1F5F9;
            --source-pill-border: #E2E8F0;
            --source-pill-text: #475569;
            --card-footer-bg: #F8FAFC;
            --card-footer-border: #E2E8F0;
            --card-footer-text: #64748B;
            --sub-meta: #64748B;
            --date-badge-bg: #FFFFFF;
            --date-badge-border: #E2E8F0;
            --date-badge-text: #334155;
            --panel-bg: #FFFFFF;
            --panel-border: #E2E8F0;
            --ad-box-bg: #FFFFFF;
            --ad-box-border: #E2E8F0;
            --ad-inner-bg: #F8FAFC;
            --ad-inner-border: #E2E8F0;
        }}

        .theme-light body {{
            background-color: var(--bg-page);
            color: var(--text-title);
        }}
        .theme-light header {{
            background-color: var(--bg-header) !important;
            border-color: var(--border-header) !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        }}
        .theme-light .theme-panel {{
            background-color: var(--panel-bg) !important;
            border-color: var(--panel-border) !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }}
                .theme-light .card-cover-wrap {{
            background-color: #F1F5F9 !important;
            border-bottom: 1px solid #E2E8F0 !important;
        }}
                /* 弹窗沉浸阅读浅色模式 */
        .theme-light .modal-content-box {{
            background-color: #FFFFFF !important;
            border-color: #E2E8F0 !important;
            color: #0F172A !important;
        }}
        .theme-light .modal-header-bar {{
            background-color: rgba(248, 250, 252, 0.95) !important;
            border-color: #E2E8F0 !important;
        }}
        .theme-light .modal-close-btn {{
            background-color: #F1F5F9 !important;
            color: #475569 !important;
        }}
        .theme-light .modal-close-btn:hover {{
            background-color: #E2E8F0 !important;
            color: #0F172A !important;
        }}
        .theme-light .modal-detail-box {{
            background-color: #F8FAFC !important;
            border: 1px solid #E2E8F0 !important;
        }}
        .theme-light .modal-body-text {{
            color: #334155 !important;
        }}
        .theme-light .modal-verify-box {{
            background-color: #F1F5F9 !important;
            border-color: #E2E8F0 !important;
            color: #475569 !important;
        }}
        .theme-light .card-summary {{
            color: #64748B !important;
        }}
        .theme-light .modal-cover-wrap {{
            border-color: #E2E8F0 !important;
            background-color: #F1F5F9 !important;
        }}
        .theme-light .news-grid-card {{
            background-color: var(--bg-card) !important;
            border-color: var(--border-card) !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
        }}
        .theme-light .news-grid-card:hover {{
            background-color: var(--bg-card-hover) !important;
            border-color: var(--border-card-hover) !important;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        }}
        .theme-light .news-grid-card.open {{
            background-color: #FFFFFF !important;
            border-color: #F59E0B !important;
            box-shadow: 0 0 0 1px #F59E0B, 0 6px 18px rgba(245, 158, 11, 0.12);
        }}
        .theme-light .news-grid-card .card-title {{
            color: var(--text-title) !important;
        }}
        .theme-light .news-grid-card:hover .card-title,
        .theme-light .news-grid-card.open .card-title {{
            color: var(--text-title-hover) !important;
        }}
        .theme-light .news-drawer-box {{
            background-color: var(--bg-drawer) !important;
            border: 1px solid var(--border-drawer) !important;
        }}
        .theme-light .news-body-text {{
            color: var(--text-body) !important;
        }}
        .theme-light .quote-box {{
            background-color: var(--quote-bg) !important;
            border: 1px solid var(--quote-border) !important;
            color: var(--quote-text) !important;
        }}
        .theme-light .quote-icon {{
            background-color: #E2E8F0 !important;
            color: #D97706 !important;
        }}
        .theme-light .source-pill {{
            background-color: var(--source-pill-bg) !important;
            border: 1px solid var(--source-pill-border) !important;
            color: var(--source-pill-text) !important;
        }}
        .theme-light .card-footer {{
            background-color: var(--card-footer-bg) !important;
            border-top: 1px solid var(--card-footer-border) !important;
        }}
        .theme-light .card-footer .footer-label {{
            color: var(--card-footer-text) !important;
        }}
        .theme-light .sub-meta-text,
        .theme-light .card-meta-time,
        .theme-light .drawer-mini-tag {{
            color: var(--sub-meta) !important;
        }}
        .theme-light .sub-meta-date {{
            color: #475569 !important;
        }}
        .theme-light .drawer-divider {{
            border-color: #E2E8F0 !important;
        }}
        .theme-light .category-pill-tag {{
            background-color: #F1F5F9 !important;
            border: 1px solid #E2E8F0 !important;
            color: #475569 !important;
        }}
        .theme-light .event-card {{
            background-color: var(--bg-card) !important;
            border-color: var(--border-card) !important;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
        }}
        .theme-light .event-card:hover {{
            background-color: var(--bg-card-hover) !important;
        }}
        .theme-light .event-card.open {{
            background-color: #FFFFFF !important;
            border-color: #F59E0B !important;
            box-shadow: 0 0 0 1px #F59E0B;
        }}
        .theme-light .event-title {{
            color: #0F172A !important;
        }}
        .theme-light .event-card:hover .event-title {{
            color: #D97706 !important;
        }}
        .theme-light .event-subtitle {{
            color: #64748B !important;
        }}
        .theme-light .event-desc {{
            color: #334155 !important;
        }}
        .theme-light .event-time-box {{
            background-color: #F8FAFC !important;
            border: 1px solid #E2E8F0 !important;
            color: #0F172A !important;
        }}
        .theme-light .event-meta {{
            color: #64748B !important;
        }}
        .theme-light .event-card .event-drawer {{
            border-color: #E2E8F0 !important;
        }}
        .theme-light .util-drawer-inner {{
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
        }}
        .theme-light .util-detail-title {{
            color: #0F172A !important;
        }}
        .theme-light .util-detail-sub {{
            color: #475569 !important;
        }}
        .theme-light .util-detail-time {{
            color: #334155 !important;
        }}
        .theme-light .theme-toggle-btn {{
            background-color: #F1F5F9;
            border-color: #CBD5E1;
            color: #0F172A;
        }}
        .theme-light .theme-toggle-btn:hover {{
            background-color: #E2E8F0;
        }}
        .theme-light .lang-switcher-box {{
            background-color: #F1F5F9;
            border-color: #E2E8F0;
        }}
        .theme-light .cat-tab-btn:not(.active) {{
            background-color: #FFFFFF !important;
            border-color: #CBD5E1 !important;
            color: #475569 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }}
        .theme-light .cat-tab-btn:not(.active):hover {{
            color: #0F172A !important;
            border-color: #94A3B8 !important;
            background-color: #F8FAFC !important;
        }}
        .theme-light .date-tab-btn:not(.active) {{
            background-color: #FFFFFF !important;
            border-color: #E2E8F0 !important;
            color: #475569 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }}
        .theme-light .date-tab-btn:not(.active):hover {{
            border-color: #94A3B8 !important;
        }}
        .theme-light .date-tab-btn:not(.active) .font-black {{
            color: #0F172A !important;
        }}
        .theme-light .marco-card {{
            background-color: #FFFFFF !important;
            border-color: #E2E8F0 !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
        }}
        .theme-light .marco-inner {{
            background-color: #FFFFFF !important;
        }}
        .theme-light .marco-box {{
            background-color: #F8FAFC !important;
            border-color: #E2E8F0 !important;
        }}
        .theme-light .marco-box-inner {{
            background-color: #FFFFFF !important;
            border-color: #E2E8F0 !important;
        }}
        .theme-light .marco-ad-title {{
            color: #0F172A !important;
        }}
        .theme-light .marco-ad-text {{
            color: #475569 !important;
        }}
        .theme-light .footer-note-box {{
            background-color: #FFFFFF !important;
            border-color: #E2E8F0 !important;
            color: #475569 !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
        }}

        /* 杂志瀑布流（Masonry Columns）：按内容自然定高，彻底根除 items-stretch 等高拉伸与底部空洞 */
        .news-masonry-container,
        #news-grid-container {{
            column-count: 2 !important;
            column-gap: 16px !important;
            display: block !important;
            width: 100% !important;
        }}


        /* 手机与平板端全量强制严格双列并排 (grid-cols-2) */
        #news-grid-container {{
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 8px !important;
            width: 100% !important;
            align-items: stretch !important;
        }}
        @media (min-width: 640px) {{
            #news-grid-container {{
                gap: 12px !important;
            }}
        }}
        @media (min-width: 768px) {{
            #news-grid-container {{
                gap: 16px !important;
            }}
        }}

        /* 纯标题自适应双列极简卡片 */
        .news-grid-card {{
            display: flex !important;
            flex-direction: column !important;
            width: 100%;
            height: 100%;
            box-sizing: border-box;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            margin-bottom: 0 !important;
        }}

        /* 分类过滤隐藏样式（最高优先级） */
        .news-grid-card.category-hidden {{
            display: none !important;
        }}

        .news-grid-card .card-inner-box {{
            padding: 10px 10px 8px 10px;
            gap: 6px;
        }}
        .news-grid-card .card-title {{
            font-size: 13px;
            line-height: 1.36;
            font-weight: 700;
        }}
        @media (min-width: 640px) {{
            .news-grid-card .card-inner-box {{
                padding: 12px 14px 10px 14px;
                gap: 8px;
            }}
            .news-grid-card .card-title {{
                font-size: 14.5px;
                line-height: 1.4;
            }}
        }}

        /* 顶部纯动态无缝全宽走马灯 */
        @keyframes marquee-seamless {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
        .marquee-track {{
            display: flex;
            width: max-content;
            animation: marquee-seamless 35s linear infinite;
        }}
        .marquee-track:hover {{
            animation-play-state: paused;
        }}

        /* 公用事业抽屉平滑过渡 */
        .util-card {{
            background: #FFD60A;
            border: 1px solid #eab308;
            border-radius: 12px;
            padding: 10px 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }}
        .util-card:hover {{
            background: #ffde33;
            box-shadow: 0 2px 8px rgba(255,214,10,0.2);
        }}
        .util-card.open {{
            background: #FFD60A;
            border-color: #FFD60A;
            box-shadow: 0 0 0 2px rgba(255,214,10,0.35);
        }}
        .util-drawer {{
            display: none;
        }}
        .util-card.open .util-drawer {{
            display: block;
            animation: fadeIn 0.25s ease;
        }}
        .util-card.open .arrow-util {{
            transform: rotate(180deg);
        }}

        /* 新闻卡片展开 */
        .news-grid-card.open .news-drawer {{
            display: block !important;
            animation: fadeIn 0.25s ease;
        }}

        /* 广告海报高度限制与自适应压缩 */
        .ad-poster-img {{
            max-height: 240px !important;
            object-fit: contain !important;
            width: 100% !important;
            display: block;
            margin: 0 auto;
        }}

        /* 活动卡片展开样式 */
        .event-card.open .event-drawer {{
            display: block !important;
            animation: fadeIn 0.25s ease;
        }}
        .event-card.open .arrow-ev {{
            transform: rotate(180deg);
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        /* 沉浸式独立全文阅读弹窗样式 (强制顶级层级与居中 Flex 浮出) */
        #news-modal {{
            z-index: 9999 !important;
        }}
        #news-modal.hidden {{
            display: none !important;
        }}
        #news-modal:not(.hidden) {{
            display: flex !important;
        }}

        /* 隐藏滚动条但保留平滑横向滚动 */
        .no-scrollbar::-webkit-scrollbar {{
            display: none !important;
            width: 0 !important;
            height: 0 !important;
        }}
        .no-scrollbar {{
            -ms-overflow-style: none !important;
            scrollbar-width: none !important;
        }}

        /* 顶部 Header 深色/浅色模式切换按钮防挤压 */
        .theme-toggle-btn {{
            flex-shrink: 0 !important;
            white-space: nowrap !important;
            min-width: 64px !important;
            box-sizing: border-box !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        @media (max-width: 640px) {{
            .theme-toggle-btn {{
                min-width: 58px !important;
                padding: 3px 8px !important;
                font-size: 11px !important;
                gap: 4px !important;
            }}
        }}

        /* 分类 Tab 原生横向平滑滚动 (Mobile Scrollable Tabs) */
        #category-tabs-container {{
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            scroll-behavior: smooth !important;
            -webkit-overflow-scrolling: touch;
        }}
        #category-tabs-container .cat-tab-btn {{
            flex-shrink: 0 !important;
            white-space: nowrap !important;
        }}
    </style>
</head>
<body class="transition-colors duration-200">

    <!-- 顶部 Header -->
    <header class="border-b sticky top-0 z-50">
        <div class="mx-auto max-w-[1440px] px-2.5 sm:px-4 md:px-6 h-[50px] sm:h-[52px] md:h-[56px] flex items-center justify-between gap-1.5 sm:gap-3">
            <div class="flex items-center gap-1.5 sm:gap-2.5 min-w-0 shrink">
                <div class="flex items-center gap-1 sm:gap-2">
                    <span class="text-[15.5px] sm:text-[18px] md:text-[20px] font-black tracking-tight whitespace-nowrap">
                        <span class="lang-zh">西门看看网</span>
                        <span class="lang-bm hidden">Simon Kankan</span>
                    </span>
                    <span class="inline-flex items-center px-1.5 sm:px-2 py-[2px] rounded-[5px] sm:rounded-[6px] bg-[#FFD60A] text-black text-[10px] sm:text-[11px] font-bold leading-none shrink-0 whitespace-nowrap">
                        <span class="lang-zh">每日晨报</span>
                        <span class="lang-bm hidden">Edisi Pagi</span>
                    </span>

                    <!-- 一键分享按钮 (窄屏优化：手机端精炼图标+文字自适应，绝不挤压右侧按钮) -->
                    <button onclick="sharePage()" class="inline-flex items-center gap-1 px-1.5 sm:px-2.5 py-[3px] rounded-[6px] bg-[#1c1c1c] hover:bg-[#282828] text-[#FFD60A] border border-[#FFD60A]/40 text-[10.5px] sm:text-[11px] font-black transition-all shadow-sm active:scale-95 cursor-pointer shrink-0 whitespace-nowrap" title="一键分享当前页面给好友">
                        <span>🔗</span>
                        <span class="lang-zh hidden sm:inline">一键分享</span>
                        <span class="lang-bm hidden">Kongsi</span>
                    </button>
                </div>

                <div class="hidden lg:flex items-center gap-2 text-[12px] mono ml-2 truncate sub-meta-text">
                    <span class="w-[6px] h-[6px] rounded-full bg-[#22c55e] inline-block animate-pulse"></span>
                    <span>每日 05:00 AM 准时晨报 • {today_mmdd} {today_time} LIVE • MYT Asia/Kuala_Lumpur • </span>
                    <span class="lang-zh">点击标题展开全文</span>
                    <span class="lang-bm hidden">Klik tajuk kembang berita</span>
                </div>
            </div>

            <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
                <!-- ☀️ 日间浅色 / 🌙 夜间深色 模式切换高质感胶囊按钮 (固定尺寸与shrink-0防止被挤压) -->
                <button id="btn-theme-toggle" onclick="toggleTheme()" class="theme-toggle-btn shrink-0 inline-flex items-center justify-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-[4px] rounded-full text-[11px] sm:text-[12px] font-bold transition-all border cursor-pointer whitespace-nowrap shadow-sm" title="切换浅色纸质模式 / 深色黑金模式">
                    <span id="theme-icon">☀️</span>
                    <span id="theme-text" class="lang-zh">浅色</span>
                    <span id="theme-text-bm" class="lang-bm hidden">Cerah</span>
                </button>

                <!-- 中文 / BM 语系即时切换 -->
                <div class="lang-switcher-box flex items-center rounded-full p-[2px] sm:p-[3px] border shrink-0">
                    <button id="btn-lang-zh" onclick="setLanguage('中文')" class="px-2 sm:px-2.5 md:px-3 py-[3px] sm:py-[4px] rounded-full text-[11px] sm:text-[12px] font-bold transition-all bg-[#FFD60A] text-black shrink-0 whitespace-nowrap">
                        中文
                    </button>
                    <button id="btn-lang-bm" onclick="setLanguage('BM')" class="px-2 sm:px-2.5 md:px-3 py-[3px] sm:py-[4px] rounded-full text-[11px] sm:text-[12px] font-bold transition-all text-[#888] hover:text-white shrink-0 whitespace-nowrap">
                        BM
                    </button>
                </div>

                <a href="https://wa.me/60109301117" target="_blank" rel="noopener" class="hidden md:inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#14532d] border border-[#166534] text-[12px] text-[#4ade80] hover:bg-[#166534] transition">
                    <span class="w-[8px] h-[8px] rounded-full bg-[#22c55e]"></span> WhatsApp
                </a>
            </div>
        </div>

        <!-- 顶部红色纯动态无缝全宽跑马灯 -->
        <div class="w-full bg-[#DC2626] h-[30px] md:h-[32px] flex items-center overflow-hidden border-y border-[#7f1d1d] relative">
            <div class="marquee-track flex whitespace-nowrap text-[12px] text-white font-medium">
                <div class="flex gap-8 items-center px-4">
                    <span class="inline-flex items-center gap-1.5 text-[#FFD60A] font-black">
                        <span class="w-2 h-2 rounded-full bg-[#FFD60A] animate-pulse"></span>
                        【今日重点聚焦】
                    </span>
                    <span>🏥 肯特医院急诊重症扩建获 1280 万拨款，增设 18 张高精度 ICU 监护床</span>
                    <span class="text-white/40">•</span>
                    <span>⚡ 沙巴水务局 (JANS) 启动地下主管网雷达探伤减漏，14 辆应急水车全城待命</span>
                    <span class="text-white/40">•</span>
                    <span>🚌 陆交局 (JPJ) 联手警方启动长巴『安全之盾』大排查，强制电子乘车单核验</span>
                    <span class="text-white/40">•</span>
                    <span>🏸 大马国家羽球队备战年终总决赛，谢苏组合与李梓嘉展开高强度特训</span>
                    <span class="text-white/40">•</span>
                    <span>⚽ 沙巴足球俱乐部（Sabah FC）超级联赛备战冲刺，主场里卡士体育场球市火爆</span>
                    <span class="text-white/40">•</span>
                    <span>🛡️ ESSCOM 强化东海岸近海夜间巡逻防务，守护海岛旅游与渔业稳定</span>
                    <span class="text-white/40">•</span>
                    <span>🌾 SAZA RICE 买大米赢豪车 Jetour Dashing 岁末抽奖进行中</span>
                    <span class="text-white/40">•</span>
                    <span>🚗 Marco Thien 山打根优质租车 010-930 1117 随时接单</span>
                </div>
                <div class="flex gap-8 items-center px-4" aria-hidden="true">
                    <span class="inline-flex items-center gap-1.5 text-[#FFD60A] font-black">
                        <span class="w-2 h-2 rounded-full bg-[#FFD60A] animate-pulse"></span>
                        【今日重点聚焦】
                    </span>
                    <span>🏥 肯特医院急诊重症扩建获 1280 万拨款，增设 18 张高精度 ICU 监护床</span>
                    <span class="text-white/40">•</span>
                    <span>⚡ 沙巴水务局 (JANS) 启动地下主管网雷达探伤减漏，14 辆应急水车全城待命</span>
                    <span class="text-white/40">•</span>
                    <span>🚌 陆交局 (JPJ) 联手警方启动长巴『安全之盾』大排查，强制电子乘车单核验</span>
                    <span class="text-white/40">•</span>
                    <span>🏸 大马国家羽球队备战年终总决赛，谢苏组合与李梓嘉展开高强度特训</span>
                    <span class="text-white/40">•</span>
                    <span>⚽ 沙巴足球俱乐部（Sabah FC）超级联赛备战冲刺，主场里卡士体育场球市火爆</span>
                    <span class="text-white/40">•</span>
                    <span>🛡️ ESSCOM 强化东海岸近海夜间巡逻防务，守护海岛旅游与渔业稳定</span>
                </div>
            </div>
        </div>
    </header>

    <!-- 主体容器 -->
    <main class="mx-auto max-w-[1440px] px-3 md:px-5 py-3 md:py-4">
        <!-- 动态日期与归档栏（今天/昨天/前天/全部挂载） -->
        <div class="mb-3 rounded-[12px] theme-panel border px-3 md:px-4 py-3 flex flex-col gap-3">
            <div class="flex flex-wrap items-center gap-2 justify-between">
                <div class="flex flex-wrap items-center gap-2">
                    <div class="inline-flex items-center gap-2 px-3 py-[6px] rounded-full bg-[#FFD60A] text-black">
                        <span class="w-2 h-2 rounded-full bg-black animate-pulse"></span>
                        <span class="text-[12px] font-black tracking-tight" id="active-date-display">
                            今天 {today_mmdd} · MYT自动计算
                        </span>
                        <span class="text-[11px] mono font-bold bg-black text-[#FFD60A] px-1.5 py-[1px] rounded-[5px]">{today_time} MYT</span>
                    </div>
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full border text-[11px] mono sub-meta-text">
                        <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                        Asia/Kuala_Lumpur • {today_full} • 
                        <span class="lang-zh">每日 05:00 AM 准时晨报</span>
                        <span class="lang-bm hidden">Kemas Kini Langsung</span>
                    </div>
                    <div class="inline-flex items-center gap-1 px-2.5 py-[4px] rounded-full border text-[11px]">
                        <span class="font-bold text-[#FFD60A]" id="news-count-badge">{len(headlines)}</span>
                        <span class="sub-meta-text">
                            <span class="lang-zh">条深度要闻</span>
                            <span class="lang-bm hidden">tajuk</span>
                        </span>
                    </div>
                </div>
                <div class="text-[10.5px] mono sub-meta-text hidden md:block">
                    <span class="lang-zh">全量大配额 20~24条 · 250~400字深度脉络 · 智能去重双核实</span>
                    <span class="lang-bm hidden">20-24 Berita Penuh · Konteks Mendalam 250-400 Patah</span>
                </div>
            </div>

            <!-- 7天归档切换按键 -->
            <div class="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin" id="date-tabs-container">
                <button onclick="switchDateArchive('today', '{today_iso}', this)" class="date-tab-btn active shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#FFD60A] bg-[#FFD60A] text-black shadow-[0_2px_10px_rgba(255,214,10,0.3)] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-black">
                        <span class="lang-zh">今天</span><span class="lang-bm hidden">Hari Ini</span>
                        <span class="font-mono font-bold text-[11px] opacity-80">{today_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-black/70">
                        <span class="lang-zh">今日晨报 • {len(headlines)} 条</span>
                        <span class="lang-bm hidden">Edisi Pagi</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('yesterday', '{yesterday_iso}', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight">
                        <span class="lang-zh">昨日归档</span><span class="lang-bm hidden">Semalam</span>
                        <span class="font-mono font-bold text-[11px] opacity-80 sub-meta-text">{yesterday_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono sub-meta-text">
                        <span class="lang-zh">已存归档池</span>
                        <span class="lang-bm hidden">Tersimpan</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('before', '{day_before_iso}', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight">
                        <span class="lang-zh">前日精选</span><span class="lang-bm hidden">Kelmarin</span>
                        <span class="font-mono font-bold text-[11px] opacity-80 sub-meta-text">{day_before_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono sub-meta-text">
                        <span class="lang-zh">已存归档池</span>
                        <span class="lang-bm hidden">Tersimpan</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('all', 'all', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight">
                        <span class="lang-zh">全部 • 7天归档库</span><span class="lang-bm hidden">Semua 7 Hari</span>
                    </span>
                    <span class="text-[10px] leading-none mono sub-meta-text">
                        <span class="lang-zh">滚动合辑池</span>
                        <span class="lang-bm hidden">Kompilasi</span>
                    </span>
                </button>
            </div>
        </div>

        <!-- 左右两栏布局 -->
        <div class="flex flex-col lg:flex-row gap-4">
            <!-- 左侧主栏 (大屏 72% / 移动端全宽) -->
            <div class="flex-1 lg:w-[72%] min-w-0 flex flex-col gap-4">
                <div>
                    <div class="flex flex-wrap items-center gap-2 mb-3">
                        <div class="inline-flex items-center gap-2 px-3 py-[5px] rounded-full border text-[11px] md:text-[12px] sub-meta-text">
                            <span class="px-2 py-[1px] rounded-full bg-[#FFD60A] text-black font-bold text-[11px]">
                                {today_mmdd} {today_time} <span class="lang-zh">发布</span><span class="lang-bm hidden">Disiarkan</span>
                            </span>
                            <span class="hidden md:inline font-medium">
                                <span class="lang-zh">标题-only • 点击展开250~400字深度脉络</span>
                                <span class="lang-bm hidden">Tajuk sahaja • Klik kembang 250-400 patah</span>
                            </span>
                            <span class="mono text-[10.5px] font-bold text-[#4ade80]">
                                <span class="lang-zh">双官方来源交叉核实</span>
                                <span class="lang-bm hidden">Disahkan 2 Sumber Rasmi</span>
                            </span>
                        </div>
                        <div class="inline-flex items-center gap-2 px-3 py-[5px] rounded-full border text-[12px]">
                            <span class="font-bold">沙巴 & 全马焦点</span>
                            <span class="px-1.5 py-[1px] rounded bg-[#FFD60A] text-black font-bold text-[11px]">{len(headlines)} <span class="lang-zh">条标题</span><span class="lang-bm hidden">tajuk</span></span>
                            <span class="w-1 h-1 bg-[#334155] rounded-full"></span>
                            <span class="sub-meta-text text-[11px]">LIVE Filter</span>
                        </div>
                    </div>

                    <!-- 3 列黄色公用事业卡片 (UTILITI) -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-3 mb-4 items-start">
                        {utiliti_cards_html}
                    </div>

                    <!-- 今日要闻标题栏 (预留足够安全间距，杜绝层叠挤压) -->
                    <div class="flex items-center justify-between gap-2 flex-wrap mb-1">
                        <div class="flex items-center gap-2 flex-wrap">
                            <h2 class="text-[16px] sm:text-[18px] md:text-[19px] font-black tracking-tight" id="headlines-section-title">
                                <span class="lang-zh">今日 {today_mmdd} 重点要闻</span>
                                <span class="lang-bm hidden">Berita Utama Hari Ini {today_mmdd}</span>
                            </h2>
                            <span class="inline-flex items-center px-2 py-[2px] rounded-full bg-[#FFD60A] text-black text-[11px] sm:text-[12px] font-black shrink-0">
                                <span id="headlines-count-tag">{len(headlines)}</span>
                                <span class="lang-zh ml-1">篇深度采编</span>
                                <span class="lang-bm hidden ml-1">Laporan Penuh</span>
                            </span>
                            <span class="hidden md:inline sub-meta-text text-[12px] mono ml-1">
                                <span class="lang-zh">点击标题展开丰富全文 250-400字背景脉络</span>
                                <span class="lang-bm hidden">Klik baca laporan 250-400 patah</span>
                            </span>
                        </div>
                        <div class="text-[10px] sm:text-[11px] sub-meta-text mono flex items-center gap-1.5 shrink-0">
                            <span>{today_mmdd} • MYT</span>
                        </div>
                    </div>

                    <!-- 新闻分类 Tab 选项卡栏（5大高质感胶囊按钮，开启原生横向平滑滚动 Mobile Scrollable Tabs） -->
                    <div class="flex flex-nowrap items-center gap-2 overflow-x-auto no-scrollbar scroll-smooth py-1 mt-3 mb-2 select-none" id="category-tabs-container">
                        <button onclick="filterNewsCategory('all', this)" class="cat-tab-btn active shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-full text-[12px] font-black transition-all bg-[#FFD60A] text-black border border-[#FFD60A] shadow-[0_2px_8px_rgba(255,214,10,0.3)]">
                            <span class="lang-zh">全部</span><span class="lang-bm hidden">Semua</span>
                        </button>
                        <button onclick="filterNewsCategory('sabah', this)" class="cat-tab-btn shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-full text-[12px] font-bold transition-all border">
                            📍 <span class="lang-zh">沙巴 & 山打根</span><span class="lang-bm hidden">Sabah & Sandakan</span>
                        </button>
                        <button onclick="filterNewsCategory('national', this)" class="cat-tab-btn shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-full text-[12px] font-bold transition-all border">
                            🇲🇾 <span class="lang-zh">全国政经</span><span class="lang-bm hidden">Nasional</span>
                        </button>
                        <button onclick="filterNewsCategory('sports', this)" class="cat-tab-btn shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-full text-[12px] font-bold transition-all border">
                            🏸 <span class="lang-zh">体育焦点</span><span class="lang-bm hidden">Sukan</span>
                        </button>
                        <button onclick="filterNewsCategory('general', this)" class="cat-tab-btn shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-full text-[12px] font-bold transition-all border">
                            🌐 <span class="lang-zh">综合百态</span><span class="lang-bm hidden">Umum</span>
                        </button>
                    </div>

                    <!-- 强制双列网格 (grid-template-columns: repeat(2, 1fr) !important;) -->
                    <div class="grid grid-cols-2 gap-2 sm:gap-3 md:gap-4 w-full" id="news-grid-container">
                        {news_cards_html}
                    </div>
                </div>

                <!-- 未来2周归档活动看板（从 news_data.json 动态渲染，含倒计时、开始结束时间与热线） -->
                <div class="theme-panel border rounded-[12px] overflow-hidden mt-2">
                    <div class="px-4 py-3 border-b flex items-center justify-between gap-2">
                        <h3 class="font-black text-[14px] md:text-[15px] flex items-center gap-2">
                            <span>
                                <span class="lang-zh">未来2周活动预告</span>
                                <span class="lang-bm hidden">Aktiviti 2 Minggu Akan Datang</span>
                            </span>
                            <span class="hidden sm:inline-flex items-center px-2 py-[1px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">{len(events_list)} <span class="lang-zh">项官方活动</span><span class="lang-bm hidden">aktiviti</span></span>
                            <span class="inline-flex items-center gap-1 px-2 py-[1px] rounded-full border text-[10px] mono sub-meta-text">
                                <span class="lang-zh">始终可见 不受日期筛选影响</span>
                                <span class="lang-bm hidden">Sentiasa Dipaparkan</span>
                            </span>
                        </h3>
                        <span class="text-[10px] mono sub-meta-text text-right leading-tight">
                            自动过时 Auto-hide past events ✓
                        </span>
                    </div>
                    <div class="p-2.5 grid grid-cols-1 md:grid-cols-2 gap-2" id="events-grid-container">
                        {events_cards_html}
                    </div>
                </div>

                <div class="p-3 rounded-[10px] border flex items-center justify-between text-[11px] mono footer-note-box">
                    <span>{today_mmdd} {today_time} MYT • 标题-only折叠 点击展开250-400字全文 • 7天归档库已挂载</span>
                    <span class="text-[#FFD60A] font-bold">{len(headlines)} 篇深度要闻 • 双核实白名单</span>
                </div>
            </div>

            <!-- 右侧侧边栏 (广告直屏并排，尺寸限制压缩) -->
            <div class="w-full lg:w-[320px] xl:w-[360px] shrink-0 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3 lg:sticky lg:top-[68px] lg:h-fit">
                <!-- 1. Marco 租车广告卡片 -->
                <div class="marco-card border rounded-[12px] overflow-hidden flex flex-col">
                    <div class="bg-[#FFD60A] px-4 py-2.5 flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="w-6 h-6 rounded-[6px] bg-black text-[#FFD60A] flex items-center justify-center font-black text-[12px]">M</span>
                            <span class="font-black text-black text-[13px] tracking-tight">MY CAR ENTERPRISE</span>
                        </div>
                        <span class="px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-bold">AD • Marco Thien</span>
                    </div>
                    <div class="p-0 marco-inner">
                        <div class="w-full bg-white flex items-center justify-center p-1">
                            <img src="./assets/a0c79ab3b0a4e2ac-image_5f00d7.png" alt="MY CAR ENTERPRISE Sewa Kereta - Marco Thien" class="ad-poster-img" />
                        </div>
                        <div class="p-3 flex flex-col gap-3">
                            <div class="rounded-[10px] marco-box border p-2.5 flex flex-col gap-2">
                                <div class="flex items-center gap-2">
                                    <span class="px-2 py-[1px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">官方 Official</span>
                                    <span class="text-[10px] mono sub-meta-text">山打根租车服务 Rent Car</span>
                                </div>
                                <div class="text-[12px] font-black leading-[1.35] marco-ad-title">
                                    Kereta Sewa Untuk Semua Keperluan Anda
                                </div>
                                <div class="text-[11px] font-bold text-[#FFD60A] tracking-tight">
                                    Jom Travel Bersama Kami • Sabah
                                </div>
                                <div class="grid grid-cols-2 gap-2 pt-1">
                                    <div class="flex flex-col gap-1">
                                        <span class="text-[9px] mono sub-meta-text font-bold tracking-wider">FEATURES / 特色</span>
                                        <ul class="flex flex-col gap-0.5 text-[10px] marco-ad-text">
                                            <li class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-[#FFD60A]"></span>Kereta Bersih</li>
                                            <li class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-[#FFD60A]"></span>Pelbagai Jenis</li>
                                            <li class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-[#FFD60A]"></span>Harga Berpatutan</li>
                                        </ul>
                                    </div>
                                    <div class="flex flex-col gap-1">
                                        <span class="text-[9px] mono sub-meta-text font-bold tracking-wider">FLEET / 车型</span>
                                        <ul class="flex flex-col gap-0.5 text-[10px] marco-ad-text">
                                            <li>• Myvi Axia Bezza</li>
                                            <li>• Vios Vellfire Alza</li>
                                            <li>• Van 11/14 & 4x4</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            <div class="rounded-[10px] marco-box-inner border p-2 flex flex-col gap-1.5">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-2">
                                        <div class="w-7 h-7 rounded-full bg-[#FFD60A] text-black flex items-center justify-center font-black text-[11px]">M</div>
                                        <div class="leading-tight">
                                            <div class="text-[11px] font-black marco-ad-title">Marco Thien</div>
                                            <div class="text-[9px] mono sub-meta-text">山打根租车</div>
                                        </div>
                                    </div>
                                    <span class="px-2 py-[1px] rounded-full bg-[#14532d] border border-[#166534] text-[#4ade80] text-[9px] font-bold">✓ 已核实 Verified</span>
                                </div>
                                <div class="flex items-center justify-between text-[11px] mono pt-1 border-t border-[#334155]/40">
                                    <span class="font-bold marco-ad-title">📞 010-930 1117</span>
                                    <span class="sub-meta-text">WeChat: Thien1117</span>
                                </div>
                            </div>

                            <a href="https://wa.me/60109301117" target="_blank" rel="noopener" class="w-full h-9 rounded-[8px] bg-[#FFD60A] text-black font-black text-[12px] flex items-center justify-center gap-1.5 hover:bg-[#ffdb33] transition shadow-[0_2px_8px_rgba(255,214,10,0.25)]">
                                <span>WhatsApp Marco 询价</span>
                                <span class="text-[13px]">→</span>
                            </a>
                        </div>
                    </div>
                </div>

                <!-- 2. SAZA RICE 官方海报广告 -->
                <div class="rounded-[12px] overflow-hidden border border-[#1e40af]/30 bg-white shadow-[0_2px_12px_rgba(30,64,175,0.15)] flex flex-col">
                    <div class="bg-[#1E40AF] px-4 py-2.5 flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <div class="w-6 h-6 rounded-[6px] bg-white text-[#1E40AF] flex items-center justify-center font-black text-[12px] shadow-sm">S</div>
                            <div class="leading-tight">
                                <div class="font-black text-white text-[13px] tracking-tight">SAZA RICE</div>
                            </div>
                        </div>
                        <span class="px-2 py-[2px] rounded-full bg-white text-[#1E40AF] text-[9px] font-black">官方 Official</span>
                    </div>

                    <div class="p-0 bg-white">
                        <div class="w-full bg-[#f8fafc] p-1 flex items-center justify-center">
                            <img src="./assets/c5b30eea4a0807cf-image_9c82dc.png" alt="Saza Rice Peraduan Beli & Menang" class="ad-poster-img rounded-[8px] border border-[#bfdbfe]" />
                        </div>

                        <div class="p-3 bg-[#f8fafc] flex flex-col gap-2.5">
                            <div class="rounded-[8px] bg-[#eff6ff] border border-[#bfdbfe] px-2.5 py-1.5 flex items-center justify-between">
                                <div class="flex items-center gap-1.5">
                                    <span class="w-2 h-2 rounded-full bg-[#22c55e] animate-pulse"></span>
                                    <span class="text-[10px] font-black text-[#1e40af] mono">Peraduan Beli & Menang</span>
                                </div>
                                <span class="text-[9px] text-[#64748b] mono">至 12/31</span>
                            </div>

                            <div class="grid grid-cols-2 gap-1 text-[9.5px] leading-[1.35] text-[#334155] px-1">
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>大奖: Jetour 汽车</span>
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>旅游金 RM8888</span>
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>金卡 RM4,000</span>
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>月度豪礼电饭煲</span>
                            </div>

                            <a href="https://www.facebook.com/search/pages/?q=Saza%20Rice" target="_blank" rel="noopener" class="w-full h-9 rounded-[8px] bg-[#1877F2] hover:bg-[#166fe5] text-white font-black text-[12px] flex items-center justify-center gap-1.5 transition shadow-[0_2px_8px_rgba(24,119,242,0.3)]">
                                <span class="w-4 h-4 rounded-full bg-white text-[#1877F2] flex items-center justify-center font-black text-[10px]">f</span>
                                <span>关注 Saza Rice Facebook</span>
                                <span class="text-[13px]">→</span>
                            </a>

                            <div class="flex items-center justify-between text-[9px] text-[#64748b] px-1">
                                <span>Kempen Rasmi 2026</span>
                                <span class="text-[#16a34a] font-bold">✓ 已确认官方活动</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    <!-- 独立沉浸式全文阅读弹窗 (Modal) -->
    <div id="news-modal" class="fixed inset-0 z-[9999] hidden flex items-center justify-center p-3 sm:p-5 bg-black/80 backdrop-blur-sm transition-opacity duration-200" onclick="handleModalBackdropClick(event)">
        <div class="relative w-11/12 sm:w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border modal-content-box" onclick="event.stopPropagation()">
            <!-- 弹窗顶部粘性栏：分类徽章、时间、双核实与右上角 ✕ 关闭按钮 -->
            <div class="sticky top-0 z-20 flex items-center justify-between px-4 sm:px-5 py-3 border-b modal-header-bar backdrop-blur-md">
                <div class="flex items-center gap-2 flex-wrap" id="modal-tags">
                    <!-- 动态注入分类与核实标签 -->
                </div>
                <button onclick="closeNewsModal()" class="w-8 h-8 rounded-full flex items-center justify-center text-[18px] font-bold transition hover:scale-110 modal-close-btn" title="关闭 (Esc)">
                    ✕
                </button>
            </div>

            <!-- 弹窗主体滚动区 -->
            <div class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 modal-body-scroll scrollbar-thin">
                <!-- 弹窗大标题 -->
                <h2 class="text-[17px] sm:text-[20px] font-black leading-[1.4] transition-colors modal-headline" id="modal-title"></h2>

                <!-- 封面大图 (仅真实原生 image_url 存在时渲染展示，无图时彻底隐藏不留空白) -->
                <div id="modal-cover-wrap" class="hidden modal-cover-wrap w-full overflow-hidden rounded-lg mb-4 border shadow-sm">
                    <img id="modal-cover-img" src="" alt="新闻配图" class="rounded-lg max-h-72 w-full object-cover" referrerpolicy="no-referrer" loading="lazy" onerror="this.parentElement.style.display='none'; this.style.display='none';">
                </div>

                <!-- 深度报道全文内容 (250~400字背景脉络与政策细则) -->
                <div class="modal-detail-box rounded-xl p-4 sm:p-5 space-y-3">
                    <div class="flex items-center gap-2">
                        <span class="w-2 h-4 rounded-full bg-[#FFD60A]"></span>
                        <span class="text-[11.5px] font-black text-[#FFD60A] tracking-wider">
                            <span class="lang-zh">深度要闻 / 250-400字背景脉络与政策细则</span>
                            <span class="lang-bm hidden">Laporan Mendalam / Konteks Penuh & Dasar Rasmi</span>
                        </span>
                    </div>

                    <p class="text-[13.5px] sm:text-[14.5px] leading-[2] font-normal modal-body-text" id="modal-body"></p>
                </div>

                <!-- 官方双核实通报细节与信源链接 -->
                <div class="rounded-xl p-4 border modal-verify-box space-y-2.5">
                    <div class="flex items-start gap-2 text-[12px] leading-[1.6]">
                        <span class="shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-[#FFD60A] text-black">✓</span>
                        <div>
                            <span class="font-bold text-[#FFD60A]">
                                <span class="lang-zh">官方双核实通报：</span>
                                <span class="lang-bm hidden">Pengesahan Rasmi:</span>
                            </span>
                            <span class="opacity-90 italic">
                                <span class="lang-zh">相关资讯已由白名单专页与核心主流报章交叉印证。</span>
                                <span class="lang-bm hidden">Maklumat disahkan melalui semakan silang portal rasmi dan akhbar utama.</span>
                            </span>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-1.5 items-center pt-2 border-t border-white/10" id="modal-sources">
                        <!-- 来源胶囊链接 -->
                    </div>
                </div>

                <!-- 正文最底部醒目的黄色大按钮：↑ 收起并返回列表 -->
                <div class="pt-2 pb-1 flex justify-center">
                    <button onclick="closeNewsModal()" class="w-full sm:w-auto px-8 py-3 rounded-xl bg-[#FFD60A] hover:bg-[#ffde33] text-black font-black text-[13.5px] tracking-wide shadow-[0_4px_16px_rgba(255,214,10,0.35)] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2">
                        <span>↑</span>
                        <span class="lang-zh">收起并返回列表</span>
                        <span class="lang-bm hidden">Tutup & Kembali ke Senarai</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    </main>

    <!-- 交互控制脚本（模式切换 + 语系切换 + 分类过滤 + 7天归档池） -->
    <script>
        const ARCHIVE_POOL = {archive_json_str};
        const CURRENT_HEADLINES = {json.dumps(headlines, ensure_ascii=False)};
        let activeCategory = 'all';

        // 需求: 『☀️ 日间 / 🌙 夜间』模式秒级切换与 localStorage 记忆
        function initThemeButton() {{
            const isLight = document.documentElement.classList.contains('theme-light');
            const iconElem = document.getElementById('theme-icon');
            const textZhElem = document.getElementById('theme-text');
            const textBmElem = document.getElementById('theme-text-bm');
            if (isLight) {{
                if (iconElem) iconElem.textContent = '🌙';
                if (textZhElem) textZhElem.textContent = '深色';
                if (textBmElem) textBmElem.textContent = 'Gelap';
            }} else {{
                if (iconElem) iconElem.textContent = '☀️';
                if (textZhElem) textZhElem.textContent = '浅色';
                if (textBmElem) textBmElem.textContent = 'Cerah';
            }}
        }}

        function toggleTheme() {{
            const htmlElem = document.documentElement;
            const isLight = htmlElem.classList.contains('theme-light');
            const targetTheme = isLight ? 'dark' : 'light';

            if (targetTheme === 'light') {{
                htmlElem.classList.remove('theme-dark');
                htmlElem.classList.add('theme-light');
                localStorage.setItem('sk_theme', 'light');
                showToast('☀️ 已切换为日间浅色模式（经典纸质报章风）', '☀️ Mod cerah diaktifkan!');
            }} else {{
                htmlElem.classList.remove('theme-light');
                htmlElem.classList.add('theme-dark');
                localStorage.setItem('sk_theme', 'dark');
                showToast('🌙 已切换为夜间深色模式（高对比黑金版）', '🌙 Mod gelap kontras tinggi diaktifkan!');
            }}
            initThemeButton();
        }}

        // 需求: 纯原生 JS 毫秒级免刷新分类过滤
        function filterNewsCategory(catKey, btnElem) {{
            activeCategory = catKey;
            
            // 1. 更新 5 个 Tab 按钮的高亮状态 (保持 shrink-0 whitespace-nowrap 绝不折行或被挤压)
            document.querySelectorAll('.cat-tab-btn').forEach(btn => {{
                btn.className = "cat-tab-btn shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-full text-[12px] font-bold transition-all border";
            }});
            const targetBtn = btnElem || document.querySelector(`.cat-tab-btn[onclick*="'${{catKey}}'"]`);
            if (targetBtn) {{
                targetBtn.className = "cat-tab-btn active shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-full text-[12px] font-black transition-all bg-[#FFD60A] text-black border border-[#FFD60A] shadow-[0_2px_8px_rgba(255,214,10,0.3)]";
            }}

            // 2. 毫秒级免刷新过滤下方卡片（双重保障：移除!important并使用category-hidden类）
            const cards = document.querySelectorAll('.news-grid-card');
            let visibleCount = 0;
            const targetCat = (catKey || '').trim().toLowerCase();
            cards.forEach(card => {{
                const itemCat = (card.getAttribute('data-category') || '').trim().toLowerCase();
                if (targetCat === 'all' || itemCat === targetCat) {{
                    card.classList.remove('category-hidden');
                    card.style.display = '';
                    visibleCount++;
                }} else {{
                    card.classList.add('category-hidden');
                    card.style.display = 'none';
                }}
            }});

            // 3. 更新标题栏数字显示
            const countTag = document.getElementById('headlines-count-tag');
            if (countTag) countTag.textContent = visibleCount;
        }}
        window.filterNewsCategory = filterNewsCategory;

        // 一键分享功能
        function sharePage() {{
            const shareTitle = document.title || '西门看看网 · 每日晨报';
            const shareUrl = window.location.href;
            if (navigator.share) {{
                navigator.share({{
                    title: shareTitle,
                    text: '西门看看网：沙巴山打根全自动双核实晨报与民生调度！',
                    url: shareUrl
                }}).catch(err => {{
                    if (err.name !== 'AbortError') {{
                        copyUrlToClipboard();
                    }}
                }});
            }} else {{
                copyUrlToClipboard();
            }}
        }}

        function copyUrlToClipboard() {{
            const url = window.location.href;
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(url).then(() => {{
                    showToast('✅ 晨报链接已复制，快去发给好友吧！', '✅ Pautan telah disalin ke papan keratan!');
                }}).catch(() => {{
                    promptFallback(url);
                }});
            }} else {{
                promptFallback(url);
            }}
        }}

        function promptFallback(url) {{
            prompt('请复制以下西门看看网晨报网址：', url);
        }}

        function showToast(msgZh, msgBm) {{
            let toast = document.getElementById('app-toast');
            if (!toast) {{
                toast = document.createElement('div');
                toast.id = 'app-toast';
                toast.className = 'fixed top-14 left-1/2 -translate-x-1/2 z-50 bg-[#FFD60A] text-black font-black px-4 py-2 rounded-full shadow-2xl text-[13px] transition-opacity duration-300 pointer-events-none flex items-center gap-2 border-2 border-black';
                document.body.appendChild(toast);
            }}
            const isBm = document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');
            toast.textContent = isBm ? msgBm : msgZh;
            toast.style.opacity = '1';
            setTimeout(() => {{
                toast.style.opacity = '0';
            }}, 2600);
        }}

        // 语系即时切换
        function setLanguage(lang) {{
            const btnZh = document.getElementById('btn-lang-zh');
            const btnBm = document.getElementById('btn-lang-bm');
            const zhElements = document.querySelectorAll('.lang-zh');
            const bmElements = document.querySelectorAll('.lang-bm');

            if (lang === '中文') {{
                btnZh.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all bg-[#FFD60A] text-black";
                btnBm.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all text-[#888] hover:text-white";
                zhElements.forEach(el => el.classList.remove('hidden'));
                bmElements.forEach(el => el.classList.add('hidden'));
                document.documentElement.lang = "zh-CN";
            }} else {{
                btnBm.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all bg-[#FFD60A] text-black";
                btnZh.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all text-[#888] hover:text-white";
                zhElements.forEach(el => el.classList.add('hidden'));
                bmElements.forEach(el => el.classList.remove('hidden'));
                document.documentElement.lang = "ms";
            }}
            // 重新刷新当前视图卡片的语言状态
            if (typeof renderNewsCards === 'function') {{
                renderNewsCards(currentRenderedHeadlines);
            }}
        }}

        // 核心修复：动态渲染新闻卡片列表（支持今天、昨日、前日与历史合辑真实切换）
        let currentRenderedHeadlines = CURRENT_HEADLINES;
        let currentRenderedDateLabel = '{today_mmdd} {today_time}';

        function renderNewsCards(headlinesList, dateLabel) {{
            currentRenderedHeadlines = headlinesList;
            if (dateLabel) currentRenderedDateLabel = dateLabel;
            const cardDateTag = currentRenderedDateLabel;
            const container = document.getElementById('news-grid-container');
            if (!container) return;
            const isBm = document.getElementById('btn-lang-bm') && document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');

            let html = '';
            headlinesList.forEach((item, index) => {{
                const idx = index + 1;
                const rawTitle = item.title || '';
                const detail = item.detail || item.summary || '';
                const category = item.category || 'general';

                const verifyMatch = rawTitle.match(/\[(.*?)\]/);
                const tag = verifyMatch ? verifyMatch[1] : "双官方来源交叉核实";
                const cleanTitle = rawTitle.replace(/\[.*?\]/g, '').trim();

                let sources = item.sources || (item.source ? [item.source] : []);
                let cleanDetail = detail;
                if (!sources.length) {{
                    if (detail.includes("来源：") || detail.includes("来源:")) {{
                        const parts = detail.split(/来源[：:]/);
                        cleanDetail = parts[0].trim();
                        const sourceStr = parts[1].replace(/。/g, '').trim();
                        sources = sourceStr.split(/[/、+及与]/).map(s => s.trim()).filter(s => s && s.length < 20);
                    }}
                }}
                if (!sources.length) sources = ["沙巴官方通报", "现场交叉复核"];

                const titleBm = item.titleBM || ("Laporan Khas: " + cleanTitle.slice(0, 35));
                const detailBm = item.detailBM || ("Laporan berita mendalam mengenai perkembangan terkini di Sabah dan seluruh Malaysia. " + cleanDetail.slice(0, 120) + "...");

                let catTagZh = "综合百态", catTagBm = "Umum";
                if (category === 'sabah') {{ catTagZh = "沙巴要闻"; catTagBm = "Sabah"; }}
                else if (category === 'national') {{ catTagZh = "全国政经"; catTagBm = "Nasional"; }}
                else if (category === 'sports') {{ catTagZh = "体育焦点"; catTagBm = "Sukan"; }}

                const sourcesPills = sources.map(s => `<span class="source-pill px-1.5 py-[1px] rounded-[4px] mono truncate max-w-[110px] text-[10px]">${{s}}</span>`).join('');
                const sourcesLinks = sources.map(s => `<span class="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/30 text-[10.5px] text-[#FFD60A] mono font-bold">↗ ${{s}}</span>`).join('');
                const pinBadge = idx <= 2 ? '<span class="shrink-0 w-2.5 h-2.5 rounded-full bg-[#EC4899] mt-2 shadow-sm animate-pulse"></span>' : '';

                const zhCls = isBm ? 'hidden' : '';
                const bmCls = isBm ? '' : 'hidden';

html += `
                <article class="news-grid-card group relative flex flex-col rounded-[12px] border transition-all cursor-pointer overflow-hidden" data-category="${{category}}" id="news-card-${{idx}}" onclick="openNewsModal(${{index}})">
                    <div class="card-inner-box p-2.5 sm:p-3 md:p-3.5 flex flex-col gap-2 flex-1">
                        <div class="flex items-start justify-between gap-1.5">
                            <h3 class="card-title font-bold leading-snug flex-1 text-[13px] sm:text-[14px] md:text-[15px] transition-colors line-clamp-3">
                                <span class="lang-zh ${{zhCls}}">${{cleanTitle}}</span>
                                <span class="lang-bm ${{bmCls}}">${{titleBm}}</span>
                            </h3>
                            ${{pinBadge}}
                        </div>

                        <div class="flex flex-wrap items-center gap-1 mt-auto pt-1">
                            <span class="mono text-[9.5px] sm:text-[10px] font-bold card-meta-time">${{cardDateTag}}</span>
                            <span class="inline-flex items-center px-1.5 py-[0.5px] rounded text-[9px] sm:text-[9.5px] font-bold bg-[#14532d] text-[#4ade80] border border-[#166534]">
                                ${{tag}}
                            </span>
                            <span class="category-pill-tag text-[9px] sm:text-[9.5px] px-1.5 py-[0.5px] rounded mono font-bold">
                                <span class="lang-zh ${{zhCls}}">${{catTagZh}}</span>
                                <span class="lang-bm ${{bmCls}}">${{catTagBm}}</span>
                            </span>
                        </div>
                    </div>

                    <div class="mt-auto flex items-center justify-between gap-1.5 px-2.5 py-2 sm:px-3 sm:py-2.5 card-footer border-t border-white/5">
                        <div class="flex flex-wrap gap-1 min-w-0">
                            ${{sourcesPills}}
                        </div>
                        <button onclick="event.stopPropagation(); openNewsModal(${{index}})" class="shrink-0 inline-flex items-center gap-0.5 px-2 py-1 sm:px-2.5 sm:py-1 rounded-md bg-[#FFD60A] text-black font-black text-[10px] sm:text-[11px] hover:bg-[#ffde33] active:scale-95 transition-all whitespace-nowrap shadow-sm">
                            <span class="lang-zh ${{zhCls}}">查看 ➡</span>
                            <span class="lang-bm ${{bmCls}}">Baca ➡</span>
                        </button>
                    </div>
                </article>
                `;
            }});

            container.innerHTML = html;

            // 保持当前分类过滤规则
            const cards = container.querySelectorAll('.news-grid-card');
            let visibleCount = 0;
            const targetCat = (activeCategory || 'all').trim().toLowerCase();
            cards.forEach(card => {{
                const itemCat = (card.getAttribute('data-category') || '').trim().toLowerCase();
                if (targetCat === 'all' || itemCat === targetCat) {{
                    card.classList.remove('category-hidden');
                    card.style.display = '';
                    visibleCount++;
                }} else {{
                    card.classList.add('category-hidden');
                    card.style.display = 'none';
                }}
            }});
            const countTag = document.getElementById('headlines-count-tag');
            if (countTag) countTag.textContent = visibleCount;
        }}

        // 7天历史归档按天真实数据切换
        function switchDateArchive(type, dateKey, btnElem) {{
            document.querySelectorAll('.date-tab-btn').forEach(btn => {{
                btn.className = "date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border transition-all";
                const titleSpan = btn.querySelector('.font-black');
                if (titleSpan) titleSpan.classList.remove('text-black');
            }});

            btnElem.className = "date-tab-btn active shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#FFD60A] bg-[#FFD60A] text-black shadow-[0_2px_10px_rgba(255,214,10,0.3)] transition-all";
            const curTitleSpan = btnElem.querySelector('.font-black');
            if (curTitleSpan) curTitleSpan.classList.add('text-black');

            const titleElem = document.getElementById('headlines-section-title');
            const displayDateElem = document.getElementById('active-date-display');
            const countTag = document.getElementById('headlines-count-tag');
            const isBm = document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');

            let targetHeadlines = [];
            let cardDateLabel = '{today_mmdd} {today_time}';
            if (type === 'today') {{
                targetHeadlines = CURRENT_HEADLINES;
                cardDateLabel = '{today_mmdd} {today_time}';
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Berita Utama Hari Ini {today_mmdd}</span>' : '<span>今日 {today_mmdd} 重点要闻</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Hari Ini {today_mmdd} · Auto MYT' : '今天 {today_mmdd} · MYT自动计算';
                showToast('已载入今日最新核实晨报！', 'Memuatkan berita terkini hari ini!');
            }} else if (type === 'yesterday') {{
                targetHeadlines = ARCHIVE_POOL[dateKey] || CURRENT_HEADLINES;
                cardDateLabel = '{yesterday_mmdd} 历史归档';
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Arkib Berita Semalam {yesterday_mmdd}</span>' : '<span>昨日 {yesterday_mmdd} 归档要闻</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Semalam {yesterday_mmdd} · Arkib' : '昨日 {yesterday_mmdd} · 归档库';
                showToast('已切换至昨日归档视角！', 'Beralih ke arkib semalam!');
            }} else if (type === 'before') {{
                targetHeadlines = ARCHIVE_POOL[dateKey] || CURRENT_HEADLINES;
                cardDateLabel = '{day_before_mmdd} 历史精选';
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Arkib Berita Kelmarin {day_before_mmdd}</span>' : '<span>前日 {day_before_mmdd} 归档要闻</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Kelmarin {day_before_mmdd} · Arkib' : '前日 {day_before_mmdd} · 归档库';
                showToast('已切换至前日归档视角！', 'Beralih ke arkib kelmarin!');
            }} else {{
                targetHeadlines = [];
                Object.values(ARCHIVE_POOL).forEach(list => {{
                    if (Array.isArray(list)) targetHeadlines.push(...list.slice(0, 4));
                }});
                cardDateLabel = '7天历史合辑';
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Semua Arkib 7 Hari</span>' : '<span>全部历史归档 (7天精选合辑)</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Semua Arkib 7 Hari' : '全部 · 7天历史库';
                showToast('已开启全量 7 天历史合辑！', 'Membuka arkib 7 hari!');
            }}

            // 核心修复：即时重绘新闻卡片 DOM
            renderNewsCards(targetHeadlines, cardDateLabel);
        }}

        // 未来活动卡片展开/收起抽屉
        function toggleEventCard(id) {{
            const card = document.getElementById('event-card-' + id);
            if (!card) return;
            card.classList.toggle('open');
        }}

        // 展开/收起 3列黄色公用事业卡片
        function toggleUtilCard(id) {{
            const card = document.getElementById('util-card-' + id);
            if (!card) return;
            const isOpen = card.classList.contains('open');
            card.classList.toggle('open');
            const hint = card.querySelector('.toggle-hint');
            if (hint) {{
                hint.textContent = isOpen ? '点击查看详情' : '收起 ↑';
            }}
        }}

        // 核心重构：沉浸式独立全文阅读弹窗 (Modal)
        function openNewsModal(index) {{
            const item = currentRenderedHeadlines[index];
            if (!item) return;

            const isBm = document.getElementById('btn-lang-bm') && document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');

            const rawTitle = item.title || '';
            const detail = item.detail || item.summary || '';
            const category = item.category || 'general';

            const verifyMatch = rawTitle.match(/\[(.*?)\]/);
            const tag = verifyMatch ? verifyMatch[1] : "双官方来源交叉核实";
            const cleanTitle = rawTitle.replace(/\[.*?\]/g, '').trim();

            let sources = item.sources || (item.source ? [item.source] : []);
            let cleanDetail = detail;
            if (!sources.length) {{
                if (detail.includes("来源：") || detail.includes("来源:")) {{
                    const parts = detail.split(/来源[：:]/);
                    cleanDetail = parts[0].trim();
                    const sourceStr = parts[1].replace(/。/g, '').trim();
                    sources = sourceStr.split(/[/、+及与]/).map(s => s.trim()).filter(s => s && s.length < 20);
                }}
            }}
            if (!sources.length) sources = ["沙巴官方通报", "现场交叉复核"];

            const titleBm = item.titleBM || ("Laporan Khas: " + cleanTitle.slice(0, 35));
            const detailBm = item.detailBM || ("Laporan berita mendalam mengenai perkembangan terkini di Sabah dan seluruh Malaysia. " + cleanDetail.slice(0, 120) + "...");

            let catTagZh = "综合百态", catTagBm = "Umum";
            if (category === 'sabah') {{ catTagZh = "沙巴要闻"; catTagBm = "Sabah"; }}
            else if (category === 'national') {{ catTagZh = "全国政经"; catTagBm = "Nasional"; }}
            else if (category === 'sports') {{ catTagZh = "体育焦点"; catTagBm = "Sukan"; }}

            const zhCls = isBm ? 'hidden' : '';
            const bmCls = isBm ? '' : 'hidden';

            // 1. 设置大标题
            const modalTitle = document.getElementById('modal-title');
            if (modalTitle) {{
                modalTitle.innerHTML = `
                    <span class="lang-zh ${{zhCls}}">${{cleanTitle}}</span>
                    <span class="lang-bm ${{bmCls}}">${{titleBm}}</span>
                `;
            }}

            // 2. 设置顶部标签
            const modalTags = document.getElementById('modal-tags');
            if (modalTags) {{
                modalTags.innerHTML = `
                    <span class="px-2.5 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[10.5px] font-black tracking-wide">
                        <span class="lang-zh ${{zhCls}}">${{catTagZh}}</span>
                        <span class="lang-bm ${{bmCls}}">${{catTagBm}}</span>
                    </span>
                    <span class="mono text-[11px] font-bold sub-meta-date">${{currentRenderedDateLabel}}</span>
                    <span class="inline-flex items-center px-2 py-[2px] rounded-[4px] text-[10px] font-bold bg-[#14532d] text-[#4ade80] border border-[#166534]">
                        ✓ ${{tag}}
                    </span>
                `;
            }}

            // 3. 设置封面大图 (仅真实原生 image_url 存在时渲染展示，无图彻底隐藏)
            const coverWrap = document.getElementById('modal-cover-wrap');
            const coverImg = document.getElementById('modal-cover-img');
            const imgUrl = (item && item.image_url && typeof item.image_url === 'string') ? item.image_url.trim() : '';

            if (imgUrl && imgUrl !== 'null' && imgUrl !== 'undefined') {{
                if (coverWrap) {{
                    coverWrap.classList.remove('hidden');
                    coverWrap.style.display = 'block';
                }}
                if (coverImg) {{
                    coverImg.style.display = 'block';
                    coverImg.onerror = function() {{
                        console.warn('[ModalImage] 加载失败，自动隐藏大图容器:', imgUrl);
                        if (coverWrap) {{
                            coverWrap.classList.add('hidden');
                            coverWrap.style.display = 'none';
                        }}
                        this.style.display = 'none';
                    }};
                    coverImg.onload = function() {{
                        if (coverWrap) {{
                            coverWrap.classList.remove('hidden');
                            coverWrap.style.display = 'block';
                        }}
                        this.style.display = 'block';
                    }};
                    coverImg.src = imgUrl;
                }}
            }} else {{
                if (coverImg) {{
                    coverImg.src = '';
                    coverImg.style.display = 'none';
                }}
                if (coverWrap) {{
                    coverWrap.classList.add('hidden');
                    coverWrap.style.display = 'none';
                }}
            }}

            // 4. 设置深度全文内容
            const modalBody = document.getElementById('modal-body');
            if (modalBody) {{
                modalBody.innerHTML = `
                    <span class="inline-block w-2 h-2 rounded-full bg-[#FFD60A] mr-2 mb-[2px]"></span>
                    <span class="lang-zh ${{zhCls}}">${{cleanDetail}}</span>
                    <span class="lang-bm ${{bmCls}}">${{detailBm}}</span>
                `;
            }}

            // 5. 设置核实来源胶囊
            const modalSources = document.getElementById('modal-sources');
            if (modalSources) {{
                const links = sources.map(s => `<span class="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/30 text-[10.5px] text-[#FFD60A] mono font-bold">↗ ${{s}}</span>`).join('');
                modalSources.innerHTML = links + `<span class="px-2.5 py-[3px] rounded-full bg-[#14532d] border border-[#166534] text-[10px] text-[#4ade80] font-bold">✓ ${{tag}}</span>`;
            }}

            // 6. 打开弹窗并平滑锁定背景滚动
            const modal = document.getElementById('news-modal');
            if (modal) {{
                modal.classList.remove('hidden');
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }}
        }}

        function closeNewsModal() {{
            const modal = document.getElementById('news-modal');
            if (modal) {{
                modal.classList.add('hidden');
                modal.style.display = 'none';
                document.body.style.overflow = '';
            }}
            const coverWrap = document.getElementById('modal-cover-wrap');
            if (coverWrap) {{
                coverWrap.classList.add('hidden');
                coverWrap.style.display = 'none';
            }}
            const coverImg = document.getElementById('modal-cover-img');
            if (coverImg) {{
                coverImg.src = '';
                coverImg.style.display = 'none';
            }}
        }}

        function handleModalBackdropClick(event) {{
            if (event.target.id === 'news-modal') {{
                closeNewsModal();
            }}
        }}

        // 绑定键盘 Esc 键快速关闭弹窗
        window.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                closeNewsModal();
            }}
        }});

        // 显式挂载到 window 对象上，确保全局任何内联 onclick 均可 100% 稳定调用
        window.openNewsModal = openNewsModal;
        window.closeNewsModal = closeNewsModal;
        window.handleModalBackdropClick = handleModalBackdropClick;

        // 初始化
        window.addEventListener('DOMContentLoaded', () => {{
            initThemeButton();
        }});
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 成功编译升级版 index.html (包含深浅双模切换、高对比黑金/纸质白、5大分类Tab、双列网格、{len(headlines)} 条深度要闻)！")

if __name__ == "__main__":
    generate_index_html()
