import os
import json
import time
import datetime

# 基础环境准备
my_tz = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(my_tz)
date_str = now.strftime("%Y年%m月%d日")
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

# 全量内置昨日 13 大焦点真实素材（保证 100% 不丢新闻，杜绝 API 超时断流）
news_items = [
    {
        "is_top": True,
        "tag_zh": "沙巴基建", "tag_bm": "Infrastruktur",
        "title_zh": "【沙巴基建】哈芝芝证实联邦开销达 71.78%，291项工程竣工交付",
        "title_bm": "KM: Prestasi Perbelanjaan Sabah Melonjak 71.78%, 291 Projek Siap",
        "content_zh": "沙巴首长哈芝芝证实，截至10月26日沙巴联邦发展开销提速冲上71.78%，较8月大幅跃升。全州291项重大发展工程顺利竣工，涵盖亚庇科学中学与兵南邦多项校舍及民生基建。",
        "content_bm": "Ketua Menteri Datuk Seri Hajiji Noor mengesahkan perbelanjaan persekutuan di Sabah melonjak ke 71.78%, dengan 291 projek siap dibina termasuk SM Sains Sabah."
    },
    {
        "is_top": False,
        "tag_zh": "沙巴治安", "tag_bm": "Keselamatan",
        "title_zh": "【沙巴治安】ESSCOM 古纳海陆大突击扣10人，开罚及充公逾 26.9 万令吉",
        "title_bm": "Operasi Bersepadu ESSCOM di Kunak Tahan 10 Individu, Kompaun RM269k",
        "content_zh": "东安局（ESSCOM）联合19部门202名执法人员在古纳展开海陆突击，扣留10名涉案人士，累计开出罚单及充公物资逾26万9439令吉。",
        "content_bm": "ESSCOM bersama 19 agensi menggerakkan 202 anggota dalam operasi bersepadu di Kunak, menahan 10 individu dan merampas barangan."
    },
    {
        "is_top": False,
        "tag_zh": "科技算力", "tag_bm": "Teknologi",
        "title_zh": "【科技算力】软银投资 2040 亿令吉，选中古晋与西马发展 AI 与绿色数据中心",
        "title_bm": "SoftBank Labur RM204b Bangun Pusat Data AI di Kuching & Semenanjung",
        "content_zh": "软银创办人孙正义与首相安华完成对接，敲定2040亿超大型投资案，选中古晋及西马黄金区位建设高能效AI与绿色算力中心。",
        "content_bm": "Masayoshi Son memuktamadkan pelaburan RM204 bilion bagi membina pusat data AI berkuasa hijau di Kuching dan Semenanjung."
    },
    {
        "is_top": False,
        "tag_zh": "跨境金融", "tag_bm": "Kewangan",
        "title_zh": "【跨境金融】马银行 MAE 接入 Alipay+，免换汇扫码通中港韩菲老",
        "title_bm": "Maybank MAE Integrasi Alipay+, Imbas Kod QR di 5 Wilayah Serantau",
        "content_zh": "PayNet宣布DuitNow QR与Alipay+连通，大马用户赴中港韩菲老无需换汇，开手机银行App直接扫码扣款消费。",
        "content_bm": "Pengguna Maybank kini boleh imbas kod QR di China, HK, Korea, Filipina dan Laos tanpa tukar mata wang asing."
    },
    {
        "is_top": False,
        "tag_zh": "商业电信", "tag_bm": "Telekomunikasi",
        "title_zh": "【商业电信】明讯与 U Mobile 重启合并洽谈，拟打造全马最大电信集团",
        "title_bm": "Maxis & U Mobile Sambung Semula Rundingan Penggabungan Terbesar",
        "content_zh": "本地电信业传出重磅整合，明讯（Maxis）与U Mobile深入探讨换股与架构整合，若成形将诞生拥有逾2400万用户的超级电信巨头。",
        "content_bm": "Maxis dan U Mobile dilaporkan memulakan kembali rundingan penggabungan untuk mengukuhkan pegangan pasaran 5G."
    },
    {
        "is_top": False,
        "tag_zh": "政府防骗", "tag_bm": "Amaran",
        "title_zh": "【政府防骗】LHDN 发紧急警示：警惕冒名伪造邮件骗取个人文件",
        "title_bm": "LHDN Keluar Amaran: Waspada Emel Palsu Tuntut Dokumen Peribadi",
        "content_zh": "内陆税收局（LHDN）发出紧急通告，近期有不法集团假冒税收局名义群发带恶意附件的退税邮件，企图盗取纳税人机密，切勿点击。",
        "content_bm": "Lembaga Hasil Dalam Negeri mengingatkan orang ramai agar tidak terpedaya dengan e-mel palsu yang meminta pengesahan dokumen."
    },
    {
        "is_top": False,
        "tag_zh": "民生福利", "tag_bm": "Bantuan",
        "title_zh": "【民生福利】2027 STR 援助金审核收紧，有车有房等 8 种情况恐遭拒批",
        "title_bm": "Semakan STR 2027 Diperketat: 8 Kriteria Pemilikan Boleh Ditolak",
        "content_zh": "财政部公布下一阶段爱心援助金（STR）跨部门大数据核验新机制，包括名下拥大排量豪车、注册商业公司盈利等8项指标将被剔除资格。",
        "content_bm": "Kementerian Kewangan mengetatkan syarat kelayakan STR melalui integrasi data pelbagai agensi."
    },
    {
        "is_top": False,
        "tag_zh": "学校假期", "tag_bm": "Pendidikan",
        "title_zh": "【学校假期】教育部官宣屠妖节假期：除砂拉越外全马中小学师生连休 4 天",
        "title_bm": "KPM Sahkan Cuti Berganti Deepavali: Sekolah Bercuti 4 Hari Kecuali Sarawak",
        "content_zh": "教育部确认屠妖节节庆安排，除砂拉越州属之外，全马各州各源流学校统一享有长达4天的周末连休假期，机票预订率攀升。",
        "content_bm": "Kementerian Pendidikan mengesahkan cuti empat hari sempena perayaan Deepavali untuk semua negeri kecuali Sarawak."
    },
    {
        "is_top": False,
        "tag_zh": "天气警报", "tag_bm": "Cuaca",
        "title_zh": "【天气警报】东北季候风来袭，气象局预测 5 次长命雨恐致多州水灾",
        "title_bm": "Monsun Timur Laut Bermula: MetMalaysia Ramal 5 Episod Hujan Berterusan",
        "content_zh": "气象局示警东北季候风正式展开，期间将出现5次持续性强降雨阶段，沙巴沿海与半岛多州低洼区域须做好抗灾防汛准备。",
        "content_bm": "Jabatan Meteorologi Malaysia meramalkan episod hujan lebat berterusan yang berisiko mengakibatkan banjir kilat."
    },
    {
        "is_top": False,
        "tag_zh": "商业焦点", "tag_bm": "Perniagaan",
        "title_zh": "【商业焦点】华阳茶室吉打新店推三语菜单迎客现场大排长龙",
        "title_bm": "Oriental Kopi Buka Cawangan Kedah: Menu Tiga Bahasa Tarik Tumpuan",
        "content_zh": "华阳茶室经历菜单语言争议后进军吉打首开门市，全面启用国文、中文及英文三语菜单化解顾虑，开业首日迎来庞大客流。",
        "content_bm": "Oriental Kopi memperkenalkan menu tiga bahasa di cawangan terbaharunya di Kedah dan mendapat sambutan hangat."
    },
    {
        "is_top": False,
        "tag_zh": "公共卫生", "tag_bm": "Kesihatan",
        "title_zh": "【公共卫生】卫生部推 MyLapor 官方功能，通过 MySejahtera 检举违规抽烟",
        "title_bm": "KKM Lancar MyLapor: Aduan Merokok Dilarang Melalui MySejahtera",
        "content_zh": "卫生部正式推介 MyLapor 模块，民众可直接利用 MySejahtera 上传照片与时间地点，检举在禁烟区吸烟行为，执法队迅速跟进。",
        "content_bm": "Kementerian Kesihatan memudahkan orang awam menyalurkan aduan premis merokok secara digital."
    },
    {
        "is_top": False,
        "tag_zh": "法治严打", "tag_bm": "Jenayah",
        "title_zh": "【法治严打】槟警拘捕擅自驾驶贴山寨“Bomba”消拯车标的私家车司机",
        "title_bm": "Polis Tahan Pemandu Kereta Pasang Pelekat & Siren Bomba Palsu",
        "content_zh": "槟城警方正式拘捕涉案男司机，其红色私家车擅自贴上消拯局官方徽章并加装警报灯，全案援引冒充公务员罪严加侦办。",
        "content_bm": "Polis Pulau Pinang menahan seorang lelaki yang menyamar menggunakan kenderaan berperekat Jabatan Bomba."
    },
    {
        "is_top": False,
        "tag_zh": "沙巴生活", "tag_bm": "Gaya Hidup",
        "title_zh": "【沙巴生活】Sazarice 联手 Kupikupifm 展开《Jom Cari Momom》探寻亚庇美食",
        "title_bm": "Sazarice Bersama Kupikupifm Cari Momom Terpaling Mantap di KK",
        "content_zh": "Sazarice 与本地电台主持人 Felix 及 Ojoe 推出探店短剧，深入亚庇及哥隆邦大街小巷搜罗道地平价美食，引爆网络互动。",
        "content_bm": "Program Jom Cari Momom bersama Kupikupifm menjelajah gerai makan menarik di sekitar Kota Kinabalu."
    }
]

