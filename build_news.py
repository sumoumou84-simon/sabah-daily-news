import os
import json
import time
import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("未找到 GEMINI_API_KEY 密鑰！")

client = genai.Client(api_key=api_key)

my_tz = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(my_tz)
date_str = now.strftime("%Y年%m月%d日")
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

prompt = f"""
你是一名沙巴與全馬權威新聞主編。請將過去24小時的重點新聞整理為標準 JSON 陣列輸出，供《西門日報》渲染。
今日日期：{date_str} · {weekday_str}。

【必須收錄的全部焦點主題】：
1. 【沙巴基建】哈芝芝證實聯邦開銷達 71.78%，291項工程竣工交付（亞庇科學中學與兵南邦新校舍）。
2. 【沙巴治安】ESSCOM 古納海陸大突擊扣10人，開罰及充公逾 26.9 萬令吉。
3. 【科技算力】軟銀孫正義投資 2040 億令吉，選中古晉與西馬發展 AI 與綠色數據中心。
4. 【跨境金融】馬銀行 MAE 接入 Alipay+，免換匯掃碼直通中港韓菲老。
5. 【商業電信】明訊與 U Mobile 重啟合併洽談，擬打造全馬最大電信集團。
6. 【政府防騙】稅收局（LHDN）發緊急警示：警惕冒名假郵件騙取文件。
7. 【民生福利】2027 STR 援助金審核收緊，有車有房等 8 種情況恐拒批。
8. 【學校假期】教育部官宣屠妖節假期：除砂拉越外全馬師生連休 4 天。
9. 【天氣警報】東北季候風來襲，氣象局預測 5 次長命雨恐致水災。
10. 【商業焦點】華陽茶室吉打新店推三語菜單迎客現場大排長龍。
11. 【公共衛生】衛生部推 MyLapor 官方功能，通過 MySejahtera 檢舉違規抽煙。
12. 【法治嚴打】檳警拘捕擅自駕駛貼山寨“Bomba”消拯車標的私家車司機。
13. 【沙巴生活】Sazarice 聯手 Kupikupifm 展開《Jom Cari Momom》探尋亞庇與哥隆邦美食。

【輸出格式規範】：
只輸出一個合法的 JSON 陣列，不帶任何額外解釋文字或 markdown 代碼塊標記。陣列中每個物件格式如下：
[
  {{
    "is_top": true,  // 只有第一篇沙巴基建設為 true，其餘一律為 false
    "tag_zh": "沙巴基建",
    "tag_bm": "Infrastruktur",
    "title_zh": "【沙巴基建】哈芝芝證實聯邦開銷達 71.78%，291項工程竣工交付",
    "title_bm": "KM: Prestasi Perbelanjaan Sabah Melonjak 71.78%, 291 Projek Siap",
    "excerpt_zh": "沙巴首長哈芝芝證實，沙巴聯邦發展撥款支出達71.78%，包含亞庇科學中學與兵南邦新校舍等291項基建順利竣工。",
    "excerpt_bm": "Ketua Menteri Sabah sahkan perbelanjaan persekutuan capai 71.78% dengan 291 projek siap dibina.",
    "content_zh": "【亞庇訊】首長哈芝芝指出，得益於州政府聯合聯邦公共工程部（JKR）實施的現場督導機制，全州多項基建重回正軌，有力改善了亞庇、兵南邦及內陸走廊的民生條件。",
    "content_bm": "KM menegaskan pemantauan mingguan bersama JKR berjaya memulihkan projek dan memperkukuh infrastruktur asas di seluruh Sabah."
  }}
]
"""

target_model = "gemini-3.8-flash"
response = None

for attempt in range(4):
    try:
        print(f"調用模型獲取新聞資料 (第 {attempt+1} 次)...")
        response = client.models.generate_content(
            model=target_model,
            contents=prompt
        )
        if response and response.text:
            break
    except Exception as e:
        wait_seconds = (attempt + 1) * 5
        print(f"等待重試 ({e})...")
        time.sleep(wait_seconds)

if not response or not response.text:
    raise RuntimeError("模型調用失敗，請稍後重試。")

raw_json = response.text.strip()
if raw_json.startswith("```json"):
    raw_json = raw_json[7:]
