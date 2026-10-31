import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime

# ====== 配置区 ======
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DRAFT_FILE = "pending_drafts.json"
NEWS_FILE = "news_data.json"
TARGET_COUNT = 8  # 保持每日 8-10 篇黄金阅读量，生成速度快且不超时

def call_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    data = json.dumps(payload).encode("utf-8")
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            # 放宽超时时间到 180 秒，防止长文本生成被打断
            with urllib.request.urlopen(req, timeout=180) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            print(f"⚠️ 第 {attempt} 次请求遭遇 HTTP {e.code}: {e.reason}")
            if attempt < max_retries:
                time.sleep(attempt * 4)
            else:
                raise e
        except Exception as e:
            print(f"⚠️ 请求异常: {e}")
            if attempt < max_retries:
                time.sleep(5)
            else:
                raise e

def main():
    if not GEMINI_API_KEY:
        raise ValueError("未检测到环境变量 GEMINI_API_KEY，请在 GitHub Secrets 中配置。")

    # 1. 读取 Telegram 积攒的草稿
    drafts = []
    if os.path.exists(DRAFT_FILE):
        try:
            with open(DRAFT_FILE, "r", encoding="utf-8") as f:
                drafts = json.load(f)
        except Exception as e:
            print(f"⚠️ 读取草稿箱异常: {e}")

    draft_count = len(drafts)
    today_str = datetime.now().strftime("%Y年%m月%d日")
    print(f"[{today_str}] 草稿池当前共有 {draft_count} 篇用户投递素材。")

    # 2. 构建精炼提示词（精简正文至 100-150 字，极大提升生成速度并防止超时）
    prompt = f"""
你现在是沙巴数字晨报《西门日报》（Berita Harian Simon）的总编辑。
今天是 {today_str}。你需要为今天的晨报生成最终正式发布的新闻列表。

【已收集的用户投递草稿素材】（数量：{draft_count}）：
{json.dumps(drafts, ensure_ascii=False, indent=2)}

【总编排版与发刊规则】：
1. 用户投递的新闻优先收录并做事实查重；不足 {TARGET_COUNT} 篇时，自动补充沙巴本地（亚庇、山打根、斗湖等）及全马最新时事经济文教要闻，凑齐约 {TARGET_COUNT} 篇。
2. 必须挑 1 篇最具社会影响力的沙巴要闻作为头条，将 "is_top" 设为 true，其余为 false。
3. 中马双语输出：每篇包含中文与马来文的标题、摘要、精炼正文（100-150字，语言干练地道）。

请严格输出为一个纯 JSON 数组，格式如下：
[
  {{
    "is_top": true,
    "source": "媒体来源 (如 诗华日报 / 沙巴星洲日报 / 自由日报)",
    "tag_zh": "沙巴交通",
    "tag_bm": "Trafik Sabah",
    "title_zh": "【中文分类】主标题",
    "title_bm": "Tajuk Berita Bahasa Melayu",
    "excerpt_zh": "中文导语摘要 (30字左右)",
    "excerpt_bm": "Ringkasan Berita Bahasa Melayu",
    "content_zh": "新闻精炼正文 (100-150字)",
    "content_bm": "Kandungan Berita Bahasa Melayu (100-150 patah perkataan)",
    "image_url": ""
  }}
]
"""

    print("🤖 正在调用 AI 主编进行查重、补全与双语排版...")
    result_text = call_gemini(prompt)

    try:
        final_news = json.loads(result_text)
    except Exception:
        cleaned = re.sub(r"^```json\s*", "", result_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        final_news = json.loads(cleaned)

    print(f"✅ 今日《西门日报》编排完成，共刊发 {len(final_news)} 条要闻！")

    # 3. 写入正式发布文件 news_data.json
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(final_news, f, ensure_ascii=False, indent=2)

    # 4. 清空草稿池
    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

    print("📦 已更新 news_data.json，并清空 pending_drafts.json。")

if __name__ == "__main__":
    main()
