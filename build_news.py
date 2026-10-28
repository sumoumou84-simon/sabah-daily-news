import os
import datetime
from google import genai

# 获取环境变量中的 API KEY
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("未找到 GEMINI_API_KEY 密钥！")

client = genai.Client(api_key=api_key)

# 获取马来西亚当前时间
my_tz = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(my_tz)
date_str = now.strftime("%Y年%m月%d日")
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

prompt = f"""
你是一名沙巴与全马权威新闻主编。请为《西门日报 / Berita Harian Simon》生成一份完整、高质量、可直接在浏览器运行的单文件 index.html 代码。
今日日期：{date_str} · {weekday_str}。

【硬性要求】：
1. 核心新闻源覆盖：沙巴星洲日报、自由日报、诗华日报、Daily Express，整合过去24小时沙巴在地民生重大基建、突发交通/事故、政府新政策与全国热点。
2. 视觉规范：
   - 绝不使用外部网络容易被墙的图片外链！
   - 每条新闻顶部必须内嵌自适应且色彩饱满、一眼看懂的【SVG 场景矢量插画】（包含地貌、挖掘机、工程、汽车、法庭或建筑等具象元素）。
   - 标题文字本身必须为深红色 (#dc2626)，醒目大方。
3. 交互结构：
   - 每张新闻卡片提供 2-3 行导读，配有「展开阅读全文 ↓ / 收起全文 ↑」折叠功能。
   - 展开内容必须充实详尽（包含现场实况、官方数据、背景来由与后续影响）。
4. 语言支持：
   - 右上角常驻【中文 / BM 一键切换】按键，点击后秒切整份报纸（包括标题、正文、折叠内容与广告）。
5. 商业赞助（必须固定在全网页最下方）：
   - 商户：MY CAR ENTERPRISE（山打根租车与接送服务 / Sandakan Car Rental Service）
   - 内容：自驾与专职司机接送，涵盖车型（K-Car: Myvi/Axia, Sedan: Vios/Saga/Bezza, MPV: Vellfire/Alphard/Innova/Alza, 货车客运: Van 11-12座, 4x4 Hilux）。
   - 联络方式：Marco（电话 010-9301117，微信号 Thien1117，带 WhatsApp 快速联络链接 https://www.wasap.my/60109301117）。

只输出完整的 <!DOCTYPE html> 开头到 </html> 结尾代码，不要包含任何 markdown 解释或多余文字。
"""

# 使用标准 gemini-2.5-flash 模型
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

html_code = response.text.strip()

# 清理 markdown 标签
if html_code.startswith("```html"):
    html_code = html_code[7:]
if html_code.startswith("```"):
    html_code = html_code[3:]
if html_code.endswith("```"):
    html_code = html_code[:-3]

html_code = html_code.strip()

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

print("西门日报已自动编译完成并成功写入 index.html！")
