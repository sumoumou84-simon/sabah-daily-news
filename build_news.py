import os
import time
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

【版面四大核心板块规范】：
1. 顶部通栏与即时资讯走马灯：
   - 包含报头、日期、[中文 / BM 一键切换] 按钮，以及滚动要闻走马灯。
2. 今日头条与沙巴要闻：
   - 整合沙巴星洲日报、自由日报、诗华日报、Daily Express过去24小时沙巴重大基建、民生政策、突发交通/事故。
   - 标题必须为深红色 (#dc2626)。
   - 绝不使用外部网络容易被墙的图片外链，每篇新闻顶部内嵌高质感具象场景【SVG 矢量插画】。
   - 采用折叠结构：卡片表面2-3行导读，点击「展开阅读全文 ↓ / 收起全文 ↑」展开深度长文。
3. 【核心刚性板块】未来两周至一个月 · 沙巴商业、展销与慈善活动预告 (Upcoming Events Forecast)：
   - 严禁回顾过去！必须专门预告未来 2 周至 1 个月即将在沙巴举行的重要商业展销、商会论坛、慈善公益或大型体育活动。
   - 涵盖亚庇 SICC（如 BIGSABAH Sale 大型展销会、创业展会等）与山打根在地（如依罗普拉慈善马拉松 Elopura Marathon、商展等）及全州性公益慈善行动。
   - 每项活动标明日历日期徽章、具体地点（亚庇 SICC / 山打根体育场等）、活动亮点与报名/参与信息，并配有日历/展会微缩场景矢量插图。
4. 商业赞助（必须固定在全网页最下方）：
   - 商户：MY CAR ENTERPRISE（山打根租车与接送服务 / Sandakan Car Rental Service）
   - 内容：自驾与专职司机接送，涵盖车型（K-Car: Myvi/Axia, Sedan: Vios/Saga/Bezza, MPV: Vellfire/Alphard/Innova/Alza, 货车客运: Van 11-12座, 4x4 Hilux）。
   - 联络方式：Marco（电话 010-9301117，微信号 Thien1117，带 WhatsApp 快速联络链接 https://www.wasap.my/60109301117）。

所有文字（要闻、活动预告、广告）必须均有 data-zh 与 data-bm 属性，支持右上角一键秒切马来文。
只输出完整的 <!DOCTYPE html> 开头到 </html> 结尾代码，不要包含任何 markdown 解释或多余文字。
"""

# 模型候选列表与自动重试策略
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

print("西门日报已自动编译完成并成功写入 index.html！")
