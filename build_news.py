import os
import json
import time
import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("未找到 GEMINI_API_KEY 密鑰！")

client = genai.Client(api_key=api_key)

my_tz = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(my_tz)
date_str = now.strftime("%Y年%m月%d日")
date_bm = now.strftime("%d %B %Y")
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

# 讓 AI 僅輸出純 JSON 數據，生成極快且穩定
prompt = f"""
你是一名沙巴權威新聞主編。請將今日（{date_str}）的 14 條重點新聞整理為標準 JSON 陣列。
請嚴格只輸出合法 JSON 格式，不要包含任何 markdown 標記（如 ```json）。

JSON 陣列中每個物件必須包含以下欄位：
- "tag_zh": 中文分類標籤（如：沙巴基建、治安執法、科技算力、跨境金融等）
- "tag_bm": 馬來文分類標籤
- "title_zh": 中文大標題（不超過28字）
- "title_bm": 馬來文標題
- "desc_zh": 展開後的詳細內文（100-150字）
- "desc_bm": 展開後的馬來文內文
- "source": 來源（如：Sayang Sabah / ESSCOM / 星洲日報 / 詩華日報）
- "has_img": 布林值（true 或 false，僅重要頭條或具備震撼現場的設為 true）
- "img_type": 字串（"gov", "police", "tech", "bank", "telco", "life", "warning" 之一）

必須涵蓋昨日全量重點素材：
1. 哈芝芝證實沙巴聯邦開銷達71.78%，291項工程竣工
2. ESSCOM古納海陸大突擊扣10人，開罰及充公逾26.9萬
3. 軟銀孫正義投資2040億古晉與西馬設AI數據中心
4. 馬銀行MAE整合Alipay+免換匯掃碼通中港韓菲老
5. 明訊與U Mobile重啟合併洽談組最大電訊集團
6. 稅收局LHDN急發警示防冒名釣魚郵件
7. 2027 STR援助金審核收緊，有車有房恐拒批
8. 教育部官宣屠妖節除砂拉越外師生連休4天
9. 東北季候風來襲，氣象局預測5次長命雨恐致水災
10. 華陽茶室吉打新店推三語菜單迎客大排長龍
11. 衛生部推MyLapor官方
