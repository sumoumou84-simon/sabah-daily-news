import json
import os
import re
import time
import base64
import urllib.request
import urllib.error
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DRAFT_FILE = "pending_drafts.json"
NEWS_FILE = "news_data.json"
TARGET_COUNT = 8

def fetch_image_base64(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return base64.b64encode(resp.read()).decode("utf-8")
    except Exception as e:
        print(f"⚠️ 下载素材图片失败: {e}")
        return ""

def call_gemini_multimodal(contents_parts: list) -> str:
    # 备选模型列表，遇 503 自动平滑切换
    candidate_models = [
        "gemini-3.8-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash"
    ]
    
    last_err = None
    for model_name in candidate_models:
        print(f"🔄 尝试通过模型节点 [{model_name}] 编排出刊...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": contents_parts}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        data = json.dumps(payload).encode("utf-8")
        
        for attempt in range(1, 3):
            try:
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=180) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    if text:
                        return text
            except urllib.error.HTTPError as e:
                last_err = e
                print(f"⚠️ 节点 [{model_name}] 第 {attempt} 次遇到 HTTP {e.code}: {e.reason}")
                time.sleep(attempt * 3)
            except Exception as e:
                last_err = e
                print(f"⚠️ 节点 [{model_name}] 发生异常: {e}")
                time.sleep(3)
                
    raise RuntimeError(f"所有可用 AI 节点均处于繁忙状态: {last_err}")

def main():
    if not GEMINI_API_KEY:
        raise ValueError("未检测到 GEMINI_API_KEY。")

    drafts = []
    if os.path.exists(DRAFT_FILE):
        try:
            with open(DRAFT_FILE, "r", encoding="utf-8") as f:
                drafts = json.load(f)
        except Exception as e:
            print(f"读取草稿失败: {e}")

    today_str = datetime.now().strftime("%Y年%m月%d日")
    print(f"[{today_str}] 收集到 {len(drafts)} 张用户素材截图，准备出刊。")

    contents_parts = []
    prompt_text = f"""
你现在是沙巴数字晨报《西门日报》（Berita Harian Simon）的总编辑。
今天是 {today_str}。
请结合附件中用户投稿的新闻报纸截图，生成今日正式出刊的精选要闻列表。

【总编排版与发刊规则】：
1. 提取并优先收录用户截图中的新闻，自动进行查重整合（如果多张图讲同一件事，合并为一条权威报道）。
2. 如果截图中的新闻不足 {TARGET_COUNT} 篇，请自动补充沙巴本地（亚庇、山打根、斗湖等）及全马最新时事、经济、文教或交通要闻，凑齐约 {TARGET_COUNT} 篇。
3. 挑选 1 篇最重要的沙巴本地新闻作为头条，将 "is_top" 设为 true，其余为 false。
4. 每篇必须包含严谨、地道的中马双语（标题、摘要、100-150字正文）。

请严格输出为一个合法的 JSON 数组，格式如下：
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
    contents_parts.append({"text": prompt_text})

    for d in drafts:
        if d.get("image_url"):
            b64 = fetch_image_base64(d["image_url"])
            if b64:
                contents_parts.append({
                    "inline_data": {"mime_type": "image/jpeg", "data": b64}
                })

    print("🤖 AI 主编正在识图、查重、补齐并编排早报...")
    result_text = call_gemini_multimodal(contents_parts)

    try:
        final_news = json.loads(result_text)
    except Exception:
        cleaned = re.sub(r"^```json\s*", "", result_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        final_news = json.loads(cleaned)

    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(final_news, f, ensure_ascii=False, indent=2)

    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

    print(f"🎉 今日出刊成功，共排版发布 {len(final_news)} 条要闻！")

if __name__ == "__main__":
    main()
