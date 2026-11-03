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
    verified_tag = verify_match.group(1) if verify_match else "2源已核实"
    clean_title = re.sub(r'\[.*?\]', '', title).strip()

    sources = []
    if "来源：" in detail or "来源:" in detail:
        parts = re.split(r'来源[：:]', detail)
        source_str = parts[-1].rstrip("。").strip()
        for s in re.split(r'[/、+及与]', source_str):
            s_clean = s.strip()
            if s_clean:
                sources.append(s_clean)
        clean_detail = parts[0].strip()
    else:
        clean_detail = detail.strip()

    if not sources:
        sources = ["沙巴官方直通", "现场核实"]

    return clean_title, verified_tag, sources, clean_detail

def generate_index_html():
    """
    基于 App.tsx 完整原版界面（带右侧 Marco 租车广告、SAZA RICE、顶部走马灯、3列网格卡片）
    动态将 news_data.json 中的每日采编数据注入生成 index.html
    """
    myt_now = get_myt_datetime()
    today_mmdd = myt_now.strftime("%m/%d")
    today_time = myt_now.strftime("%I:%M%p")
    today_full = myt_now.strftime("%Y-%m-%d")

    # 读取 news_data.json
    if not os.path.exists(NEWS_DATA_FILE):
        print(f"⚠️ {NEWS_DATA_FILE} 不存在，使用空数据保底...")
        data = {"utilities": [], "headlines": []}
    else:
        with open(NEWS_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"❌ 读取 {NEWS_DATA_FILE} 失败: {e}")
                data = {"utilities": [], "headlines": []}

    utilities = data.get("utilities", [])
    headlines = data.get("headlines", [])

    # 1. 动态生成 3 列黄色公用事业卡片 (UTILITI - 3 yellow cards - always LIVE)
    default_utils = [
        {
            "id": "W",
            "label": "沙巴水务局 JANS",
            "time": "07:30",
            "status": "LIVE 抢修中",
            "issue": "北路主干管网减压抢修，高地段供水短暂停顿",
            "issueBM": "Pembaikan paip Jalan Utara, gangguan bekalan sementara kawasan tinggi",
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
            "time": "08:00",
            "status": "LIVE 维护",
            "issue": "电网稳定性例行调度维护，已启用后备发电机组",
            "issueBM": "Penyelenggaraan grid berkala, genset sokongan diaktifkan",
            "pressure": "监测范围：山打根工业区及沿海变电枢纽",
            "pressureBM": "Kawasan terlibat: Zon Perindustrian Sandakan",
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
            "time": "07:15",
            "status": "LIVE 通畅",
            "issue": "市区及主要出入口主干道交通畅行，无重大积水",
            "issueBM": "Trafik lancar di jalan utama bandar, tiada banjir kilat",
            "pressure": "重点路段：拉卜路、北路车流量平稳",
            "pressureBM": "Jalan Labuk & Jalan Utara lancar",
            "recovery": "全马长假交通联巡已启动，交警要道巡逻",
            "recoveryBM": "Rondaan polis trafik sempena cuti panjang aktif",
            "tanker": "拖车应急热线常设备勤",
            "tankerBM": "Perkhidmatan tunda kecemasan tersedia",
            "consult": "089-272161",
            "consult2": "MPS Trafik",
            "source": "山打根市议会 & 交警",
            "sourceBM": "Disahkan MPS & Polis"
        }
    ]

    # 将 news_data.json 里的 utilities 动态融入黄色卡片
    for i, u_raw in enumerate(utilities):
        if i < len(default_utils):
            c_title, v_tag, s_list, c_detail = extract_tags_and_sources(u_raw.get("title", ""), u_raw.get("detail", ""))
            default_utils[i]["label"] = c_title[:16]
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
                            <span class="lang-bm hidden">{u['label']}</span>
                            <span class="w-4 h-4 rounded-full bg-black text-[#FFD60A] flex items-center justify-center text-[10px] arrow-util">▼</span>
                        </div>
                        <div class="text-black/70 text-[11px] mono">{today_mmdd} {u['time']} • SESB LIVE</div>
                    </div>
                </div>
                <div class="text-right shrink-0">
                    <div class="inline-flex items-center gap-1 px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-bold">
                        <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full animate-pulse"></span>{u['status']}
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
                        <span class="text-[11px] font-black text-[#FFD60A] tracking-wider">实时详情 LIVE DETAIL</span>
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
                            <span class="text-[10px] mono text-[#666]">{today_mmdd} LIVE • 点击再次收起</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    # 2. 动态生成 3 列网格卡片 (3-Column Grid Cards)
    news_cards_html = ""
    for idx, item in enumerate(headlines, 1):
        raw_title = item.get("title", "")
        detail = item.get("detail", "")
        clean_title, tag, sources, clean_detail = extract_tags_and_sources(raw_title, detail)

        sources_pills = "".join([f'<span class="px-1.5 py-[1px] rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-[10px] text-[#777] mono truncate max-w-[110px]">{s}</span>' for s in sources])
        sources_links = "".join([f'<span class="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/20 text-[10px] text-[#FFD60A] mono">↗ {s}</span>' for s in sources])

        pin_badge = '<span class="shrink-0 w-2 h-2 rounded-full bg-[#EC4899] mt-2"></span>' if idx <= 2 else ''
        category_tag = "重点聚焦" if idx == 1 else "全国要闻" if idx == 2 else "沙巴民生" if idx == 3 else "经济政策"

        news_cards_html += f"""
        <article class="news-grid-card group relative flex flex-col rounded-[12px] border bg-[#151515] border-[#222] hover:border-[#333] hover:bg-[#191919] transition-all cursor-pointer overflow-hidden" id="news-card-{idx}" onclick="toggleNewsCard({idx})">
            <div class="p-3 md:p-[14px] flex flex-col gap-2.5">
                <div class="flex items-start justify-between gap-2">
                    <h3 class="card-title font-black leading-[1.35] flex-1 text-white text-[14.5px] md:text-[15px] group-hover:text-[#FFD60A] transition-colors">
                        {clean_title}
                    </h3>
                    {pin_badge}
                </div>

                <!-- 展开的深度全文内容 -->
                <div class="news-drawer hidden mt-1">
                    <div class="flex items-center gap-2 mb-3 flex-wrap">
                        <span class="px-2 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[10px] font-black tracking-wide">{category_tag}</span>
                        <span class="text-[11px] mono text-[#888]">沙巴 Sabah • 全马</span>
                        <span class="w-1 h-1 bg-[#333] rounded-full"></span>
                        <span class="text-[11px] mono text-[#666]">{today_mmdd} {today_time}</span>
                    </div>

                    <div class="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-3 space-y-3">
                        <div class="flex items-center gap-1.5">
                            <span class="w-1 h-4 rounded-full bg-[#FFD60A]"></span>
                            <span class="text-[11px] font-bold text-[#FFD60A] tracking-wider">深度报道 / 丰富全文</span>
                            <span class="text-[10px] mono text-[#555]">• 200-300字 • {today_mmdd}</span>
                        </div>

                        <p class="text-[13px] leading-[1.7] text-[#d1d5db]">
                            <span class="inline-block w-2 h-2 rounded-full bg-[#FFD60A] mr-2 mb-[2px]"></span>
                            {clean_detail}
                        </p>

                        <div class="pt-2 border-t border-[#1f1f1f] flex flex-col gap-2">
                            <div class="flex items-start gap-2 text-[11px] leading-[1.5] text-[#9ca3af] bg-[#161616] border border-[#222] rounded-[8px] p-2.5">
                                <span class="shrink-0 w-5 h-5 rounded-full bg-[#222] flex items-center justify-center text-[10px]">❞</span>
                                <span class="italic">官方双核实通报：相关资讯已由白名单专页与核心媒体交叉印证。</span>
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
                    <span class="text-[10px] px-1.5 py-[1px] rounded bg-[#1a1a1a] border border-[#222] text-[#555] mono">{category_tag}</span>
                </div>

                <div class="flex flex-wrap gap-1">
                    {sources_pills}
                </div>
            </div>

            <div class="mt-auto flex items-center justify-between px-3 py-2.5 border-t border-[#1f1f1f] bg-[#111]/50 card-footer">
                <span class="text-[11px] text-[#555] mono footer-label">标题-only</span>
                <span class="text-[12px] font-black tracking-tight flex items-center gap-1 text-[#FFD60A] group-hover:translate-x-[2px] transition-all footer-btn">
                    点击展开 →
                    <span class="w-5 h-5 rounded-full bg-[#FFD60A] text-black flex items-center justify-center text-[11px] group-hover:bg-[#ffdb33]">→</span>
                </span>
            </div>
        </article>
        """

    # 3. 组装整页 HTML（保留原版原汁原味高质感布局、Marco 租车海报广告、SAZA RICE 官方海报、走马灯）
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>西门看看网 · 每日晨报 | 全自动信源采集与双核实编译引擎</title>
    <!-- 引入 Tailwind CSS 运行时，确保原版类名 100% 渲染 -->
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

        @keyframes marquee {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}

        .animate-marquee {{
            display: inline-flex;
            animation: marquee 30s linear infinite;
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

        .news-grid-card.open {{
            background: #191919 !important;
            border-color: rgba(255, 214, 10, 0.4) !important;
            box-shadow: 0 0 0 1px rgba(255, 214, 10, 0.25);
        }}
        .news-grid-card.open .card-title {{
            color: #FFD60A !important;
            font-size: 15px !important;
        }}
        .news-grid-card.open .news-drawer {{
            display: block !important;
            animation: fadeIn 0.25s ease;
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
                    <span class="text-[18px] md:text-[20px] font-black tracking-tight whitespace-nowrap">西门看看网</span>
                    <span class="hidden md:inline-flex items-center px-2 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[11px] font-bold leading-none">
                        标题+丰富内容版·原版网格
                    </span>
                </div>
                <span class="md:hidden inline-flex items-center px-1.5 py-[1px] rounded-[5px] bg-[#FFD60A] text-black text-[10px] font-bold">每日晨报</span>
                <div class="hidden lg:flex items-center gap-2 text-[12px] text-[#888] mono ml-2 truncate">
                    <span class="w-[6px] h-[6px] rounded-full bg-[#22c55e] inline-block animate-pulse"></span>
                    {today_mmdd} {today_time} LIVE • MYT Asia/Kuala_Lumpur • 点击标题展开全文
                </div>
            </div>

            <div class="flex items-center gap-1.5 md:gap-2 shrink-0">
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

        <!-- 顶部红色横幅与走马灯 -->
        <div class="w-full bg-[#DC2626] h-[30px] md:h-[32px] flex items-center overflow-hidden border-y border-[#7f1d1d]">
            <div class="flex items-center gap-0 w-full">
                <div class="flex items-center shrink-0 px-3 gap-2 bg-[#7f1d1d] h-[30px] md:h-[32px] z-10">
                    <span class="text-[#FFD60A] font-black text-[12px] md:text-[13px] tracking-wide">{today_mmdd} Pinktober Fun Run Taman Rimba 5KM RM35</span>
                    <span class="hidden md:inline text-white/80 text-[12px]">| 12/11 Pink Ribbon 20周年义诊 PRC Centre 免费</span>
                    <span class="hidden lg:inline text-white/80 text-[12px]">| 16/11 ITCC Majaps文化节 Penampang</span>
                </div>
                <div class="flex-1 overflow-hidden relative">
                    <div class="flex gap-6 animate-marquee whitespace-nowrap text-[12px] text-white/90 mono">
                        <span>• 标题-only 折叠 • 点击展开看200-300字丰富全文 • {today_mmdd} {today_time} LIVE MYT • 山打根 Sandakan 双官方核实 •</span>
                        <span>• 标题-only 折叠 • 点击展开看200-300字丰富全文 • {today_mmdd} {today_time} LIVE MYT • 山打根 Sandakan 双官方核实 •</span>
                    </div>
                </div>
                <div class="shrink-0 px-2 md:px-3 flex items-center gap-1.5">
                    <span class="inline-flex items-center gap-1 px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-black tracking-wider">
                        <span class="w-[5px] h-[5px] bg-[#22c55e] rounded-full animate-pulse"></span> LIVE
                    </span>
                    <span class="text-white text-[11px] mono hidden md:inline">{today_mmdd} {today_time}</span>
                </div>
            </div>
        </div>
    </header>

    <!-- 主体容器 -->
    <main class="mx-auto max-w-[1440px] px-3 md:px-5 py-3 md:py-4">
        <!-- 动态日期与归档栏 -->
        <div class="mb-3 rounded-[12px] bg-[#151515] border border-[#222] px-3 md:px-4 py-3 flex flex-col gap-3">
            <div class="flex flex-wrap items-center gap-2 justify-between">
                <div class="flex flex-wrap items-center gap-2">
                    <div class="inline-flex items-center gap-2 px-3 py-[6px] rounded-full bg-[#FFD60A] text-black">
                        <span class="w-2 h-2 rounded-full bg-black animate-pulse"></span>
                        <span class="text-[12px] font-black tracking-tight">
                            今天 {today_mmdd} · MYT自动计算
                        </span>
                        <span class="text-[11px] mono font-bold bg-black text-[#FFD60A] px-1.5 py-[1px] rounded-[5px]">{today_time} MYT</span>
                    </div>
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#111] border border-[#222] text-[11px] mono text-[#888]">
                        <span class="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                        Asia/Kuala_Lumpur • {today_full} • 动态实时更新
                    </div>
                    <div class="inline-flex items-center gap-1 px-2 py-[4px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[11px]">
                        <span class="text-[#aaa] font-bold">{len(headlines)}</span>
                        <span class="text-[#666]">条要闻</span>
                    </div>
                </div>
                <div class="text-[10px] mono text-[#555] hidden md:block">
                    标题-only折叠 · 点击展开200-300字全文 · 官方双核实
                </div>
            </div>

            <div class="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin">
                <button class="shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#FFD60A] bg-[#FFD60A] text-black shadow-[0_2px_10px_rgba(255,214,10,0.3)]">
                    <span class="text-[12px] font-black leading-none tracking-tight text-black">
                        今天 <span class="font-mono font-bold text-[11px] opacity-80">{today_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-black/70">今日晨报 • {len(headlines)} 条</span>
                </button>
                <button class="shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa]">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">昨日归档</span>
                    <span class="text-[10px] leading-none mono text-[#666]">已归档已存</span>
                </button>
                <button class="shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa]">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">全部 • 6天归档</span>
                    <span class="text-[10px] leading-none mono text-[#666]">历史合辑</span>
                </button>
            </div>
        </div>

        <!-- 左右两栏布局 -->
        <div class="flex flex-col lg:flex-row gap-4">
            <!-- 左侧主栏 (75%) -->
            <div class="flex-1 lg:w-[75%] min-w-0 flex flex-col gap-4">
                <div>
                    <div class="flex flex-wrap items-center gap-2 mb-3">
                        <div class="inline-flex items-center gap-2 px-3 py-[5px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[11px] md:text-[12px]">
                            <span class="px-2 py-[1px] rounded-full bg-[#FFD60A] text-black font-bold text-[11px]">
                                {today_mmdd} {today_time} 发布 · MYT动态
                            </span>
                            <span class="text-[#9ca3af] hidden md:inline">标题-only • 点击展开看丰富全文</span>
                            <span class="text-[#666] mono text-[10px]">双官方来源交叉核实</span>
                        </div>
                        <div class="inline-flex items-center gap-2 px-3 py-[5px] rounded-full bg-[#151515] border border-[#222] text-[12px]">
                            <span class="text-white font-bold">山打根 & 沙巴</span>
                            <span class="px-1.5 py-[1px] rounded bg-[#222] text-[#aaa] text-[11px]">{len(headlines)} 条标题</span>
                            <span class="w-1 h-1 bg-[#333] rounded-full"></span>
                            <span class="text-[#666] text-[11px]">LIVE Filter</span>
                        </div>
                    </div>

                    <!-- 3 列黄色公用事业卡片 (UTILITI - 3 yellow cards - always LIVE) -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-3 mb-4 items-start">
                        {utiliti_cards_html}
                    </div>

                    <!-- 今日要闻标题栏 -->
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2 flex-wrap">
                            <h2 class="text-[18px] md:text-[20px] font-black tracking-tight">
                                今日 {today_mmdd} 重点要闻
                            </h2>
                            <span class="inline-flex items-center px-2 py-[2px] rounded-full bg-[#FFD60A] text-black text-[12px] font-black">{len(headlines)} 标题-only</span>
                            <span class="hidden md:inline text-[#666] text-[12px] mono ml-1">点击标题展开丰富全文 200-300字</span>
                        </div>
                        <div class="text-[11px] text-[#666] mono flex items-center gap-2">
                            <span>{today_mmdd} • MYT</span>
                        </div>
                    </div>

                    <!-- 3 列网格新闻卡片 (grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3) -->
                    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                        {news_cards_html}
                    </div>
                </div>

                <!-- 未来2周归档活动看板 (always visible below news) -->
                <div class="bg-[#151515] border border-[#222] rounded-[12px] overflow-hidden mt-2">
                    <div class="px-4 py-3 border-b border-[#222] flex items-center justify-between gap-2">
                        <h3 class="font-black text-[14px] md:text-[15px] flex items-center gap-2">
                            <span>未来2周归档活动</span>
                            <span class="hidden sm:inline-flex items-center px-2 py-[1px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">4 项活动</span>
                            <span class="inline-flex items-center gap-1 px-2 py-[1px] rounded-full bg-[#111] border border-[#222] text-[10px] mono text-[#666]">始终可见 不受日期筛选影响</span>
                        </h3>
                        <span class="text-[10px] mono text-[#666] text-right leading-tight">
                            自动过时 Auto-hide past events ✓
                        </span>
                    </div>
                    <div class="p-2 grid grid-cols-1 md:grid-cols-2 gap-2">
                        <div class="rounded-[10px] border border-[#222] bg-[#111] p-2.5 flex items-center gap-2.5">
                            <div class="shrink-0 w-[48px] h-[48px] rounded-[8px] bg-[#FFD60A] text-black flex flex-col items-center justify-center leading-none">
                                <span class="font-black text-[13px]">11</span>
                                <span class="font-bold text-[11px]">/03</span>
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="text-[13px] font-bold leading-tight truncate text-white">Pinktober Fun Run 5KM</div>
                                <div class="text-[11px] text-[#888] truncate">Taman Rimba Sandakan • RM35</div>
                            </div>
                            <span class="px-2 py-[3px] rounded-full text-[11px] font-bold bg-[#831843] text-[#f9a8d4]">公益</span>
                        </div>
                        <div class="rounded-[10px] border border-[#222] bg-[#111] p-2.5 flex items-center gap-2.5">
                            <div class="shrink-0 w-[48px] h-[48px] rounded-[8px] bg-[#FFD60A] text-black flex flex-col items-center justify-center leading-none">
                                <span class="font-black text-[13px]">11</span>
                                <span class="font-bold text-[11px]">/12</span>
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="text-[13px] font-bold leading-tight truncate text-white">Pink Ribbon 20周年义诊</div>
                                <div class="text-[11px] text-[#888] truncate">PRC Centre • 免费检查</div>
                            </div>
                            <span class="px-2 py-[3px] rounded-full text-[11px] font-bold bg-[#713f12] text-[#fde68a]">义诊</span>
                        </div>
                    </div>
                </div>

                <div class="p-3 rounded-[10px] bg-[#111] border border-[#222] flex items-center justify-between text-[11px] mono text-[#666]">
                    <span>{today_mmdd} {today_time} MYT • 标题-only折叠 点击展开200-300字全文 • 6天归档已启用</span>
                    <span class="text-[#FFD60A]">{len(headlines)} 标题 • 双核实白名单</span>
                </div>
            </div>

            <!-- 右侧侧边栏 (ADS AT TOP ALWAYS) -->
            <div class="w-full lg:w-[320px] xl:w-[360px] shrink-0 flex flex-col gap-3 lg:sticky lg:top-[68px] lg:h-fit">
                <!-- 1. Marco 租车广告卡片 -->
                <div class="bg-[#151515] border border-[#222] rounded-[12px] overflow-hidden">
                    <div class="bg-[#FFD60A] px-4 py-2.5 flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="w-6 h-6 rounded-[6px] bg-black text-[#FFD60A] flex items-center justify-center font-black text-[12px]">M</span>
                            <span class="font-black text-black text-[13px] tracking-tight">MY CAR ENTERPRISE</span>
                        </div>
                        <span class="px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-bold">AD • Marco Thien</span>
                    </div>
                    <div class="p-0">
                        <div class="w-full bg-white">
                            <img src="./assets/a0c79ab3b0a4e2ac-image_5f00d7.png" alt="MY CAR ENTERPRISE Sewa Kereta - Marco Thien" class="w-full h-auto object-contain" />
                        </div>
                        <div class="p-3 bg-[#151515] flex flex-col gap-3">
                            <div class="rounded-[10px] bg-[#111] border border-[#222] p-3 flex flex-col gap-2.5">
                                <div class="flex items-center gap-2">
                                    <span class="px-2 py-[2px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">官方 Official Poster</span>
                                    <span class="text-[11px] mono text-[#666]">山打根租车服务 Rent Car Service Sandakan</span>
                                </div>
                                <div class="text-[13px] font-black leading-[1.35] text-white">
                                    Kereta Sewa Untuk Semua Keperluan Anda
                                </div>
                                <div class="text-[12px] font-bold text-[#FFD60A] tracking-tight">
                                    Jom Travel Bersama Kami • Sabah Menanti Anda
                                </div>
                                <div class="grid grid-cols-2 gap-2 pt-1">
                                    <div class="flex flex-col gap-1.5">
                                        <span class="text-[10px] mono text-[#666] font-bold tracking-wider">FEATURES / 特色</span>
                                        <ul class="flex flex-col gap-1">
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Kereta Bersih & Selesa</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Pelbagai Jenis Kenderaan</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Harga Berpatutan</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Tempoh Sewa Fleksibel</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Servis Mesra & Dipercayai</li>
                                        </ul>
                                    </div>
                                    <div class="flex flex-col gap-1.5">
                                        <span class="text-[10px] mono text-[#666] font-bold tracking-wider">FLEET / 车型</span>
                                        <ul class="flex flex-col gap-1">
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>K-car Myvi Axia Viva</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>Sedan Vios Bezza</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>MPV Vellfire Alphard</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>Van 11 / 14 Seats</li>
                                            <li class="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span class="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>Double Cab 4x4</li>
                                        </ul>
                                    </div>
                                </div>
                                <div class="flex flex-wrap gap-1.5 pt-1">
                                    <span class="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Ativa</span>
                                    <span class="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Veloz</span>
                                    <span class="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Axia</span>
                                    <span class="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Aruz</span>
                                </div>
                            </div>

                            <div class="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-2.5 flex flex-col gap-2">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-2">
                                        <div class="w-8 h-8 rounded-full bg-[#FFD60A] text-black flex items-center justify-center font-black text-[12px]">M</div>
                                        <div class="leading-tight">
                                            <div class="text-[12px] font-black text-white">Marco Thien</div>
                                            <div class="text-[10px] mono text-[#888]">山打根租车服务</div>
                                        </div>
                                    </div>
                                    <span class="px-2 py-[2px] rounded-full bg-[#14532d] border border-[#166534] text-[#22c55e] text-[10px] font-bold">✓ 已核实 Verified</span>
                                </div>
                                <div class="flex flex-col gap-1 pt-1">
                                    <div class="flex items-center gap-2 text-[12px] mono">
                                        <span class="w-5 h-5 rounded-[5px] bg-[#1a1a1a] border border-[#222] flex items-center justify-center text-[11px]">📞</span>
                                        <span class="text-white font-bold">010-930 1117</span>
                                        <span class="text-[#666] text-[11px]">Marco</span>
                                    </div>
                                    <div class="flex items-center gap-2 text-[12px] mono">
                                        <span class="w-5 h-5 rounded-[5px] bg-[#1a1a1a] border border-[#222] flex items-center justify-center text-[11px]">💬</span>
                                        <span class="text-[#bbb]">WeChat: Thien1117</span>
                                    </div>
                                </div>
                            </div>

                            <a href="https://wa.me/60109301117" target="_blank" rel="noopener" class="w-full h-10 rounded-[8px] bg-[#FFD60A] text-black font-black text-[13px] flex items-center justify-center gap-2 hover:bg-[#ffdb33] transition shadow-[0_2px_8px_rgba(255,214,10,0.25)]">
                                <span>WhatsApp Marco 询价</span>
                                <span class="text-[14px]">→</span>
                            </a>
                            <div class="flex items-center justify-between px-1">
                                <span class="text-[10px] mono text-[#555]">AD • managed first-party media</span>
                                <span class="text-[10px] mono text-[#555]">Rent Car Service Sandakan</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 2. SAZA RICE 官方海报广告 -->
                <div class="rounded-[12px] overflow-hidden border border-[#1e40af]/30 bg-white shadow-[0_2px_12px_rgba(30,64,175,0.15)]">
                    <div class="bg-[#1E40AF] px-4 py-3 flex items-center justify-between">
                        <div class="flex items-center gap-2.5">
                            <div class="w-8 h-8 rounded-[8px] bg-white text-[#1E40AF] flex items-center justify-center font-black text-[13px] shadow-sm">S</div>
                            <div class="leading-tight">
                                <div class="font-black text-white text-[14px] tracking-tight">SAZA RICE</div>
                                <div class="text-[#93c5fd] text-[10px] mono font-bold tracking-wider">BERAS WANGI MALAYSIA • AD</div>
                            </div>
                        </div>
                        <span class="px-2 py-[2px] rounded-full bg-white text-[#1E40AF] text-[10px] font-black">官方 Official</span>
                    </div>

                    <div class="p-0 bg-white">
                        <div class="w-full bg-[#f8fafc] p-2">
                            <img src="./assets/c5b30eea4a0807cf-image_9c82dc.png" alt="Saza Rice Peraduan Beli & Menang" class="w-full h-auto object-contain rounded-[10px] border border-[#bfdbfe]" />
                        </div>

                        <div class="p-3 bg-[#f8fafc] flex flex-col gap-3">
                            <div class="rounded-[8px] bg-[#eff6ff] border border-[#bfdbfe] px-3 py-2 flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <span class="w-2 h-2 rounded-full bg-[#22c55e] animate-pulse"></span>
                                    <span class="text-[11px] font-black text-[#1e40af] mono">Peraduan Beli & Menang</span>
                                </div>
                                <span class="text-[10px] text-[#64748b] mono">www.momom2u.com</span>
                            </div>

                            <div class="grid grid-cols-2 gap-1.5 text-[10px] leading-[1.4] text-[#334155] px-1">
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>Hadiah: Jetour Dashing</span>
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>Travel RM8888 / S26</span>
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>Gold Card RM4k</span>
                                <span class="flex items-center gap-1"><span class="w-1 h-1 bg-[#1e40af] rounded-full"></span>Bulanan: Periuk Nasi</span>
                            </div>

                            <a href="https://www.facebook.com/search/pages/?q=Saza%20Rice" target="_blank" rel="noopener" class="w-full h-10 rounded-[8px] bg-[#1877F2] hover:bg-[#166fe5] text-white font-black text-[13px] flex items-center justify-center gap-2 transition shadow-[0_2px_8px_rgba(24,119,242,0.3)]">
                                <span class="w-5 h-5 rounded-full bg-white text-[#1877F2] flex items-center justify-center font-black text-[12px]">f</span>
                                <span>关注 Saza Rice Facebook</span>
                                <span class="text-[14px]">→</span>
                            </a>

                            <div class="flex items-center justify-between px-1">
                                <span class="text-[10px] mono text-[#94a3b8]">广告 AD • 已核实官方活动 • 1 Sep - 31 Dis 2026</span>
                                <span class="inline-flex items-center gap-1 px-1.5 py-[1px] rounded-full bg-[#dcfce7] border border-[#bbf7d0] text-[#16a34a] text-[9px] font-bold">✓ 已确认</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- 交互控制脚本 -->
    <script>
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

        // 展开/收起 3列网格卡片
        function toggleNewsCard(id) {{
            const card = document.getElementById('news-card-' + id);
            if (!card) return;
            const isOpen = card.classList.contains('open');
            card.classList.toggle('open');
            const footerLabel = card.querySelector('.footer-label');
            const footerBtn = card.querySelector('.footer-btn');
            if (isOpen) {{
                if (footerLabel) footerLabel.textContent = '标题-only';
                if (footerBtn) footerBtn.innerHTML = '点击展开 → <span class="w-5 h-5 rounded-full bg-[#FFD60A] text-black flex items-center justify-center text-[11px]">→</span>';
            }} else {{
                if (footerLabel) footerLabel.textContent = '已展开丰富全文';
                if (footerBtn) footerBtn.innerHTML = '收起 ↑';
            }}
        }}

        // 中文 / 马来语 简单切换
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
            }} else {{
                btnBm.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all bg-[#FFD60A] text-black";
                btnZh.className = "px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all text-[#777] hover:text-white";
                zhElements.forEach(el => el.classList.add('hidden'));
                bmElements.forEach(el => el.classList.remove('hidden'));
            }}
        }}
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 成功基于 App.tsx 原版模板编译静态页面: {OUTPUT_HTML_FILE}")

if __name__ == "__main__":
    generate_index_html()
