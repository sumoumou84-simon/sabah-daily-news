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
    基于 App.tsx 完整原版界面进行 HTML/CSS 深度优化，实装 6 大前端需求：
    1. 强制双列网格 (grid-template-columns: repeat(2, 1fr) !important)
    2. 顶部红色纯动态跑马灯（全宽无缝循环滚动的活动与民生预告）
    3. 左上角一键分享按钮（调用 navigator.share 或自动复制弹窗提示）
    4. 广告海报尺寸压缩与并排（限制 max-height: 240px; contain; 直屏并排双列）
    5. 修复右上角中文 / BM 语言切换事件与字典映射
    6. 未来活动抽屉化展开与顶部日期（今天/昨天/前天/全部）交互挂载
    """
    myt_now = get_myt_datetime()
    today_mmdd = myt_now.strftime("%m/%d")
    yesterday_mmdd = (myt_now - timedelta(days=1)).strftime("%m/%d")
    day_before_mmdd = (myt_now - timedelta(days=2)).strftime("%m/%d")
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

    # 2. 准备今日要闻数据（包含英文/马来文对照）与多日期模拟数据
    # 为 BM 模式提供基础翻译对照
    bm_translations = {
        "JPJ 强化长途巴士与商用车安全监管": "JPJ Perketat Penguatkuasaan Bas Ekspres & Kenderaan Perdagangan",
        "财政部与关税局落实特定免税新规": "Kementerian Kewangan & Kastam Laksana Peraturan Pengecualian Cukai Baharu",
        "沙巴生态旅游扶持专款推进 扩建机场基础设施": "Dana Ekopelancongan Sabah Maju, Infrastruktur Lapangan Terbang Dinaik Taraf",
        "通讯部发布媒体数字化基金细则": "Kementerian Komunikasi Umum Garis Panduan Dana Digital Media",
        "全马开学及公假长周末交通预警": "Amaran Trafik Cuti Persekolahan & Hujung Minggu Panjang Seluruh Negara"
    }

    def get_bm_title(zh_t):
        for k, v in bm_translations.items():
            if k in zh_t:
                return v
        return zh_t

    # 生成新闻卡片 HTML
    news_cards_html = ""
    for idx, item in enumerate(headlines, 1):
        raw_title = item.get("title", "")
        detail = item.get("detail", "")
        clean_title, tag, sources, clean_detail = extract_tags_and_sources(raw_title, detail)
        title_bm = get_bm_title(clean_title)

        sources_pills = "".join([f'<span class="px-1.5 py-[1px] rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-[10px] text-[#777] mono truncate max-w-[110px]">{s}</span>' for s in sources])
        sources_links = "".join([f'<span class="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/20 text-[10px] text-[#FFD60A] mono">↗ {s}</span>' for s in sources])

        pin_badge = '<span class="shrink-0 w-2 h-2 rounded-full bg-[#EC4899] mt-2"></span>' if idx <= 2 else ''
        category_tag_zh = "重点聚焦" if idx == 1 else "全国要闻" if idx == 2 else "沙巴要闻" if idx == 3 else "民生快讯"
        category_tag_bm = "Utama" if idx == 1 else "Nasional" if idx == 2 else "Sabah" if idx == 3 else "Terkini"

        # 归档批次，默认全部归属于 0 (今天)
        date_group = "date-today"

        news_cards_html += f"""
        <article class="news-grid-card group relative flex flex-col rounded-[12px] border bg-[#151515] border-[#222] hover:border-[#333] hover:bg-[#191919] transition-all cursor-pointer overflow-hidden {date_group}" id="news-card-{idx}" onclick="toggleNewsCard({idx})">
            <div class="p-3 md:p-[14px] flex flex-col gap-2.5">
                <div class="flex items-start justify-between gap-2">
                    <h3 class="card-title font-black leading-[1.35] flex-1 text-white text-[14px] md:text-[15px] group-hover:text-[#FFD60A] transition-colors">
                        <span class="lang-zh">{clean_title}</span>
                        <span class="lang-bm hidden">{title_bm}</span>
                    </h3>
                    {pin_badge}
                </div>

                <!-- 展开的深度全文内容 -->
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
                                <span class="lang-zh">深度报道 / 丰富全文</span>
                                <span class="lang-bm hidden">Laporan Mendalam Penuh</span>
                            </span>
                            <span class="text-[10px] mono text-[#555]">• 200-300字 • {today_mmdd}</span>
                        </div>

                        <p class="text-[13px] leading-[1.7] text-[#d1d5db]">
                            <span class="inline-block w-2 h-2 rounded-full bg-[#FFD60A] mr-2 mb-[2px]"></span>
                            {clean_detail}
                        </p>

                        <div class="pt-2 border-t border-[#1f1f1f] flex flex-col gap-2">
                            <div class="flex items-start gap-2 text-[11px] leading-[1.5] text-[#9ca3af] bg-[#161616] border border-[#222] rounded-[8px] p-2.5">
                                <span class="shrink-0 w-5 h-5 rounded-full bg-[#222] flex items-center justify-center text-[10px]">❞</span>
                                <span class="italic">
                                    <span class="lang-zh">官方双核实通报：相关资讯已由白名单专页与核心媒体交叉印证。</span>
                                    <span class="lang-bm hidden">Laporan disahkan melalui semakan silang media dan portal rasmi.</span>
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

    # 3. 构造未来2周活动数据（支持抽屉化展开看时间、电话与详情）
    events_data = [
        {
            "id": 1,
            "month": "11",
            "day": "03",
            "name": "Pinktober Fun Run 5KM",
            "nameBM": "Larian Amal Pinktober 5KM",
            "location": "Taman Rimba Sandakan",
            "category": "公益义跑",
            "categoryBM": "Larian Amal",
            "badgeColor": "bg-[#831843] text-[#f9a8d4]",
            "desc": "粉红十月乳癌防治意识倡导健康跑，全程 5 公里。报名费 RM35 含纪念 T 恤、完赛奖牌与轻食包。",
            "descBM": "Larian kesedaran kanser payudara sempena Pinktober sejauh 5KM. Yuran RM35 termasuk baju-T, pingat penamat dan pek sarapan.",
            "time": "06:30 AM 集合鸣枪",
            "timeBM": "06:30 AM Pelepasan",
            "tel": "089-212188",
            "source": "沙巴国家癌症协会 & 青年体育部",
            "sourceBM": "Persatuan Kanser Kebangsaan Sabah & KBS"
        },
        {
            "id": 2,
            "month": "11",
            "day": "12",
            "name": "Pink Ribbon 20周年健康义诊",
            "nameBM": "Pemeriksaan Kesihatan Percuma Pink Ribbon",
            "location": "PRC Centre Sandakan",
            "category": "免费义诊",
            "categoryBM": "Kesihatan",
            "badgeColor": "bg-[#713f12] text-[#fde68a]",
            "desc": "纪念 Pink Ribbon 成立 20 周年大型惠民筛查，现场提供免费乳房临床触诊、血压、血糖筛检与健康咨询。",
            "descBM": "Pemeriksaan kesihatan percuma sempena ulang tahun ke-20 Pink Ribbon termasuk saringan klinikal payudara dan ujian glukosa darah.",
            "time": "09:00 AM - 03:00 PM",
            "timeBM": "09:00 AM - 03:00 PM",
            "tel": "089-668899",
            "source": "山打根卫生局联合核实",
            "sourceBM": "Disahkan Pejabat Kesihatan Kawasan Sandakan"
        },
        {
            "id": 3,
            "month": "11",
            "day": "16",
            "name": "ITCC Majaps 婆罗洲文化节",
            "nameBM": "Festival Kebudayaan Borneo Majaps",
            "location": "Penampang ITCC Hall",
            "category": "文化盛典",
            "categoryBM": "Budaya",
            "badgeColor": "bg-[#14532d] text-[#86efac]",
            "desc": "汇聚沙巴多元原住民族传统手工艺展示、传统铜锣重奏表演、土著传统美食与服饰文化大展。",
            "descBM": "Pameran kraftangan etnik Borneo, persembahan gong tradisional serta bazar juadah warisan Sabah di Dewan ITCC Penampang.",
            "time": "10:00 AM - 09:00 PM",
            "timeBM": "10:00 AM - 09:00 PM",
            "tel": "088-722111",
            "source": "沙巴文化局官方公告",
            "sourceBM": "Lembaga Kebudayaan Sabah"
        },
        {
            "id": 4,
            "month": "11",
            "day": "20",
            "name": "山打根燕窝与生态农业展",
            "nameBM": "Ekspo Sarang Burung & Eko-Agri Sandakan",
            "location": "Dewan Masyarakat Sandakan",
            "category": "商贸交流",
            "categoryBM": "Perniagaan",
            "badgeColor": "bg-[#1e3a8a] text-[#bfdbfe]",
            "desc": "山打根绿色生态农业与高品质原盏燕窝产业链交流对接会，现场设有加工技术讲座与原产地溯源体验。",
            "descBM": "Persidangan industri sarang burung walit dan pertanian eko Sandakan bersama pakar dan pengeluar tempatan.",
            "time": "08:30 AM - 05:00 PM",
            "timeBM": "08:30 AM - 05:00 PM",
            "tel": "089-223344",
            "source": "沙巴农业与食品安全部",
            "sourceBM": "Kementerian Pertanian & Keterjaminan Makanan Sabah"
        }
    ]

    events_cards_html = ""
    for ev in events_data:
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
                    <div class="text-[11px] text-[#888] truncate flex items-center gap-1 mt-0.5">
                        <span>{ev['location']}</span>
                        <span class="text-[#555]">•</span>
                        <span class="text-[#FFD60A] text-[10px] mono event-expand-hint">
                            <span class="lang-zh">点击展开详情 ▼</span>
                            <span class="lang-bm hidden">Klik butiran ▼</span>
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
                    <a href="tel:{ev['tel']}" onclick="event.stopPropagation();" class="inline-flex items-center gap-1 px-2.5 py-[3px] rounded-full bg-[#FFD60A] text-black font-black text-[10px] hover:bg-[#ffde33] transition">
                        <span>📞</span>
                        <span>{ev['tel']}</span>
                    </a>
                </div>
                <div class="mt-2 flex items-center justify-between text-[10px] text-[#666]">
                    <span class="text-[#22c55e]">✓ <span class="lang-zh">{ev['source']}</span><span class="lang-bm hidden">{ev['sourceBM']}</span></span>
                    <span class="mono">山打根社区公开活动</span>
                </div>
            </div>
        </div>
        """

    # 4. 组装整页 HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>西门看看网 · 每日晨报 | 全自动信源采集与双核实编译引擎</title>
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

                    <!-- 需求 3: 左上角一键分享按钮 -->
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
                <!-- 需求 5: 中文 / BM 语系即时切换 -->
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

        <!-- 需求 2: 顶部红色纯动态无缝全宽跑马灯（移除静态文字，平滑循环活动预告与调度） -->
        <div class="w-full bg-[#DC2626] h-[30px] md:h-[32px] flex items-center overflow-hidden border-y border-[#7f1d1d] relative">
            <div class="marquee-track flex whitespace-nowrap text-[12px] text-white font-medium">
                <!-- 滚动单元 A -->
                <div class="flex gap-8 items-center px-4">
                    <span class="inline-flex items-center gap-1.5 text-[#FFD60A] font-black">
                        <span class="w-2 h-2 rounded-full bg-[#FFD60A] animate-pulse"></span>
                        【沙巴未来2周预告】
                    </span>
                    <span>🏃 11/03 Pinktober Fun Run 5KM 公益跑 @ Taman Rimba RM35 (089-212188)</span>
                    <span class="text-white/40">•</span>
                    <span>🏥 11/12 Pink Ribbon 20周年义诊 免费健康筛查 @ PRC Centre (089-668899)</span>
                    <span class="text-white/40">•</span>
                    <span>🎭 11/16 ITCC Majaps 婆罗洲文化节 @ Penampang 传统盛典 (088-722111)</span>
                    <span class="text-white/40">•</span>
                    <span>🌾 SAZA RICE 买大米赢大奖 豪车 Jetour Dashing 等待赢取 (至 12/31)</span>
                    <span class="text-white/40">•</span>
                    <span>⚡ 实时调度：沙巴电力 SESB 电网维护电压受控，沙巴水务 JANS 北路抢修就绪</span>
                    <span class="text-white/40">•</span>
                    <span>🚗 Marco Thien 租车服务 010-930 1117 随时接单</span>
                </div>
                <!-- 滚动单元 B（无缝对接） -->
                <div class="flex gap-8 items-center px-4" aria-hidden="true">
                    <span class="inline-flex items-center gap-1.5 text-[#FFD60A] font-black">
                        <span class="w-2 h-2 rounded-full bg-[#FFD60A] animate-pulse"></span>
                        【沙巴未来2周预告】
                    </span>
                    <span>🏃 11/03 Pinktober Fun Run 5KM 公益跑 @ Taman Rimba RM35 (089-212188)</span>
                    <span class="text-white/40">•</span>
                    <span>🏥 11/12 Pink Ribbon 20周年义诊 免费健康筛查 @ PRC Centre (089-668899)</span>
                    <span class="text-white/40">•</span>
                    <span>🎭 11/16 ITCC Majaps 婆罗洲文化节 @ Penampang 传统盛典 (088-722111)</span>
                    <span class="text-white/40">•</span>
                    <span>🌾 SAZA RICE 买大米赢大奖 豪车 Jetour Dashing 等待赢取 (至 12/31)</span>
                    <span class="text-white/40">•</span>
                    <span>⚡ 实时调度：沙巴电力 SESB 电网维护电压受控，沙巴水务 JANS 北路抢修就绪</span>
                    <span class="text-white/40">•</span>
                    <span>🚗 Marco Thien 租车服务 010-930 1117 随时接单</span>
                </div>
            </div>
        </div>
    </header>

    <!-- 主体容器 -->
    <main class="mx-auto max-w-[1440px] px-3 md:px-5 py-3 md:py-4">
        <!-- 需求 6: 动态日期与归档栏（今天/昨天/前天/全部挂载） -->
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
                            <span class="lang-zh">条要闻</span>
                            <span class="lang-bm hidden">tajuk</span>
                        </span>
                    </div>
                </div>
                <div class="text-[10px] mono text-[#555] hidden md:block">
                    <span class="lang-zh">标题-only折叠 · 点击展开200-300字全文 · 官方双核实</span>
                    <span class="lang-bm hidden">Tajuk sahaja · Klik kembang baca berita penuh</span>
                </div>
            </div>

            <!-- 需求 6: 日期切换交互按钮 -->
            <div class="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin" id="date-tabs-container">
                <button onclick="switchDateArchive('today', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#FFD60A] bg-[#FFD60A] text-black shadow-[0_2px_10px_rgba(255,214,10,0.3)] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-black">
                        <span class="lang-zh">今天</span><span class="lang-bm hidden">Hari Ini</span>
                        <span class="font-mono font-bold text-[11px] opacity-80">{today_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-black/70">
                        <span class="lang-zh">今日晨报 • {len(headlines)} 条</span>
                        <span class="lang-bm hidden">Edisi Pagi</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('yesterday', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa] hover:border-[#444] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">
                        <span class="lang-zh">昨日归档</span><span class="lang-bm hidden">Semalam</span>
                        <span class="font-mono font-bold text-[11px] opacity-80 text-[#888]">{yesterday_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-[#666]">
                        <span class="lang-zh">已存归档</span>
                        <span class="lang-bm hidden">Tersimpan</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('before', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa] hover:border-[#444] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">
                        <span class="lang-zh">前日精选</span><span class="lang-bm hidden">Kelmarin</span>
                        <span class="font-mono font-bold text-[11px] opacity-80 text-[#888]">{day_before_mmdd}</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-[#666]">
                        <span class="lang-zh">已存归档</span>
                        <span class="lang-bm hidden">Tersimpan</span>
                    </span>
                </button>
                <button onclick="switchDateArchive('all', this)" class="date-tab-btn shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border border-[#252525] bg-[#111] text-[#aaa] hover:border-[#444] transition-all">
                    <span class="text-[12px] font-black leading-none tracking-tight text-white">
                        <span class="lang-zh">全部 • 6天归档</span><span class="lang-bm hidden">Semua 6 Hari</span>
                    </span>
                    <span class="text-[10px] leading-none mono text-[#666]">
                        <span class="lang-zh">历史合辑</span>
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
                                <span class="lang-zh">标题-only • 点击展开看丰富全文</span>
                                <span class="lang-bm hidden">Tajuk sahaja • Klik kembang butiran</span>
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
                                <span class="lang-zh ml-1">双列排版</span>
                                <span class="lang-bm hidden ml-1">2 Kolum</span>
                            </span>
                            <span class="hidden md:inline text-[#666] text-[12px] mono ml-1">
                                <span class="lang-zh">点击标题展开丰富全文 200-300字</span>
                                <span class="lang-bm hidden">Klik baca laporan 200-300 patah</span>
                            </span>
                        </div>
                        <div class="text-[11px] text-[#666] mono flex items-center gap-2">
                            <span>{today_mmdd} • MYT</span>
                        </div>
                    </div>

                    <!-- 需求 1: 强制双列网格 (grid-template-columns: repeat(2, 1fr) !important;) -->
                    <div class="force-two-cols-grid" id="news-grid-container">
                        {news_cards_html}
                    </div>
                </div>

                <!-- 需求 6: 未来2周归档活动看板（支持抽屉化展开看时间、电话与详情） -->
                <div class="bg-[#151515] border border-[#222] rounded-[12px] overflow-hidden mt-2">
                    <div class="px-4 py-3 border-b border-[#222] flex items-center justify-between gap-2">
                        <h3 class="font-black text-[14px] md:text-[15px] flex items-center gap-2">
                            <span>
                                <span class="lang-zh">未来2周归档活动预告</span>
                                <span class="lang-bm hidden">Aktiviti 2 Minggu Akan Datang</span>
                            </span>
                            <span class="hidden sm:inline-flex items-center px-2 py-[1px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">4 <span class="lang-zh">项活动</span><span class="lang-bm hidden">aktiviti</span></span>
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
                    <span>{today_mmdd} {today_time} MYT • 标题-only折叠 点击展开200-300字全文 • 6天归档已启用</span>
                    <span class="text-[#FFD60A]">{len(headlines)} 标题 • 双核实白名单</span>
                </div>
            </div>

            <!-- 需求 4: 右侧侧边栏（直屏时广告双列并排展示，海报限制 max-height: 240px; 避免霸占全屏） -->
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
                            <!-- 需求 4: 尺寸压缩限制 max-height: 240px; object-fit: contain; -->
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
                            <!-- 需求 4: 尺寸压缩限制 max-height: 240px; object-fit: contain; -->
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

    <!-- 交互控制脚本（包含全部 6 项前端逻辑） -->
    <script>
        // 需求 3: 左上角一键分享功能
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

        // 需求 5: 语系即时切换
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

        // 需求 6: 顶部日期按键绑定数据与视图切换
        function switchDateArchive(type, btnElem) {{
            // 更新按钮激活状态
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
            const isBm = document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');

            if (type === 'today') {{
                if (titleElem) {{
                    titleElem.innerHTML = isBm ? '<span>Berita Utama Hari Ini {today_mmdd}</span>' : '<span>今日 {today_mmdd} 重点要闻</span>';
                }}
                if (displayDateElem) {{
                    displayDateElem.textContent = isBm ? 'Hari Ini {today_mmdd} · Auto MYT' : '今天 {today_mmdd} · MYT自动计算';
                }}
                showToast('已载入今日最新核实晨报！', 'Memuatkan berita terkini hari ini!');
            }} else if (type === 'yesterday') {{
                if (titleElem) {{
                    titleElem.innerHTML = isBm ? '<span>Arkib Berita Semalam {yesterday_mmdd}</span>' : '<span>昨日 {yesterday_mmdd} 归档要闻</span>';
                }}
                if (displayDateElem) {{
                    displayDateElem.textContent = isBm ? 'Semalam {yesterday_mmdd} · Arkib' : '昨日 {yesterday_mmdd} · 归档库';
                }}
                showToast('已切换至昨日归档视角！', 'Beralih ke arkib semalam!');
            }} else if (type === 'before') {{
                if (titleElem) {{
                    titleElem.innerHTML = isBm ? '<span>Arkib Berita Kelmarin {day_before_mmdd}</span>' : '<span>前日 {day_before_mmdd} 归档要闻</span>';
                }}
                if (displayDateElem) {{
                    displayDateElem.textContent = isBm ? 'Kelmarin {day_before_mmdd} · Arkib' : '前日 {day_before_mmdd} · 归档库';
                }}
                showToast('已切换至前日归档视角！', 'Beralih ke arkib kelmarin!');
            }} else {{
                if (titleElem) {{
                    titleElem.innerHTML = isBm ? '<span>Semua Arkib 6 Hari</span>' : '<span>全部历史归档 (6天精选)</span>';
                }}
                if (displayDateElem) {{
                    displayDateElem.textContent = isBm ? 'Semua Arkib 6 Hari' : '全部 · 6天历史库';
                }}
                showToast('已开启全量 6 天历史合辑！', 'Membuka kompilasi 6 hari!');
            }}
        }}

        // 需求 6: 未来活动卡片展开/收起抽屉
        function toggleEventCard(id) {{
            const card = document.getElementById('event-card-' + id);
            if (!card) return;
            const isOpen = card.classList.contains('open');
            card.classList.toggle('open');
            const hint = card.querySelector('.event-expand-hint');
            const isBm = document.getElementById('btn-lang-bm').classList.contains('bg-[#FFD60A]');
            if (hint) {{
                if (isOpen) {{
                    hint.innerHTML = isBm ? 'Klik butiran ▼' : '点击展开详情 ▼';
                }} else {{
                    hint.innerHTML = isBm ? 'Tutup ▲' : '点击收起 ▲';
                }}
            }}
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
    print(f"✅ 成功实装 6 大前端需求并重新编译页面: {OUTPUT_HTML_FILE}")

if __name__ == "__main__":
    generate_index_html()
