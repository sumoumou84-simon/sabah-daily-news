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
date_bm = now.strftime("%d %B %Y")
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

prompt = f"""
你是一名沙巴与全马权威新闻主编。请为《西门日报 / Berita Harian Simon》生成一份完整、高质量、信息极其充实的单文件 index.html 代码。
今日日期：{date_str} · {weekday_str}。

【版面严格排版与功能规范（绝对不可违反）】：
1. 顶部通栏：
   - 报头《西门日报 / BERITA HARIAN SIMON》。
   - 右上角包含三组控件：
     a. 历史日期下拉框：[📅 今日：{date_str} | 📅 昨天 | 📅 前天]
     b. 布局切换按钮：[📱 手机版 / 💻 电脑版]（通过给 body 切换 .mobile-view 类，将网格变为 1 列或 2 列）
     c. 双语切换按钮：[Bahasa Melayu / 中文]
   - 【严禁输出任何 BREAKING 走马灯或即时滚动条】！既然是24小时深度晨报，绝不放任何滚动走马灯。

2. 今日头条与沙巴要闻（采用双排多宫格布局，必须完整收录以下全部 15 篇新闻，不可擅自删减）：
   【最顶层全宽特大头条】：
   - 【沙巴基建】沙巴首长哈芝芝宣布联邦发展支出提速达 71.78%，291项工程竣工交付（涵盖亚庇科学中学及兵南邦新校舍）。
   
   【以下 14 篇采用双排多宫格（Grid 2列）整齐依次向下排列】：
   1. 【沙巴治安】东安局（ESSCOM）古纳海陆大突击扣10人，开罚与充公逾 26.9 万令吉。
   2. 【科技外资】软银孙正义敲定 2040 亿令吉投资，选中古晋与西马发展 AI 与绿色数据中心。
   3. 【跨境金融】马银行 MAE / DuitNow 整合 Alipay+，免换汇扫码直通中港韩菲老五地。
   4. 【商业电信】明讯（Maxis）与 U Mobile 重启合并洽谈，拟打造全马最大电信集团。
   5. 【政府防骗】税收局（LHDN）发紧急警示：警惕冒充内陆税收局钓鱼邮件骗取个人文件。
   6. 【民生福利】2027 年 STR 援助金审核收紧，名下有车有房等 8 种情况恐遭拒批。
   7. 【节日教育】教育部官宣屠妖节假期：除砂拉越外全马中小学师生连休 4 天。
   8. 【天气警报】东北季候风 10 月 27 日来袭，气象局预测 5 次长命雨恐致多州水灾。
   9. 【商业焦点】华阳茶室菜单风波后于吉打首开新店，推三语菜单迎客现场大排长龙。
   10. 【公共卫生】卫生部推 MyLapor 官方举报指南，通过 MySejahtera 拍照检举违规抽烟。
   11. 【法治严打】槟警拘捕擅自驾驶贴上山寨“Bomba”消拯局标识与警灯的私家车司机。
   12. 【沙巴生活】Sazarice 联手 Kupikupifm 推出《Jom Cari Momom》探寻亚庇与哥隆邦在地美食。
   13. 【砂州突发】西连 32 哩中华公学男厕惊现男子昏迷死亡案，消拯队与警方介入。
   14. 【科技创新】大马开发者打造免下载网页导航 Lapan，开浏览器即用。

3. 每张新闻卡片规范：
   - 标题文字本身必须为深红色 (#dc2626)。
   - 绝不使用外部图片外链！每条新闻顶部内嵌色彩饱满、具象写实的【SVG 矢量场景插画】（神山、巡逻艇、芯片算力、扫码手机、基站、税收天平等）。
   - 卡片表面保留 2 行导读，配有「展开阅读全文 ↓ / 收起全文 ↑」折叠功能。

4. 未来两周至一个月 · 沙巴商业、展销与慈善活动预告（独立多宫格板块）：
   - 亚庇 SICC：BIGSABAH Sale 2026 年度大型经贸展销盛会（逾650个品牌展位）。
   - 亚庇 SICC：Borneo 4by4 户外越野与汽车文化节（CULT Festival）。
   - 山打根：2026年依罗普拉慈善马拉松博览会（Elopura Charity Run 2026，为期3天健康博览会）。

5. 商业赞助（固定置于全网页最下方）：
   - MY CAR ENTERPRISE · 山打根租车与接送服务（Marco: 010-9301117 / WeChat: Thien1117）。

所有文字必须配备 data-zh 与 data-bm 属性，支持一键切换马来文。
只输出 <!DOCTYPE html> 开头到 </html> 结尾的代码，不带 markdown 代码块标记。
"""

models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash"]
response = None

for model_name in models_to_try:
    for attempt in range(3):
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
    raise RuntimeError("所有模型重试后仍繁忙，请稍后再试。")

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

print("西门日报全量 15 篇新闻与活动预告已自动编译完成！")
