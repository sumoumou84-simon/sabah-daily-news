import os
import datetime
import requests
from google import genai
from google.genai import types

# 获取环境变量
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 获取系统当前真实日期
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")

# 初始化 Gemini 客户端
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
注意：今天的准确日期是 {today_str}。请使用 Google 搜索实时抓取今天最新的沙巴与全马头条！

请帮我整理过去 24 小时来自 Facebook 官方粉专及各大日报（如《星洲日报沙巴》、《自由日报》、《诗华日报》、《Daily Express》等）的沙巴（特别是山打根）本地与全马头条新闻及商业活动资讯。

详细要求如下：
1. 📰 新闻头条（沙巴/山打根/全马）：
   - 必须包含各大日报/FB粉专的最新头条新闻。
   - 每条新闻总结核心要点（100 至 200 字以内摘要）。
   - 每条新闻结尾需尽量给出文章链接，方便阅读全文。
   - 绝不要包含任何 AI 生图 Prompt 或黑白画图描述。

2. 💼 本地商业活动预告（Sabah & Sandakan）：
   - 仅整理未来两周至一个月内即将举办的重点商业活动、展销会、行业论坛或政商会议预告。

3. 格式要求：
   - 顶部明确标注：📅 每日新闻简报 | {today_str}。
   - 适合 Telegram 阅读的 Markdown 格式，排版紧凑。
"""

# 调用最新的 gemini-3.8-flash 模型，并开启实时联网搜索扩展
response = client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt,
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
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
