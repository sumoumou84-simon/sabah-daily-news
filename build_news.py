import os
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
你是一名沙巴與全馬權威新聞主編。請為《西門日報 / Berita Harian Simon》生成一份完整、高資訊密度、單文件 index.html 代碼。
今日日期：{date_str} · {weekday_str}。

【極其嚴格的排版與 CSS 規範（絕對不可違反）】：
1. 嚴禁跑馬燈：絕不輸出任何 BREAKING 走馬燈。
2. 頂部通欄：包含報頭《西門日報 / BERITA HARIAN SIMON》、歷史日期下拉選單、雙語切換按鈕。
3. 【手機端與電腦端強制雙列多宮格 (Dual-Column Grid)】：
   - 核心 CSS 必須寫死：
     .news-grid {{
       display: grid !important;
       grid-template-columns: repeat(2, 1fr) !important; /* 嚴禁在手機版改為 1fr！手機也必須是 2 列！ */
       gap: 8px !important;
       margin-bottom: 24px;
     }}
   - 頂部第一篇特大焦點（沙巴基建 71.78%）：grid-column: 1 / -1; 獨佔全寬，附帶輕量頂圖與簡介。
   - 【其餘所有新聞（雙列宮格卡片）】：
     * 表面【嚴禁顯示冗長摘要段落】！
     * 表面【只顯示】：分類小標籤、深紅色粗體標題（color: #dc2626 !important; font-size: 14px; font-weight: 800; line-height: 1.3;）、以及一個精緻的「展開全文 ↓」按鍵。
     * 部分重要新聞才帶精簡小巧的配圖（高度控制在 80px-100px 以內），其他政策通報一律為純文字緊湊卡片。
     * 所有正文必須預設隱藏在 display: none 的容器中，點擊「展開全文 ↓」才展開顯示。
   - 必須收錄全部 13-15 條要聞（沙巴基建、古納大掃蕩、軟銀投資、馬銀行掃碼、明訊合併、LHDN防騙、STR援助金、屠妖節連假、季候風長命雨、華陽茶室、MyLapor抽煙檢舉、假消防車、Sazarice美食等）。

4. 未來兩周至一個月 · 沙巴商業、展銷與慈善活動預告（獨立專區，自帶撥號與 WhatsApp）：
   - SICC BIGSABAH Sale（附 tel:088206000 與 wa.me 直達）
   - SICC 越野汽車節（附 tel:0198812399 參展熱線）
   - 山打根依羅普拉慈善跑（附 tel:089221144 與 wa.me 直達）

5. 置底商業贊助：
   - MY CAR ENTERPRISE · 山打根租車（Marco: 010-9301117 / WeChat: Thien1117 / WhatsApp 預約）。

所有文字具備 data-zh 與 data-bm，支援一秒切換馬來文。
只輸出完整 <!DOCTYPE html> 開頭到 </html> 結尾的純 HTML，不帶 markdown 標記。
"""

target_model = "gemini-3.8-flash"
response = None

for attempt in range(4):
    try:
        print(f"嘗試調用官方主力模型 {target_model} (第 {attempt+1} 次)...")
        response = client.models.generate_content(
            model=target_model,
            contents=prompt
        )
        if response and response.text:
            break
    except Exception as e:
        wait_seconds = (attempt + 1) * 8
        print(f"伺服器忙碌中 ({e})，等待 {wait_seconds} 秒後重試...")
        time.sleep(wait_seconds)

if not response or not response.text:
    raise RuntimeError("模型在多次重試後仍繁忙，請稍後重試。")

html_code = response.text.strip()
if html_code.startswith("```html"):
    html_code = html_code[7:]
if html_code.startswith("```"):
    html_code = html_code[3:]
if html_code.endswith("```"):
    html_code = html_code[:-3]

html_code = html_code.strip()

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

print("西門日報手機端雙列超緊湊版已編譯完成並寫入 index.html！")
