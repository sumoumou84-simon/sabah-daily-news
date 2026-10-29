import os
import time
import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("未找到 GEMINI_API_KEY 密钥！")

client = genai.Client(api_key=api_key)

my_tz = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(my_tz)
date_str = now.strftime("%Y年%m月%d日")
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

prompt = f"""
你是一名沙巴与全马权威新闻主编。请为《西门日报 / Berita Harian Simon》生成一份完整、高质量、信息充实的单文件 index.html 代码。
今日日期：{date_str} · {weekday_str}。

【硬性排版要求】：
1. 顶部通栏：
   - 报头《西门日报 / BERITA HARIAN SIMON》。
   - 右上角包含：历史日期下拉框 [今日：{date_str} | 昨天 | 前天]、布局切换按钮 [📱 手机版 / 💻 电脑版]（点击给 body 切换 .mobile-view）、双语切换按钮 [Bahasa Melayu / 中文]。
   - 【严禁输出任何 BREAKING 走马灯或滚动条】。

2. 今日头条与沙巴要闻（采用双排多宫格 CSS Grid repeat(2, 1fr) 布局，手机版 .mobile-view 下为 1 列）：
   【最顶层全宽特大头条 (grid-column: 1 / -1)】：
   - 【沙巴基建】哈芝芝证实联邦开销达 71.78%，291项工程竣工（涵盖亚庇科学中学及兵南邦新校舍）。
   
   【以下采用双排宫格并列排列，涵盖全部重点】：
   1. 【沙巴治安】ESSCOM 古纳海陆大突击扣10人，开罚及充公逾 26.9 万令吉。
   2. 【科技算力】软银投资 2040 亿令吉，选中古晋与西马发展 AI 与绿色数据中心。
   3. 【跨境金融】马银行 MAE 接入 Alipay+，免换汇扫码通中港韩菲老。
   4. 【商业电信】明讯与 U Mobile 重启合并洽谈，拟打造全马最大电信集团。
   5. 【政府防骗】LHDN 发紧急警示：警惕冒名假邮件骗取文件。
   6. 【民生福利】2027 STR 援助金审核收紧，有车有房等 8 种情况恐拒批。
   7. 【学校假期】教育部定屠妖节假期：除砂拉越外全马师生连休 4 天。
   8. 【天气警报】东北季候风来袭，气象局预测 5 次长命雨恐致水灾。
   9. 【商业焦点】华阳茶室吉打新店推三语菜单迎客现场大排长龙。
   10. 【公共卫生】卫生部推 MyLapor 官方功能，通过 MySejahtera 检举违规抽烟。
   11. 【法治严打】槟警拘捕擅自驾驶贴山寨“Bomba”消拯车标的私家车司机。
   12. 【沙巴生活】Sazarice 联手 Kupikupifm 展开《Jom Cari Momom》探寻亚庇与哥隆邦美食。

3. 每张新闻卡片规范：
   - 标题文字本身必须为深红色 (#dc2626)。
   - 绝不使用外部网络图片！每篇卡片顶部内嵌轻量简洁色彩明亮的【SVG 矢量场景图】（神山、巡逻船、芯片、手机扫码、警车等几何色块绘制，代码精简）。
   - 卡片表面 2 行摘要，配有「展开阅读全文 ↓ / 收起全文 ↑」折叠容器（默认隐藏，点击 display: block）。

4. 未来两周至一个月 · 沙巴商业、展销与慈善活动预告（独立多宫格专区）：
   - 亚庇 SICC：BIGSABAH Sale 2026 年度大型展销盛会（逾650展位）。
   - 亚庇 SICC：Borneo 4by4 户外越野与汽车文化节（CULT Festival）。
   - 山打根：2026年依罗普拉慈善马拉松博览会（Elopura Charity Run 2026）。

5. 商业赞助（必须固定在全网页最下方）：
   - 商户：MY CAR ENTERPRISE · 山打根租车与接送服务（Marco: 010-9301117 / WeChat: Thien1117）。

所有文字配备 data-zh 与 data-bm 属性，支持一键切换马来文。
只输出 <!DOCTYPE html> 开头到 </html> 结尾代码，不带 markdown 标记。
"""

# 使用当前环境支持的最新模型
models_to_try = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]
response = None

for model_name in models_to_try:
    for attempt in range(2):
        try:
            print(f"尝试使用模型 {model_name} (第 {attempt+1} 次)...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                break
        except Exception as e:
            print(f"请求波动: {e}")
            time.sleep(3)
    if response and response.text:
        break

if not response or not response.text:
    raise RuntimeError("模型调用失败，请稍后重试。")

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

print("西门日报全量新闻与活动预告已成功写入 index.html！")
