import os
import datetime
import requests
from google import genai

# 获取环境变量
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 获取今天的真实日期
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")

# 初始化 Gemini 客户端
client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
注意：今天的准确日期是 {today_str}。请严格基于这个日期搜寻新闻与商业活动预告！

请帮我整理过去24小时来自 Facebook 官方粉专及各大日报（如《星洲日报沙巴》、《自由日报》、《诗华日报》、《Daily Express》等）的沙巴（特别是山打根）本地与全马头条新闻及商业活动资讯。

详细要求如下：
1. 📰 新闻头条：
   - 必须包含各大日报的最新头条新闻。
   - 每条新闻总结核心要点（根据内容丰富程度提供 100 至 200 字以内摘要）。
   - 每条新闻附带一段供 AI 生图使用的【黑白线稿新闻插图 Prompt】（Editorial Black and White Sketch Prompt）。

2. 💼 本地商业活动预告（Sabah & Sandakan）：
   - 仅整理未来两周至一个月内（从 {today_str} 开始计算）即将举办的重点商业活动、展销会、行业论坛或政商会议预告。

3. 格式要求：
   - 必须在顶部明确标注更新日期为：{today_str}（禁止出现 2024 年等过期年份）。
   - 适合 Telegram 阅读的 Markdown 格式，结构紧凑清晰。
"""

# 调用最新的 gemini-3.8-flash 模型
response = client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt
)
text_content = response.text

# 发送到 Telegram
tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": text_content,
    "parse_mode": "Markdown"
}

res = requests.post(tg_url, json=payload)
print("Telegram 响应状态码:", res.status_code)
print("新闻已成功发送至 Telegram！")