if raw_json.startswith("```"):
    raw_json = raw_json[3:]
if raw_json.endswith("```"):
    raw_json = raw_json[:-3]
raw_json = raw_json.strip()

news_items = json.loads(raw_json)

# 生成新聞卡片 HTML
cards_html = ""
for idx, item in enumerate(news_items):
    card_id = f"card_{idx}"
    is_top = item.get("is_top", False)
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
      <button class="expand-btn" onclick="toggleExpand('{card_id}', this)" data-zh="展開全文 ↓" data-bm="Baca Lanjut ↓">展開全文 ↓</button>
    </article>
    """

full_html = f"""<!DOCTYPE html>
<html lang="zh-MY">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>西門日報 | Berita Harian Simon</title>
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
    /* 強制雙排多宮格：手機與電腦均為 2 列 */
    .news-grid {{
      display: grid !important;
      grid-template-columns: repeat(2, 1fr) !important;
      gap: 10px !important;
      margin-bottom: 24px;
    }}
    /* 頂層全寬焦點卡片 */
    .top-headline {{
      grid-column: 1 / -1 !important;
      background: #fffdfd !important;
      border: 1.5px solid #f87171 !important;
    }}
    .news-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 10px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    .card-meta {{ margin-bottom: 6px; }}
    .news-tag {{
      display: inline-block;
      font-size: 11px;
      font-weight: 800;
      color: #9a3412;
      background: #ffedd5;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .news-title {{
      color: var(--primary-red) !important;
      font-size: 14px;
      line-height: 1.35;
      font-weight: 800;
      margin-bottom: 8px;
    }}
    .top-headline .news-title {{
      font-size: 16px;
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
      margin-bottom: 8px;
    }}
    .expand-btn {{
      margin-top: auto;
      align-self: flex-start;
      background: none;
      border: 1px solid var(--primary-red);
      color: var(--primary-red);
      padding: 3px 8px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 4px;
      cursor: pointer;
    }}
    /* 活動預告專區 */
    .section-title {{
      margin: 20px 0 10px 0;
      font-size: 16px;
      font-weight: 800;
      color: #0f172a;
      border-left: 4px solid var(--primary-red);
      padding-left: 8px;
    }}
    .events-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 10px;
      margin-bottom: 24px;
    }}
    .event-card {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-top: 3px solid #d97706;
      border-radius: 8px;
      padding: 12px;
    }}
    .event-date {{
      font-size: 11px;
      font-weight: 800;
      color: #b45309;
      background: #fef3c7;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 6px;
    }}
    .event-title {{
      font-size: 14px;
      font-weight: 800;
      color: #1e293b;
      margin-bottom: 6px;
    }}
    .event-desc {{
      font-size: 12px;
      color: #64748b;
      margin-bottom: 10px;
    }}
    .event-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .event-link-btn {{
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 4px;
      text-decoration: none;
      background: #f1f5f9;
      color: #0284c7;
      border: 1px solid #cbd5e1;
    }}
    /* 置底廣告 */
    .sponsor-card {{
      background: #0f172a;
      color: #ffffff;
      border-radius: 8px;
      padding: 16px;
      margin-top: 10px;
    }}
    .sponsor-title {{
      font-size: 16px;
      font-weight: 900;
      color: #38bdf8;
      margin-bottom: 4px;
    }}
    .sponsor-desc {{
      font-size: 12px;
      color: #94a3b8;
      margin-bottom: 12px;
    }}
    .fleet-box {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 6px;
      font-size: 11px;
      color: #cbd5e1;
      margin-bottom: 12px;
    }}
    .contact-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      font-size: 12px;
    }}
    .wa-btn {{
      margin-left: auto;
      background: #22c55e;
      color: #ffffff;
      padding: 6px 14px;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 700;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <header>
    <div class="top-bar">
      <div class="logo-group">
        <h1 data-zh="西門日報" data-bm="Berita Harian Simon">西門日報</h1>
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
    <div class="section-title" data-zh="今日頭條與沙巴要聞" data-bm="Berita Utama & Sabah Hari Ini">今日頭條與沙巴要聞</div>
    
    <div class="news-grid">
      {cards_html}
    </div>

    <div class="section-title" data-zh="未來兩周至一個月 · 活動預告" data-bm="Acara & Ekspo Sabah (Akan Datang)">未來兩周至一個月 · 活動預告</div>
    <div class="events-grid">
      <div class="event-card">
        <span class="event-date">11月13日 – 15日 · 亞庇 SICC</span>
        <div class="event-title" data-zh="BIGSABAH Sale 2026 大型商貿展銷盛會" data-bm="Ekspo Jualan Mega BIGSABAH 2026">BIGSABAH Sale 2026 大型商貿展銷盛會</div>
        <p class="event-desc" data-zh="全州規模最大商業展銷，匯集家電、餐飲加盟與零售展位。" data-bm="Ekspo jualan pengguna terbesar di SICC merangkumi 650 reruai perniagaan.">全州規模最大商業展銷，匯集家電、餐飲加盟與零售展位。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:088206000">📞 088-206000</a>
          <a class="event-link-btn" href="[https://wa.me/60168332118](https://wa.me/60168332118)" target="_blank">💬 WhatsApp 諮詢</a>
        </div>
      </div>
      <div class="event-card">
        <span class="event-date">11月20日 – 22日 · 亞庇 SICC 戶外展區</span>
        <div class="event-title" data-zh="Borneo 4by4 越野與汽車文化節 (CULT)" data-bm="Festival Budaya Kereta & 4x4 Borneo">Borneo 4by4 越野與汽車文化節 (CULT)</div>
        <p class="event-desc" data-zh="婆羅洲四驅改裝零件展銷與自駕露營裝備交流對接平台。" data-bm="Pameran aksesori 4x4 dan perkhemahan ekstrem serantau Borneo.">婆羅洲四驅改裝零件展銷與自駕露營裝備交流對接平台。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:0198812399">📞 019-8812399</a>
        </div>
      </div>
      <div class="event-card">
        <span class="event-date">11月29日 · 山打根市議會廣場</span>
        <div class="event-title" data-zh="2026 依羅普拉慈善長跑與健康博覽會" data-bm="Larian Amal Elopura Sandakan 2026">2026 依羅普拉慈善長跑與健康博覽會</div>
        <p class="event-desc" data-zh="為山打根特殊兒童康復中心籌款，設5KM及10KM組別。" data-bm="Larian amal mengumpul dana kebajikan untuk kanak-kanak istimewa Sandakan.">為山打根特殊兒童康復中心籌款，設5KM及10KM組別。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:089221144">📞 089-221144</a>
          <a class="event-link-btn" href="[https://wa.me/60109301117](https://wa.me/60109301117)" target="_blank">💬 報名諮詢</a>
        </div>
      </div>
    </div>

    <footer class="sponsor-card">
      <div class="sponsor-title" data-zh="MY CAR ENTERPRISE · 山打根租車與接送服務" data-bm="MY CAR ENTERPRISE · Sewa Kereta Sandakan">MY CAR ENTERPRISE · 山打根租車與接送服務</div>
      <div class="sponsor-desc" data-zh="全車系齊全 · 自駕自遊 · 商務長租 · 機場專車接送" data-bm="Pandu Sendiri / Sewaan Korporat / Bersama Pemandu">全車系齊全 · 自駕自遊 · 商務長租 · 機場專車接送</div>
      <div class="fleet-box">
        <div>• 掀背車：Myvi / Axia</div>
        <div>• 舒適房車：Vios / Saga / Bezza</div>
        <div>• 豪華商務：Vellfire / Alphard / Innova</div>
        <div>• 客運越野：Van 11-12座 / Hilux 4x4</div>
      </div>
      <div class="contact-row">
        <span>負責人：<strong>Marco (010-9301117)</strong></span>
        <span>微信：<strong>Thien1117</strong></span>
        <a class="wa-btn" href="[https://www.wasap.my/60109301117](https://www.wasap.my/60109301117)" target="_blank">WhatsApp 立即預約</a>
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
        ? (currentLang === 'zh' ? '展開全文 ↓' : 'Baca Lanjut ↓')
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

print("《西門日報》雙欄高密度極速架構已成功編譯寫入 index.html！")
