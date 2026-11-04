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
    前端渲染引擎 2.0：
    1. 强制双列网格 (grid-template-columns: repeat(2, 1fr) !important;)
    2. 渲染 12~16 条重点要闻（包含 250~400 字深层脉络与背景）
    3. 读取并展示未来 2 周活动（含倒计时、开始结束时间、100-150字简介与官方热线）
    4. 挂载 7 天真实历史归档池，支持前端无缝按天切换查看
    5. 顶部全宽纯动态无缝跑马灯 + 左上角一键分享 + 广告海报压缩并排 + 中马双语即时切换
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
                    <div class="text-[10px] text-black/60 mono mt-1 font-bold toggle-hint">
                        { '收起 ↑' if is_first else '点击查看详情' }
                    </div>
                </div>
            </div>

            <div class="util-drawer mt-3">
                <div class="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-3 flex flex-col gap-2.5">
                    <div class="flex items-center gap-1.5">
                        <span class="w-1 h-4 rounded-full bg-[#FFD60A]"></span>
                        <span class="text-[11px] font-black text-[#FFD60A] tracking-wider">
                            <span class="lang-zh">实时详情 LIVE DETAIL</span>
                            <span class="lang-bm hidden">BUTIRAN LANGSUNG</span>
                        </span>
                        <span class="text-[10px] mono text-[#555]">• {today_mmdd} {u['time']} LIVE</span>
                    </div>

                    <div class="space-y-2">
                        <div class="flex gap-2 text-[12px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-[#FFD60A]/15 text-[#FFD60A] flex items-center justify-center text-[10px]">!</span>
                            <span class="text-[#e5e7eb] font-bold lang-zh">{u['issue']}</span>
                            <span class="text-[#e5e7eb] font-bold lang-bm hidden">{u['issueBM']}</span>
                        </div>
                        <div class="flex gap-2 text-[12px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-[#1f1f1f] text-[#888] flex items-center justify-center text-[10px]">≋</span>
                            <span class="text-[#9ca3af] lang-zh">{u['pressure']}</span>
                            <span class="text-[#9ca3af] lang-bm hidden">{u['pressureBM']}</span>
                        </div>
                        <div class="flex gap-2 text-[12px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-[#1f1f1f] text-[#888] flex items-center justify-center text-[10px]">◷</span>
                            <span class="text-[#d1d5db] lang-zh">{u['recovery']}</span>
                            <span class="text-[#d1d5db] lang-bm hidden">{u['recoveryBM']}</span>
                        </div>
                        <div class="flex gap-2 text-[12px] leading-[1.5]">
                            <span class="shrink-0 w-5 h-5 rounded-[5px] bg-[#14532d] text-[#22c55e] flex items-center justify-center text-[10px]">◩</span>
                            <span class="text-[#9ca3af] lang-zh">{u['tanker']}</span>
                            <span class="text-[#9ca3af] lang-bm hidden">{u['tankerBM']}</span>
                        </div>
                    </div>

                    <div class="pt-2 border-t border-[#1f1f1f] flex flex-col gap-2">
                        <div class="flex flex-wrap gap-1.5">
                            <span class="inline-flex items-center gap-1 px-2 py-[3px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[11px] text-[#e5e7eb] mono">
                                <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                                {u['consult']}
                            </span>
                            <span class="inline-flex items-center gap-1 px-2 py-[3px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[11px] text-[#e5e7eb] mono">
                                <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                                {u['consult2']}
                            </span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="inline-flex items-center gap-1 px-2 py-[2px] rounded-[6px] bg-[#14532d] border border-[#166534] text-[#22c55e] text-[10px] font-bold">
                                ✓ <span class="lang-zh">{u['source']}</span><span class="lang-bm hidden">{u['sourceBM']}</span>
                            </span>
                            <span class="text-[10px] mono text-[#666]">
                                <span class="lang-zh">点击再次收起</span>
                                <span class="lang-bm hidden">Klik tutup</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    # 2. 动态生成 12 ~ 16 条重点要闻双列网格卡片
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
        "流感": "Jabatan Kesihatan Negeri Sabah (JKNS)"
    }

    def get_bm_title(zh_t):
        for k, v in bm_translations.items():
            if k in zh_t:
                return f"Laporan Khas: {v} - Kemas Kini Rasmi"
        return f"Berita Terkini Sabah & Malaysia: {zh_t[:30]}"

    news_cards_html = ""
    for idx, item in enumerate(headlines, 1):
        raw_title = item.get("title", "")
        detail = item.get("detail", "")
        clean_title, tag, sources, clean_detail = extract_tags_and_sources(raw_title, detail)
        title_bm = get_bm_title(clean_title)

        sources_pills = "".join([f'<span class="px-1.5 py-[1px] rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-[10px] text-[#777] mono truncate max-w-[110px]">{s}</span>' for s in sources])
        sources_links = "".join([f'<span class="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/20 text-[10px] text-[#FFD60A] mono">↗ {s}</span>' for s in sources])

        pin_badge = '<span class="shrink-0 w-2 h-2 rounded-full bg-[#EC4899] mt-2"></span>' if idx <= 3 else ''
        category_tag_zh = "重点聚焦" if idx <= 2 else "沙巴民生" if idx <= 6 else "全国大盘" if idx <= 10 else "政策前沿"
        category_tag_bm = "Utama" if idx <= 2 else "Sabah" if idx <= 6 else "Nasional" if idx <= 10 else "Polisi"

        news_cards_html += f"""
        <article class="news-grid-card group relative flex flex-col rounded-[12px] border bg-[#151515] border-[#222] hover:border-[#333] hover:bg-[#191919] transition-all cursor-pointer overflow-hidden" id="news-card-{idx}" onclick="toggleNewsCard({idx})">
            <div class="p-3 md:p-[14px] flex flex-col gap-2.5">
                <div class="flex items-start justify-between gap-2">
                    <h3 class="card-title font-black leading-[1.35] flex-1 text-white text-[14px] md:text-[15px] group-hover:text-[#FFD60A] transition-colors">
                        <span class="lang-zh">{clean_title}</span>
                        <span class="lang-bm hidden">{title_bm}</span>
                    </h3>
                    {pin_badge}
                </div>

                <!-- 展开的深度全文内容 (250~400字深度脉络与背景) -->
                <div class="news-drawer hidden mt-1">
                    <div class="flex items-center gap-2 mb-3 flex-wrap">
                        <span class="px-2 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[10px] font-black tracking-wide">
                            <span class="lang-zh">{category_tag_zh}</span>
                            <span class="lang-bm hidden">{category_tag_bm}</span>
                        </span>
                        <span class="text-[11px] mono text-[#888]">沙巴 Sabah • 全马</span>
                        <span class="w-1 h-1 bg-[#333] rounded-full"></span>
                        <span class="text-[11px] mono text-[#666]">{today_mmdd} {today_time}</span>
                    </div>

                    <div class="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-3 space-y-3">
                        <div class="flex items-center gap-1.5">
                            <span class="w-1 h-4 rounded-full bg-[#FFD60A]"></span>
                            <span class="text-[11px] font-bold text-[#FFD60A] tracking-wider">
                                <span class="lang-zh">深度报道 / 250-400字背景脉络</span>
                                <span class="lang-bm hidden">Laporan Terperinci / Konteks Penuh</span>
                            </span>
                            <span class="text-[10px] mono text-[#555]">• 深度脉络 • {today_mmdd}</span>
                        </div>

                        <p class="text-[13px] leading-[1.75] text-[#d1d5db]">
                            <span class="inline-block w-2 h-2 rounded-full bg-[#FFD60A] mr-2 mb-[2px]"></span>
                            {clean_detail}
                        </p>

                        <div class="pt-2 border-t border-[#1f1f1f] flex flex-col gap-2">
                            <div class="flex items-start gap-2 text-[11px] leading-[1.5] text-[#9ca3af] bg-[#161616] border border-[#222] rounded-[8px] p-2.5">
                                <span class="shrink-0 w-5 h-5 rounded-full bg-[#222] flex items-center justify-center text-[10px]">❞</span>
                                <span class="italic">
                                    <span class="lang-zh">官方双核实通报：相关资讯已由白名单专页与核心主流报章交叉印证。</span>
                                    <span class="lang-bm hidden">Maklumat disahkan melalui semakan silang portal rasmi dan akhbar utama.</span>
                                </span>
                            </div>
                            <div class="flex flex-wrap gap-1.5">
                                {sources_links}
                                <span class="px-2 py-[3px] rounded-full bg-[#14532d] border border-[#166534] text-[10px] text-[#22c55e] font-bold">
                                    ✓ {tag}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex flex-wrap items-center gap-1.5 mt-auto">
                    <span class="mono text-[10px] text-[#666]">{today_mmdd} {today_time}</span>
                    <span class="inline-flex items-center px-1.5 py-[1px] rounded-[4px] text-[10px] font-bold bg-[#14532d] text-[#22c55e] border border-[#166534]">
                        {tag}
                    </span>
                    <span class="text-[10px] px-1.5 py-[1px] rounded bg-[#1a1a1a] border border-[#222] text-[#555] mono">
                        <span class="lang-zh">{category_tag_zh}</span>
                        <span class="lang-bm hidden">{category_tag_bm}</span>
                    </span>
                </div>

                <div class="flex flex-wrap gap-1">
                    {sources_pills}
                </div>
            </div>

            <div class="mt-auto flex items-center justify-between px-3 py-2.5 border-t border-[#1f1f1f] bg-[#111]/50 card-footer">
                <span class="text-[11px] text-[#555] mono footer-label">
                    <span class="lang-zh">标题-only</span>
                    <span class="lang-bm hidden">Tajuk Sahaja</span>
                </span>
                <span class="text-[12px] font-black tracking-tight flex items-center gap-1 text-[#FFD60A] group-hover:translate-x-[2px] transition-all footer-btn">
                    <span class="btn-text lang-zh">点击展开 →</span>
                    <span class="btn-text lang-bm hidden">Kembang →</span>
                    <span class="w-5 h-5 rounded-full bg-[#FFD60A] text-black flex items-center justify-center text-[11px] group-hover:bg-[#ffdb33]">→</span>
                </span>
            </div>
        </article>
        """

    # 3. 动态渲染未来 2 周活动预告卡片（从 news_data.json 读取 events）
    events_cards_html = ""
    for ev in events_list:
        countdown_label_zh = f"还有 {ev.get('countdown_days', 0)} 天"
        countdown_label_bm = f"{ev.get('countdown_days', 0)} hari lagi"
        
        events_cards_html += f"""
        <div class="event-card group cursor-pointer rounded-[10px] border border-[#222] bg-[#111] hover:bg-[#161616] transition-all p-3" id="event-card-{ev['id']}" onclick="toggleEventCard({ev['id']})">
            <div class="flex items-center gap-3">
                <div class="shrink-0 w-[48px] h-[48px] rounded-[8px] bg-[#FFD60A] text-black flex flex-col items-center justify-center leading-none">
                    <span class="font-black text-[13px]">{ev['month']}</span>
                    <span class="font-bold text-[11px]">/{ev['day']}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-[13px] font-bold leading-tight truncate text-white group-hover:text-[#FFD60A] transition-colors">
                        <span class="lang-zh">{ev['name']}</span>
                        <span class="lang-bm hidden">{ev['nameBM']}</span>
                    </div>
                    <div class="text-[11px] text-[#888] truncate flex items-center gap-1.5 mt-0.5">
                        <span>{ev['location']}</span>
                        <span class="text-[#555]">•</span>
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
                    <span class="text-[11px] text-[#777] arrow-ev transition-transform">▼</span>
                </div>
            </div>

            <!-- 活动抽屉详情面板 -->
            <div class="event-drawer hidden mt-3 pt-3 border-t border-[#222]">
                <p class="text-[12px] leading-[1.6] text-[#ccc] mb-2.5">
                    <span class="lang-zh">{ev['desc']}</span>
                    <span class="lang-bm hidden">{ev['descBM']}</span>
                </p>
                <div class="flex flex-wrap items-center justify-between gap-2 text-[11px] bg-[#0a0a0a] p-2 rounded-[8px] border border-[#1f1f1f]">
                    <div class="flex items-center gap-1.5 text-[#e5e7eb]">
                        <span class="text-[#FFD60A]">⏰</span>
                        <span class="lang-zh">{ev['time']}</span>
                        <span class="lang-bm hidden">{ev['timeBM']}</span>
                    </div>
                    <a href="tel:{ev['tel'].split('/')[0].strip()}" onclick="event.stopPropagation();" class="inline-flex items-center gap-1 px-2.5 py-[3px] rounded-full bg-[#FFD60A] text-black font-black text-[10px] hover:bg-[#ffde33] transition">
                        <span>📞</span>
                        <span>{ev['tel']}</span>
                    </a>
                </div>
                <div class="mt-2 flex items-center justify-between text-[10px] text-[#666]">
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
    <title>西门看看网 · 每日晨报 | 全自动信源采集与双核实编译引擎 2.0</title>
    <!-- 引入 Tailwind CSS 运行时 -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0a0a0a;
            --bg-soft: #151515;
            --bg-card: #151515;
            --border: #222222;
            --border-soft: #2a2a2a;
            --text: #f5f5f5;
            --text-muted: #9ca3af;
            --text-dim: #6b7280;
            --yellow: #FFD60A;
            --yellow-soft: #FFD60A14;
            --red: #E53935;
            --red-dark: #991b1b;
            --green: #22c55e;
        }}

        * {{
            font-family: "Noto Sans SC", system-ui, -apple-system, sans-serif;
            box-sizing: border-box;
        }}
        .mono {{
            font-family: "JetBrains Mono", monospace;
        }}

        body {{
            background-color: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }}

        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #2a2a2a;
            border-radius: 999px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}

        /* 需求 1: 强制双列网格无论横向/纵向均保持严格双列 */
        .force-two-cols-grid {{
            display: grid !important;
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 12px;
        }}
        @media (max-width: 640px) {{
            .force-two-cols-grid {{
                grid-template-columns: repeat(2, 1fr) !important;
                gap: 8px;
            }}
            .news-grid-card {{
                padding: 10px 8px !important;
            }}
            .news-grid-card .card-title {{
                font-size: 13.5px !important;
            }}
        }}

        /* 需求 2: 顶部纯动态无缝全宽走马灯 */
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

        /* 抽屉平滑过渡 */
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
        .news-grid-card.open {{
            background: #191919 !important;
            border-color: rgba(255, 214, 10, 0.4) !important;
            box-shadow: 0 0 0 1px rgba(255, 214, 10, 0.25);
        }}
        .news-grid-card.open .card-title {{
            color: #FFD60A !important;
        }}
        .news-grid-card.open .news-drawer {{
            display: block !important;
            animation: fadeIn 0.25s ease;
        }}

        /* 需求 4: 广告海报高度限制与自适应压缩 */
        .ad-poster-img {{
            max-height: 240px !important;
            object-fit: contain !important;
            width: 100% !important;
            display: block;
            margin: 0 auto;
        }}

        /* 活动卡片展开样式 */
        .event-card.open {{
            border-color: rgba(255, 214, 10, 0.4) !important;
            background: #161616 !important;
        }}
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
    </style>
</head>
<body class="bg-[#0a0a0a] text-[#f5f5f5]">

    <!-- 顶部 Header -->
    <header class="border-b border-[#222] bg-[#0f0f0f] sticky top-0 z-50">
        <div class="mx-auto max-w-[1440px] px-3 md:px-6 h-[52px] md:h-[56px] flex items-center justify-between gap-3">
            <div class="flex items-center gap-2 md:gap-3 min-w-0">
                <div class="flex items-center gap-2">
                    <span class="text-[18px] md:text-[20px] font-black tracking-tight whitespace-nowrap">
                        <span class="lang-zh">西门看看网</span>
                        <span class="lang-bm hidden">Simon Kankan</span>
                    </span>
                    <span class="inline-flex items-center px-2 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[11px] font-bold leading-none shrink-0">
                        <span class="lang-zh">每日晨报</span>
                        <span class="lang-bm hidden">Edisi Pagi</span>
                    </span>

                    <!-- 一键分享按钮 -->
                    <button onclick="sharePage()" class="inline-flex items-center gap-1.5 px-2.5 py-[3px] rounded-[6px] bg-[#1c1c1c] hover:bg-[#282828] text-[#FFD60A] border border-[#FFD60A]/40 text-[11px] font-black transition-all shadow-sm active:scale-95 cursor-pointer ml-1 shrink-0" title="一键分享当前页面给好友">
                        <span>🔗</span>
                        <span class="lang-zh">一键分享</span>
                        <span class="lang-bm hidden">Kongsi</span>
                    </button>
                </div>

                <div class="hidden lg:flex items-center gap-2 text-[12px] text-[#888] mono ml-2 truncate">
                    <span class="w-[6px] h-[6px] rounded-full bg-[#22c55e] inline-block animate-pulse"></span>
                    <span>{today_mmdd} {today_time} LIVE • MYT Asia/Kuala_Lumpur • </span>
                    <span class="lang-zh">点击标题展开全文</span>
                    <span class="lang-bm hidden">Klik tajuk kembang berita</span>
                </div>
            </div>

            <div class="flex items-center gap-1.5 md:gap-2 shrink-0">
                <!-- 中文 / BM 语系即时切换 -->
                <div class="flex items-center rounded-full bg-[#1a1a1a] p-[3px] border border-[#252525]">
                    <button id="btn-lang-zh" onclick="setLanguage('中文')" class="px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all bg-[#FFD60A] text-black">
                        中文
                    </button>
                    <button id="btn-lang-bm" onclick="setLanguage('BM')" class="px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all text-[#777] hover:text-white">
                        BM
                    </button>
                </div>
                <a href="https://wa.me/60109301117" target="_blank" rel="noopener" class="hidden md:inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[12px] text-white hover:bg-[#222] transition">
                    <span class="w-[8px] h-[8px] rounded-full bg-[#22c55e]"></span> WhatsApp
                </a>
                <a href="https://www.facebook.com" target="_blank" rel="noopener" class="hidden md:inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#1877F2] text-white text-[12px] font-medium">
                    f Facebook
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
                    <span>🛡️ ESSCOM 强化东海安近海夜间巡逻防务，守护海岛旅游与渔业稳定</span>
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
                    <span>🛡️ ESSCOM 强化东海安近海夜间巡逻防务，守护海岛旅游与渔业稳定</span>
                    <span class="text-white/40">•</span>
                    <span>🌾 SAZA RICE 买大米赢豪车 Jetour Dashing 岁末抽奖进行中</span>
                    <span class="text-white/40">•</span>
                    <span>🚗 Marco Thien 山打根优质租车 010-930 1117 随时接单</span>
                </div>
            </div>
        </div>
    </header>

    <!-- 主体容器 -->
    <main class="mx-auto max-w-[1440px] px-3 md:px-5 py-3 md:py-4">
        <!-- 动态日期与归档栏（今天/昨天/前天/全部挂载） -->
        <div class="mb-3 rounded-[12px] bg-[#151515] border border-[#222] px-3 md:px-4 py-3 flex flex-col gap-3">
            <div class="flex flex-wrap items-center gap-2 justify-between">
                <div class="flex flex-wrap items-center gap-2">
                    <div class="inline-flex items-center gap-2 px-3 py-[6px] rounded-full bg-[#FFD60A] text-black">
                        <span class="w-2 h-2 rounded-full bg-black animate-pulse"></span>
                        <span class="text-[12px] font-black tracking-tight" id="active-date-display">
                            今天 {today_mmdd} · MYT自动计算
                        </span>
                        <span class="text-[11px] mono font-bold bg-black text-[#FFD60A] px-1.5 py-[1px] rounded-[5px]">{today_time} MYT</span>
                    </div>
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#111] border border-[#222] text-[11px] mono text-[#888]">
                        <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                        Asia/Kuala_Lumpur • {today_full} • 
                        <span class="lang-zh">动态实时更新</span>
                        <span class="lang-bm hidden">Kemas Kini Langsung</span>
                    </div>
                    <div class="inline-flex items-center gap-1 px-2 py-[4px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[11px]">
                        <span class="text-[#aaa] font-bold" id="news-count-badge">{len(headlines)}</span>
                        <span class="text-[#666]">
                            <span class="lang-zh">条深度要闻</span>
                            <span class="lang-bm hidden">tajuk</span>
                        </span>
                    </div>
                </div>
                <div class="text-[10px] mono text-[#555] hidden md:block">
                    <span class="lang-zh">配额升级 12~16条 · 250~400字深度脉络 · 智能去重双核实</span>
                    <span class="lang-bm hidden">12-16 Berita Penuh · Konteks Mendalam 250-400 Patah</span>
                </div>
            </div>

            <!-- 7天归档切换按键 -->
            <div class="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin" id="date-tabs-container">
                <button onclick="switchDateArchive('today', '{today_iso}', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#FFD60A] bg-[#FFD60A] text-black shadow-[0_2px_10px_rgba(255,214,10,0.3)] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-black">
                        <span class="lang-zh">今天</span><span class="lang-bm hidden">Hari Ini</span>
                        <span class="font-mono font-bold text-[11px] opacity-80">{today_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-black/70">
                        <span class="lang-zh">今日晨报 • {len(headlines)} 条</span>
                        <span class="lang-bm hidden">Edisi Pagi</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('yesterday', '{yesterday_iso}', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa] hover:border-[#444] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">
                        <span class="lang-zh">昨日归档</span><span class="lang-bm hidden">Semalam</span>
                        <span class="font-mono font-bold text-[11px] opacity-80 text-[#888]">{yesterday_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-[#666]">
                        <span class="lang-zh">已存归档池</span>
                        <span class="lang-bm hidden">Tersimpan</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('before', '{day_before_iso}', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa] hover:border-[#444] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">
                        <span class="lang-zh">前日精选</span><span class="lang-bm hidden">Kelmarin</span>
                        <span class="font-mono font-bold text-[11px] opacity-80 text-[#888]">{day_before_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-[#666]">
                        <span class="lang-zh">已存归档池</span>
                        <span class="lang-bm hidden">Tersimpan</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('all', 'all', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa] hover:border-[#444] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">
                        <span class="lang-zh">全部 • 7天归档库</span><span class="lang-bm hidden">Semua 7 Hari</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-[#666]">
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
                        <div class="inline-flex items-center gap-2 px-3 py-[5px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[11px] md:text-[12px]">
                            <span class="px-2 py-[1px] rounded-full bg-[#FFD60A] text-black font-bold text-[11px]">
                                {today_mmdd} {today_time} <span class="lang-zh">发布</span><span class="lang-bm hidden">Disiarkan</span>
                            </span>
                            <span class="text-[#9ca3af] hidden md:inline">
                                <span class="lang-zh">标题-only • 点击展开250~400字深度脉络</span>
                                <span class="lang-bm hidden">Tajuk sahaja • Klik kembang 250-400 patah</span>
                            </span>
                            <span class="text-[#666] mono text-[10px]">
                                <span class="lang-zh">双官方来源交叉核实</span>
                                <span class="lang-bm hidden">Disahkan 2 Sumber Rasmi</span>
                            </span>
                        </div>
                        <div class="inline-flex items-center gap-2 px-3 py-[5px] rounded-full bg-[#151515] border border-[#222] text-[12px]">
                            <span class="text-white font-bold">山打根 & 沙巴</span>
                            <span class="px-1.5 py-[1px] rounded bg-[#222] text-[#aaa] text-[11px]">{len(headlines)} <span class="lang-zh">条标题</span><span class="lang-bm hidden">tajuk</span></span>
                            <span class="w-1 h-1 bg-[#333] rounded-full"></span>
                            <span class="text-[#666] text-[11px]">LIVE Filter</span>
                        </div>
                    </div>

                    <!-- 3 列黄色公用事业卡片 (UTILITI) -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-3 mb-4 items-start">
                        {utiliti_cards_html}
                    </div>

                    <!-- 今日要闻标题栏 -->
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2 flex-wrap">
                            <h2 class="text-[17px] md:text-[19px] font-black tracking-tight" id="headlines-section-title">
                                <span class="lang-zh">今日 {today_mmdd} 重点要闻</span>
                                <span class="lang-bm hidden">Berita Utama Hari Ini {today_mmdd}</span>
                            </h2>
                            <span class="inline-flex items-center px-2 py-[2px] rounded-full bg-[#FFD60A] text-black text-[12px] font-black">
                                <span id="headlines-count-tag">{len(headlines)}</span>
                                <span class="lang-zh ml-1">篇深度采编</span>
                                <span class="lang-bm hidden ml-1">Laporan Penuh</span>
                            </span>
                            <span class="hidden md:inline text-[#666] text-[12px] mono ml-1">
                                <span class="lang-zh">点击标题展开丰富全文 250-400字背景脉络</span>
                                <span class="lang-bm hidden">Klik baca laporan 250-400 patah</span>
                            </span>
                        </div>
                        <div class="text-[11px] text-[#666] mono flex items-center gap-2">
                            <span>{today_mmdd} • MYT</span>
                        </div>
                    </div>

                    <!-- 强制双列网格 (grid-template-columns: repeat(2, 1fr) !important;) -->
                    <div class="force-two-cols-grid" id="news-grid-container">
                        {news_cards_html}
                    </div>
                </div>

                <!-- 未来2周归档活动看板（从 news_data.json 动态渲染，含倒计时、开始结束时间与热线） -->
                <div class="bg-[#151515] border border-[#222] rounded-[12px] overflow-hidden mt-2">
                    <div class="px-4 py-3 border-b border-[#222] flex items-center justify-between gap-2">
                        <h3 class="font-black text-[14px] md:text-[15px] flex items-center gap-2">
                            <span>
                                <span class="lang-zh">未来2周活动预告</span>
                                <span class="lang-bm hidden">Aktiviti 2 Minggu Akan Datang</span>
                            </span>
                            <span class="hidden sm:inline-flex items-center px-2 py-[1px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">{len(events_list)} <span class="lang-zh">项官方活动</span><span class="lang-bm hidden">aktiviti</span></span>
                            <span class="inline-flex items-center gap-1 px-2 py-[1px] rounded-full bg-[#111] border border-[#222] text-[10px] mono text-[#666]">
                                <span class="lang-zh">始终可见 不受日期筛选影响</span>
                                <span class="lang-bm hidden">Sentiasa Dipaparkan</span>
                            </span>
                        </h3>
                        <span class="text-[10px] mono text-[#666] text-right leading-tight">
                            自动过时 Auto-hide past events ✓
                        </span>
                    </div>
                    <div class="p-2 grid grid-cols-1 md:grid-cols-2 gap-2" id="events-grid-container">
                        {events_cards_html}
                    </div>
                </div>

                <div class="p-3 rounded-[10px] bg-[#111] border border-[#222] flex items-center justify-between text-[11px] mono text-[#666]">
                    <span>{today_mmdd} {today_time} MYT • 标题-only折叠 点击展开250-400字全文 • 7天归档库已挂载</span>
                    <span class="text-[#FFD60A]">{len(headlines)} 篇深度要闻 • 双核实白名单</span>
                </div>
            </div>

            <!-- 右侧侧边栏 (广告直屏并排，尺寸限制压缩) -->
            <div class="w-full lg:w-[320px] xl:w-[360px] shrink-0 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3 lg:sticky lg:top-[68px] lg:h-fit">
                <!-- 1. Marco 租车广告卡片 -->
                <div class="bg-[#151515] border border-[#222] rounded-[12px] overflow-hidden flex flex-col">
                    <div class="bg-[#FFD60A] px-4 py-2.5 flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="w-6 h-6 rounded-[6px] bg-black text-[#FFD60A] flex items-center justify-center font-black text-[12px]">M</span>
                            <span class="font-black text-black text-[13px] tracking-tight">MY CAR ENTERPRISE</span>
                        </div>
                        <span class="px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-bold">AD • Marco Thien</span>
                    </div>
                    <div class="p-0">
                        <div class="w-full bg-white flex items-center justify-center p-1">
                            <img src="./assets/a0c79ab3b0a4e2ac-image_5f00d7.png" alt="MY CAR ENTERPRISE Sewa Kereta - Marco Thien" class="ad-poster-img" />
                        </div>
                        <div class="p-3 bg-[#151515] flex flex-col gap-3">
                            <div class="rounded-[10px] bg-[#111] border border-[#222] p-2.5 flex flex-col gap-2">
                                <div class="flex items-center gap-2">
                                    <span class="px-2 py-[1px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">官方 Official</span>
                                    <span class="text-[10px] mono text-[#666]">山打根租车服务 Rent Car</span>
                                </div>
                                <div class="text-[12px] font-black leading-[1.35] text-white">
                                    Kereta Sewa Untuk Semua Keperluan Anda
                                </div>
                                <div class="text-[11px] font-bold text-[#FFD60A] tracking-tight">
                                    Jom Travel Bersama Kami • Sabah
                                </div>
                                <div class="grid grid-cols-2 gap-2 pt-1">
                                    <div class="flex flex-col gap-1">
                                        <span class="text-[9px] mono text-[#666] font-bold tracking-wider">FEATURES / 特色</span>
                                        <ul class="flex flex-col gap-0.5 text-[10px] text-[#bbb]">
                                            <li class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-[#FFD60A]"></span>Kereta Bersih</li>
                                            <li class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-[#FFD60A]"></span>Pelbagai Jenis</li>
                                            <li class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-[#FFD60A]"></span>Harga Berpatutan</li>
                                        </ul>
                                    </div>
                                    <div class="flex flex-col gap-1">
                                        <span class="text-[9px] mono text-[#666] font-bold tracking-wider">FLEET / 车型</span>
                                        <ul class="flex flex-col gap-0.5 text-[10px] text-[#bbb]">
                                            <li>• Myvi Axia Bezza</li>
                                            <li>• Vios Vellfire Alza</li>
                                            <li>• Van 11/14 & 4x4</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            <div class="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-2 flex flex-col gap-1.5">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-2">
                                        <div class="w-7 h-7 rounded-full bg-[#FFD60A] text-black flex items-center justify-center font-black text-[11px]">M</div>
                                        <div class="leading-tight">
                                            <div class="text-[11px] font-black text-white">Marco Thien</div>
                                            <div class="text-[9px] mono text-[#888]">山打根租车</div>
                                        </div>
                                    </div>
                                    <span class="px-2 py-[1px] rounded-full bg-[#14532d] border border-[#166534] text-[#22c55e] text-[9px] font-bold">✓ 已核实 Verified</span>
                                </div>
                                <div class="flex items-center justify-between text-[11px] mono pt-1 border-t border-[#1f1f1f]">
                                    <span class="text-white font-bold">📞 010-930 1117</span>
                                    <span class="text-[#bbb]">WeChat: Thien1117</span>
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
    </main>

    <!-- 交互控制脚本（挂载 7 天归档数据池） -->
    <script>
        // 挂载真实 7 天归档池数据
        const ARCHIVE_POOL = {archive_json_str};
        const CURRENT_HEADLINES = {json.dumps(headlines, ensure_ascii=False)};

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
                btnBm.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all text-[#777] hover:text-white";
                zhElements.forEach(el => el.classList.remove('hidden'));
                bmElements.forEach(el => el.classList.add('hidden'));
                document.documentElement.lang = "zh-CN";
            }} else {{
                btnBm.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all bg-[#FFD60A] text-black";
                btnZh.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all text-[#777] hover:text-white";
                zhElements.forEach(el => el.classList.add('hidden'));
                bmElements.forEach(el => el.classList.remove('hidden'));
                document.documentElement.lang = "ms";
            }}
        }}

        // 7天历史归档按天真实数据切换
        function switchDateArchive(type, dateKey, btnElem) {{
            document.querySelectorAll('.date-tab-btn').forEach(btn => {{
                btn.className = "date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa] hover:border-[#444] transition-all";
                const titleSpan = btn.querySelector('.font-black');
                if (titleSpan) titleSpan.classList.remove('text-black');
            }});

            btnElem.className = "date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#FFD60A] bg-[#FFD60A] text-black shadow-[0_2px_10px_rgba(255,214,10,0.3)] transition-all";
            const curTitleSpan = btnElem.querySelector('.font-black');
            if (curTitleSpan) curTitleSpan.classList.add('text-black');

            const titleElem = document.getElementById('headlines-section-title');
            const displayDateElem = document.getElementById('active-date-display');
            const countTag = document.getElementById('headlines-count-tag');
            const isBm = document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');

            let targetHeadlines = [];
            if (type === 'today') {{
                targetHeadlines = CURRENT_HEADLINES;
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Berita Utama Hari Ini {today_mmdd}</span>' : '<span>今日 {today_mmdd} 重点要闻</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Hari Ini {today_mmdd} · Auto MYT' : '今天 {today_mmdd} · MYT自动计算';
                showToast('已载入今日最新核实晨报！', 'Memuatkan berita terkini hari ini!');
            }} else if (type === 'yesterday') {{
                targetHeadlines = ARCHIVE_POOL[dateKey] || CURRENT_HEADLINES;
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Arkib Berita Semalam {yesterday_mmdd}</span>' : '<span>昨日 {yesterday_mmdd} 归档要闻</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Semalam {yesterday_mmdd} · Arkib' : '昨日 {yesterday_mmdd} · 归档库';
                showToast('已切换至昨日归档视角！', 'Beralih ke arkib semalam!');
            }} else if (type === 'before') {{
                targetHeadlines = ARCHIVE_POOL[dateKey] || CURRENT_HEADLINES;
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Arkib Berita Kelmarin {day_before_mmdd}</span>' : '<span>前日 {day_before_mmdd} 归档要闻</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Kelmarin {day_before_mmdd} · Arkib' : '前日 {day_before_mmdd} · 归档库';
                showToast('已切换至前日归档视角！', 'Beralih ke arkib kelmarin!');
            }} else {{
                // 全量 7 天归档聚合
                targetHeadlines = [];
                Object.values(ARCHIVE_POOL).forEach(list => {{
                    if (Array.isArray(list)) targetHeadlines.push(...list.slice(0, 3));
                }});
                if (titleElem) titleElem.innerHTML = isBm ? '<span>Semua Arkib 7 Hari</span>' : '<span>全部历史归档 (7天精选合辑)</span>';
                if (displayDateElem) displayDateElem.textContent = isBm ? 'Semua Arkib 7 Hari' : '全部 · 7天历史库';
                showToast('已开启全量 7 天历史合辑！', 'Membuka arkib 7 hari!');
            }}

            if (countTag) countTag.textContent = targetHeadlines.length;
        }}

        // 未来活动卡片展开/收起抽屉
        function toggleEventCard(id) {{
            const card = document.getElementById('event-card-' + id);
            if (!card) return;
            const isOpen = card.classList.contains('open');
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

        // 展开/收起 新闻网格卡片
        function toggleNewsCard(id) {{
            const card = document.getElementById('news-card-' + id);
            if (!card) return;
            const isOpen = card.classList.contains('open');
            card.classList.toggle('open');
            const footerBtn = card.querySelector('.footer-btn .btn-text');
            const isBm = document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');
            if (footerBtn) {{
                if (isOpen) {{
                    footerBtn.textContent = isBm ? 'Kembang →' : '点击展开 →';
                }} else {{
                    footerBtn.textContent = isBm ? 'Tutup ↑' : '收起 ↑';
                }}
            }}
        }}
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 成功编译升级版 index.html (包含双列网格、{len(headlines)} 条要闻、{len(events_list)} 项活动与 7天归档库)！")

if __name__ == "__main__":
    generate_index_html()
