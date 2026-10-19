import os
import datetime
import requests
from google import genai

# 获取环境变量
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 获取系统当前日期
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")

# 初始化 Gemini 客户端
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
请帮我整理一份今天（{today_str}）的沙巴（特别是山打根）本地与全马头条新闻摘要及未来商业活动预告简报。

要求如下：
1. 📰 新闻头条（沙巴/山打根/全马）：
   - 梳理目前沙巴（尤其是山打根）及全马各大媒体（如《星洲日报沙巴》、《自由日报》、《诗华日报》、《Daily Express》等）关注的核心焦点政经与民生新闻。
   - 每条新闻提供 100 至 200 字以内的核心要点总结。
   - 绝不要包含任何 AI 生图 Prompt 或黑白画图描述。

2. 💼 本地商业活动预告（Sabah & Sandakan）：
   - 整理近期至未来一个月内沙巴及山打根重点即将举办或预告的商业活动、展销会、行业论坛或政商会议。

3. 🌐 官方新闻直达链接：
   - 在简报底部附上各大官方日报（星洲沙巴、诗华日报、自由日报、Daily Express）及山打根商会的官方入口链接，方便查阅现场原图。

4. 格式：
   - 顶部明确标注：📅 每日新闻简报 | {today_str}。
   - 适合 Telegram 阅读的 Markdown 格式，排版紧凑。
"""

# 调用稳定版模型
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt
)
text_content = response.text

# 发送到 Telegram
tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": text_content,
    "parse_mode": "Markdown",
    "disable_web_page_preview": True
}

res = requests.post(tg_url, json=payload)
print("Telegram 响应状态码:", res.status_code)
print("新闻已成功发送至 Telegram！")
