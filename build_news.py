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
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

prompt = f"""
你是一名沙巴与全马权威新闻主编。请为《西门日报 / Berita Harian Simon》生成一份完整、高质量、可直接运行的单文件 index.html 代码。
今日日期：{date_str} · {weekday_str}。

【版面四大核心板块硬性要求】：

1. 顶部通栏（固定吸顶）：
   - 报头《西门日报 / BERITA HARIAN SIMON》。
   - 右上角包含：历史日期下拉框 [📅 今日：{date_str} | 📅 昨天 | 📅 前天]、双语切换按钮 [Bahasa Melayu / 中文]。
   - 【严禁输出任何 BREAKING 走马灯或即时滚动条】。

2. 今日头条与沙巴要闻（手机与电脑端全量双列多宫格，大幅减少滑动）：
   - CSS 网格：.news-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }}
   - 【顶层特大头条 (grid-column: 1 / -1)】：哈芝芝证实联邦开销达 71.78%，291项工程竣工交付。
   - 【双列多宫格新闻卡片（不强制每篇都有图，动静结合）】：
     * 【精选配图卡片】：针对有震撼画面或重要素材的新闻（如古纳 ESSCOM 海陆大突击、软银 2040 亿算力中心、马银行 MAE 扫码通五地、假 Bomba 司机落网），卡片顶部内嵌简洁色彩明快的 SVG 场景图，并在图片底部叠加一层半透明黑底来源角标（例如：📷 来源：ESSCOM 官方通报 / 诗华日报 / 星洲日报），带「📤 分享」小按钮。
     * 【纯文本紧凑卡片】：针对政策通告类（LHDN 防骗、STR 援助金、学校假期、天气长命雨、MyLapor 卫生部检举），不强行配图，直接以深红标题呈现，极致节省版面高度。
   - 【手机端极简浏览体验】：卡片表面默认只显示深红标题（color: #dc2626）和分类小标签，完整正文收在隐藏容器中，每张卡片下方带有「展开阅读全文 ↓ / 收起全文 ↑」按钮，按需展开。
   - 必须涵盖昨日全量资讯（古纳突击、软银投资、马银行、明讯合并、LHDN防骗、STR、假期、天气、茶室、抽烟检举、假消防车、Sazarice探店等）。

3. 未来两周至一个月 · 沙巴商业、展销与慈善活动预告（强化电话、WhatsApp 与外链通道）：
   独立多宫格专区，每个活动卡片下方必须带有点击即可互动的【联系与报名按钮】：
   - 【活动 1】亚庇 SICC：BIGSABAH Sale 2026 年度大型展销盛会（11月13日-15日）
     * 附带拨打电话 <a href="tel:088206000">📞 088-206000</a> 与 WhatsApp 直达咨询 <a href="https://wa.me/60168332118">💬 官方 WhatsApp</a>
   - 【活动 2】亚庇 SICC：Borneo 4by4 户外越野与汽车文化节（11月20日-22日）
     * 附带组委会热线 <a href="tel:0198812399">📞 019-8812399</a> 与参展通道
   - 【活动 3】山打根：2026年依罗普拉慈善长跑与健康博览会（11月29日 · 市议会广场）
     * 附带报名专线 <a href="tel:089221144">📞 089-221144</a> 与 WhatsApp: 010-9301117

4. 商业赞助（固定置于全网页最下方）：
   - MY CAR ENTERPRISE · 山打根专业租车与专车接送（Sandakan Car Rental Service）
   - 负责人：Marco（热线 010-9301117 / 微信 Thien1117 / WhatsApp: https://www.wasap.my/60109301117）。

所有文字配备 data-zh 与 data-bm 属性，支持一键切换马来文。
只输出完整 <!DOCTYPE html> 开头到 </html> 结尾代码，不带任何 markdown 代码块标记。
"""

# 严格使用官方当前唯一主力模型 gemini-3.8-flash，增加 4 次指数避让重试应对 503 高峰
target_model = "gemini-3.8-flash"
response = None

for attempt in range(4):
    try:
        print(f"尝试使用官方模型 {target_model} (第 {attempt+1} 次)...")
        response = client.models.generate_content(
            model=target_model,
            contents=prompt
        )
        if response and response.text:
            break
    except Exception as e:
        wait_seconds = (attempt + 1) * 8
        print(f"服务器高峰波动 ({e})，正在等待 {wait_seconds} 秒后重试...")
        time.sleep(wait_seconds)

if not response or not response.text:
    raise RuntimeError("模型在多次重试后仍然繁忙，请稍后再试。")

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

print("西门日报已顺利完成编译并成功写入 index.html！")