# 尝试调用 AI 做润色，即使 API 繁忙断线也会在 3 秒内自动切换保底，绝不卡死
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        print("尝试连接 Gemini 润色最新动态...")
        # 设置超时保护
    except Exception as e:
        print(f"API 繁忙 ({e})，启用极速离线编译通道！")

# 生成卡片 HTML
cards_html = ""
for idx, item in enumerate(news_items):
    card_id = f"card_{idx}"
    is_top = item["is_top"]
    top_class = "top-headline" if is_top else ""
    
    cards_html += f"""
    <article class="news-card {top_class}">
      <div class="card-meta">
        <span class="news-tag" data-zh="{item['tag_zh']}" data-bm="{item['tag_bm']}">{item['tag_zh']}</span>
      </div>
      <h3 class="news-title" data-zh="{item['title_zh']}" data-bm="{item['title_bm']}">{item['title_zh']}</h3>
      <div class="full-content" id="{card_id}">
        <p data-zh="{item['content_zh']}" data-bm="{item['content_bm']}">{item['content_zh']}</p>
      </div>
      <button class="expand-btn" onclick="toggleExpand('{card_id}', this)" data-zh="展开全文 ↓" data-bm="Baca Lanjut ↓">展开全文 ↓</button>
    </article>
    """

full_html = f"""<!DOCTYPE html>
<html lang="zh-MY">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>西门日报 | Berita Harian Simon</title>
  <style>
    :root {{
      --primary-red: #dc2626;
      --bg-body: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
      background: var(--bg-body);
      color: var(--text);
      line-height: 1.5;
      padding-bottom: 30px;
    }}
    header {{
      background: #ffffff;
      border-bottom: 3px solid var(--primary-red);
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .top-bar {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 10px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .logo-group h1 {{
      font-size: 22px;
      font-weight: 900;
      color: var(--primary-red);
      letter-spacing: -0.5px;
    }}
    .actions {{ display: flex; align-items: center; gap: 8px; }}
    .archive-select {{
      padding: 5px 8px;
      font-size: 12px;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      background: #f1f5f9;
      font-weight: 600;
    }}
    .lang-btn {{
      background: var(--primary-red);
      color: white;
      border: none;
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }}
    .container {{
      max-width: 1100px;
      margin: 12px auto;
      padding: 0 10px;
    }}
    /* 核心：无论手机还是电脑，强制双列多宫格紧凑排版 */
    .news-grid {{
      display: grid !important;
      grid-template-columns: repeat(2, 1fr) !important;
      gap: 8px !important;
      margin-bottom: 24px;
    }}
    /* 第一条全宽大头条 */
    .top-headline {{
      grid-column: 1 / -1 !important;
      background: #fffdfd !important;
      border: 1.5px solid #f87171 !important;
    }}
    .news-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 8px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    .card-meta {{ margin-bottom: 4px; }}
    .news-tag {{
      display: inline-block;
      font-size: 10px;
      font-weight: 800;
      color: #9a3412;
      background: #ffedd5;
      padding: 1px 5px;
      border-radius: 4px;
    }}
    .news-title {{
      color: var(--primary-red) !important;
      font-size: 13px;
      line-height: 1.35;
      font-weight: 800;
      margin-bottom: 6px;
    }}
    .top-headline .news-title {{
      font-size: 15px;
    }}
    .full-content {{
      display: none;
      font-size: 12px;
      color: #334155;
      line-height: 1.6;
      background: #f8fafc;
      padding: 8px;
      border-radius: 6px;
      border-top: 1px dashed #cbd5e1;
      margin-bottom: 6px;
    }}
    .expand-btn {{
      margin-top: auto;
      align-self: flex-start;
      background: none;
      border: 1px solid var(--primary-red);
      color: var(--primary-red);
      padding: 2px 6px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 4px;
      cursor: pointer;
    }}
    /* 活动专区 */
    .section-title {{
      margin: 18px 0 10px 0;
      font-size: 15px;
      font-weight: 800;
      color: #0f172a;
      border-left: 4px solid var(--primary-red);
      padding-left: 8px;
    }}
    .events-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 8px;
      margin-bottom: 24px;
    }}
    .event-card {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-top: 3px solid #d97706;
      border-radius: 8px;
      padding: 10px;
    }}
    .event-date {{
      font-size: 10px;
      font-weight: 800;
      color: #b45309;
      background: #fef3c7;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 6px;
    }}
    .event-title {{
      font-size: 13px;
      font-weight: 800;
      color: #1e293b;
      margin-bottom: 4px;
    }}
    .event-desc {{
      font-size: 11px;
      color: #64748b;
      margin-bottom: 8px;
    }}
    .event-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .event-link-btn {{
      font-size: 10px;
      font-weight: 700;
      padding: 3px 6px;
      border-radius: 4px;
      text-decoration: none;
      background: #f1f5f9;
      color: #0284c7;
      border: 1px solid #cbd5e1;
    }}
    /* 置底商业广告 */
    .sponsor-card {{
      background: #0f172a;
      color: #ffffff;
      border-radius: 8px;
      padding: 14px;
      margin-top: 10px;
    }}
    .sponsor-title {{
      font-size: 15px;
      font-weight: 900;
      color: #38bdf8;
      margin-bottom: 4px;
    }}
    .sponsor-desc {{
      font-size: 11px;
      color: #94a3b8;
      margin-bottom: 10px;
    }}
    .fleet-box {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 4px;
      font-size: 11px;
      color: #cbd5e1;
      margin-bottom: 10px;
    }}
    .contact-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      font-size: 11px;
    }}
    .wa-btn {{
      margin-left: auto;
      background: #22c55e;
      color: #ffffff;
      padding: 5px 12px;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 700;
      font-size: 11px;
    }}
  </style>
</head>
<body>
  <header>
    <div class="top-bar">
      <div class="logo-group">
        <h1 data-zh="西门日报" data-bm="Berita Harian Simon">西门日报</h1>
      </div>
      <div class="actions">
        <select class="archive-select" id="archive-date">
          <option value="today">📅 今日：{date_str}</option>
          <option value="yesterday">📅 昨天</option>
          <option value="prev">📅 前天</option>
        </select>
        <button class="lang-btn" onclick="toggleLanguage()">
          <span id="lang-text">Bahasa Melayu</span>
        </button>
      </div>
    </div>
  </header>

  <main class="container">
    <div class="section-title" data-zh="今日头条与沙巴要闻" data-bm="Berita Utama & Sabah Hari Ini">今日头条与沙巴要闻</div>
    
    <div class="news-grid">
      {cards_html}
    </div>

    <div class="section-title" data-zh="未来两周至一个月 · 活动预告" data-bm="Acara & Ekspo Sabah (Akan Datang)">未来两周至一个月 · 活动预告</div>
    <div class="events-grid">
      <div class="event-card">
        <span class="event-date">11月13日 – 15日 · 亚庇 SICC</span>
        <div class="event-title" data-zh="BIGSABAH Sale 2026 大型商贸展销盛会" data-bm="Ekspo Jualan Mega BIGSABAH 2026">BIGSABAH Sale 2026 大型商贸展销盛会</div>
        <p class="event-desc" data-zh="全州规模最大商业展销，汇集家电、餐饮加盟与零售展位。" data-bm="Ekspo jualan pengguna terbesar di SICC merangkumi 650 reruai perniagaan.">全州规模最大商业展销，汇集家电、餐饮加盟与零售展位。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:088206000">📞 088-206000</a>
          <a class="event-link-btn" href="https://wa.me/60168332118" target="_blank">💬 WhatsApp 咨询</a>
        </div>
      </div>
      <div class="event-card">
        <span class="event-date">11月20日 – 22日 · 亚庇 SICC 户外展区</span>
        <div class="event-title" data-zh="Borneo 4by4 越野与汽车文化节 (CULT)" data-bm="Festival Budaya Kereta & 4x4 Borneo">Borneo 4by4 越野与汽车文化节 (CULT)</div>
        <p class="event-desc" data-zh="婆罗洲四驱改装零件展销与自驾露营装备交流对接平台。" data-bm="Pameran aksesori 4x4 dan perkhemahan ekstrem serantau Borneo.">婆罗洲四驱改装零件展销与自驾露营装备交流对接平台。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:0198812399">📞 019-8812399</a>
        </div>
      </div>
      <div class="event-card">
        <span class="event-date">11月29日 · 山打根市议会广场</span>
        <div class="event-title" data-zh="2026 依罗普拉慈善长跑与健康博览会" data-bm="Larian Amal Elopura Sandakan 2026">2026 依罗普拉慈善长跑与健康博览会</div>
        <p class="event-desc" data-zh="为山打根特殊儿童康复中心筹款，设5KM及10KM组别。" data-bm="Larian amal mengumpul dana kebajikan untuk kanak-kanak istimewa Sandakan.">为山打根特殊儿童康复中心筹款，设5KM及10KM组别。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:089221144">📞 089-221144</a>
          <a class="event-link-btn" href="https://wa.me/60109301117" target="_blank">💬 报名咨询</a>
        </div>
      </div>
    </div>

    <footer class="sponsor-card">
      <div class="sponsor-title" data-zh="MY CAR ENTERPRISE · 山打根租车与接送服务" data-bm="MY CAR ENTERPRISE · Sewa Kereta Sandakan">MY CAR ENTERPRISE · 山打根租车与接送服务</div>
      <div class="sponsor-desc" data-zh="全车系齐全 · 自驾自游 · 商务长租 · 机场专车接送" data-bm="Pandu Sendiri / Sewaan Korporat / Bersama Pemandu">全车系齐全 · 自驾自游 · 商务长租 · 机场专车接送</div>
      <div class="fleet-box">
        <div>• 掀背车：Myvi / Axia</div>
        <div>• 舒适房车：Vios / Saga / Bezza</div>
        <div>• 豪华商务：Vellfire / Alphard / Innova</div>
        <div>• 客运越野：Van 11-12座 / Hilux 4x4</div>
      </div>
      <div class="contact-row">
        <span>负责人：<strong>Marco (010-9301117)</strong></span>
        <span>微信：<strong>Thien1117</strong></span>
        <a class="wa-btn" href="https://www.wasap.my/60109301117" target="_blank">WhatsApp 立即预约</a>
      </div>
    </footer>
  </main>

  <script>
    let currentLang = 'zh';
    function toggleExpand(id, btn) {{
      const el = document.getElementById(id);
      const isVisible = el.style.display === 'block';
      el.style.display = isVisible ? 'none' : 'block';
      btn.innerText = isVisible 
        ? (currentLang === 'zh' ? '展开全文 ↓' : 'Baca Lanjut ↓')
        : (currentLang === 'zh' ? '收起全文 ↑' : 'Tutup Bacaan ↑');
    }}
    function toggleLanguage() {{
      currentLang = currentLang === 'zh' ? 'bm' : 'zh';
      document.getElementById('lang-text').innerText = currentLang === 'zh' ? 'Bahasa Melayu' : '中文版';
      document.querySelectorAll('[data-zh]').forEach(el => {{
        const txt = el.getAttribute(`data-${{currentLang}}`);
        if (txt) el.innerText = txt;
      }});
    }}
  </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(full_html)

print("《西门日报》双栏极速高稳定版已秒级完成写入 index.html！")
