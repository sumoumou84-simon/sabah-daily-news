import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime

# ====== 配置区 ======
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DRAFT_FILE = "pending_drafts.json"
NEWS_FILE = "news_data.json"
TARGET_COUNT = 12  # 每日早报目标篇数（建议 10 - 15 篇）

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
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        return res_json["candidates"][0]["content"]["parts"][0]["text"]

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

    # 2. 构建发刊提示词（方案 A：去重、补齐、提炼头条、中马双语排版）
    prompt = f"""
你现在是沙巴顶尖数字晨报《西门日报》（Berita Harian Simon）的总编辑。
今天是 {today_str}。你需要为今天的晨报生成最终正式发布的新闻列表。

【已收集的用户投递草稿素材】（数量：{draft_count}）：
{json.dumps(drafts, ensure_ascii=False, indent=2)}

【总编排版与发刊规则】：
1. **用户投递优先**：优先采用用户投递的新闻，并对其进行智能排重。如果同一事件有多张截图或多条报道，合并提炼为一条事实最完整、最权威的报道。
2. **AI 智能补位**：
   - 如果用户草稿不足 {TARGET_COUNT} 篇，请作为主编自动检索/补充沙巴本地（优先亚庇、山打根、斗湖等）及全马的重大时事、经济、文教或交通要闻，将新闻总数补齐至约 {TARGET_COUNT} 篇。
   - 如果用户草稿已经达到或超过 {TARGET_COUNT} 篇，则严格在现有草稿中进行合并精简，无需补充额外新闻。
3. **今日头条甄选**：
   - 必须挑选 1 篇最具社会影响力或公众关注度的沙巴本地新闻作为今日头条，将其 "is_top" 设为 true，其余为 false。
4. **中马双语与质量要求**：
   - 每篇新闻必须包含严谨、地道的中马双语（标题、导语摘要、150-250字的完整正文）。
   - 保持分类标签贴切（如：沙巴要闻、沙巴交通、沙巴治安、东马商业、民生民情、全马热点等）。

请严格输出为一个合法的 JSON 数组，数组中的每个元素格式如下：
[
  {{
    "is_top": true,
    "source": "媒体来源 (如 诗华日报 / 沙巴星洲日报 / 自由日报 / Daily Express)",
    "tag_zh": "沙巴交通",
    "tag_bm": "Trafik Sabah",
    "title_zh": "【中文分类】主标题",
    "title_bm": "Tajuk Berita Bahasa Melayu",
    "excerpt_zh": "中文导语摘要 (30字左右)",
    "excerpt_bm": "Ringkasan Berita Bahasa Melayu",
    "content_zh": "完整新闻正文 (150-250字)",
    "content_bm": "Kandungan Penuh Berita Bahasa Melayu",
    "image_url": "可选图片链接（如果草稿有则保留，没有可为空字符串）"
  }}
]
"""

    print("🤖 正在调用 AI 主编进行查重、补全与双语排版...")
    result_text = call_gemini(prompt)

    try:
        final_news = json.loads(result_text)
    except Exception:
        # 清理可能附带的 markdown 包裹
        cleaned = re.sub(r"^```json\s*", "", result_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        final_news = json.loads(cleaned)

    print(f"✅ 今日《西门日报》编排完成，共刊发 {len(final_news)} 条要闻！")

    # 3. 写入正式发布文件 news_data.json
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(final_news, f, ensure_ascii=False, indent=2)

    # 4. 清空草稿池，为新一天的收集做准备
    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

    print("📦 已更新 news_data.json，并清空 pending_drafts.json。")

if __name__ == "__main__":
    main()
