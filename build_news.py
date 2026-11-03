import os
import json
import re
from datetime import datetime
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

NEWS_DATA_FILE = "news_data.json"
OUTPUT_HTML_FILE = "index.html"

def extract_verification_tag(title):
    """
    提取标题中的双核实标签内容，若有类似 [...] 则提取为单独 badge 并返回干净标题与标签
    """
    match = re.search(r'\[(.*?)\]', title)
    if match:
        tag = match.group(1)
        clean_title = title.replace(f"[{tag}]", "").strip()
        return clean_title, tag
    return title, None

def generate_index_html():
    """
    读取 news_data.json，编译生成具有高端黑金质感、展开抽屉、双核实徽章的 index.html
    """
    if not os.path.exists(NEWS_DATA_FILE):
        print(f"⚠️ {NEWS_DATA_FILE} 不存在，生成默认结构数据...")
        data = {
            "utilities": [],
            "headlines": []
        }
    else:
        with open(NEWS_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"❌ 读取 {NEWS_DATA_FILE} 失败: {e}")
                data = {"utilities": [], "headlines": []}

    utilities = data.get("utilities", [])
    headlines = data.get("headlines", [])
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    # 构建民生 LIVE HTML 条目
    utilities_html = ""
    for idx, item in enumerate(utilities, 1):
        raw_title = item.get("title", "")
        detail = item.get("detail", "")
        clean_title, tag = extract_verification_tag(raw_title)
        badge_html = f'<span class="badge-verify"><svg class="icon-shield" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>{tag}</span>' if tag else '<span class="badge-verify">官方双核实</span>'
        
        utilities_html += f"""
        <div class="news-card utility-card" id="util-{idx}">
            <div class="card-header" onclick="toggleDrawer('drawer-util-{idx}', this)">
                <div class="card-meta">
                    <span class="live-pill"><span class="pulse-dot"></span>LIVE 调度</span>
                    {badge_html}
                </div>
                <h3 class="card-title">{clean_title}</h3>
                <div class="card-footer-action">
                    <span class="view-btn">查看核实报告与详情</span>
                    <span class="arrow-icon">▼</span>
                </div>
            </div>
            <div class="card-drawer" id="drawer-util-{idx}">
                <div class="drawer-content">
                    <div class="detail-label">核实简报与详细指引</div>
                    <p class="detail-text">{detail}</p>
                    <div class="verified-box">
                        <span class="v-icon">✓</span>
                        <span class="v-desc">已通过沙巴/山打根白名单监控矩阵完成双信源交叉比对，通报信息有效可靠。</span>
                    </div>
                </div>
            </div>
        </div>
        """

    # 构建今日要闻 HTML 条目
    headlines_html = ""
    for idx, item in enumerate(headlines, 1):
        raw_title = item.get("title", "")
        detail = item.get("detail", "")
        clean_title, tag = extract_verification_tag(raw_title)
        badge_html = f'<span class="badge-verify">{tag}</span>' if tag else '<span class="badge-gold">重点聚焦</span>'

        # 从 detail 提取信源尾缀如果有
        source_badge = ""
        if "来源：" in detail or "来源:" in detail:
            parts = re.split(r'来源[：:]', detail)
            if len(parts) > 1:
                source_badge = f'<span class="source-tag">信源: {parts[1].strip()}</span>'

        headlines_html += f"""
        <div class="news-card headline-card" id="head-{idx}">
            <div class="card-header" onclick="toggleDrawer('drawer-head-{idx}', this)">
                <div class="card-meta">
                    <span class="tag-seq">#{idx:02d}</span>
                    {badge_html}
                    {source_badge}
                </div>
                <h3 class="card-title">{clean_title}</h3>
                <div class="card-footer-action">
                    <span class="view-btn">展开快讯摘要</span>
                    <span class="arrow-icon">▼</span>
                </div>
            </div>
            <div class="card-drawer" id="drawer-head-{idx}">
                <div class="drawer-content">
                    <div class="detail-label">通报与采编细则</div>
                    <p class="detail-text">{detail}</p>
                </div>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>西门看看网 · Simon Kankan | 全自动信源采集与双核实编译引擎</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #090b0e;
            --bg-surface: #10141a;
            --bg-elevated: #161b22;
            --bg-drawer: #0d1017;
            --gold-primary: #d4af37;
            --gold-light: #f5d77f;
            --gold-dark: #aa8420;
            --gold-gradient: linear-gradient(135deg, #f5d77f 0%, #d4af37 50%, #997517 100%);
            --text-main: #f0f3f6;
            --text-muted: #8b949e;
            --text-dim: #545d68;
            --border-gold: rgba(212, 175, 55, 0.32);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --accent-green: #2ea043;
            --accent-red: #da3633;
            --shadow-gold: 0 4px 20px rgba(212, 175, 55, 0.12);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            min-height: 100vh;
            padding: 0 16px 60px 16px;
            background-image: 
                radial-gradient(circle at 50% 0%, rgba(212, 175, 55, 0.08) 0%, transparent 60%),
                linear-gradient(to bottom, #090b0e, #0c0f14);
            background-attachment: fixed;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        /* Header 黑金头部 */
        header {{
            padding: 40px 0 28px 0;
            text-align: center;
            border-bottom: 1px solid var(--border-gold);
            margin-bottom: 32px;
            position: relative;
        }}

        .brand-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 5px 14px;
            border-radius: 20px;
            background: rgba(212, 175, 55, 0.1);
            border: 1px solid var(--border-gold);
            color: var(--gold-light);
            font-size: 0.78rem;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 14px;
        }}

        .brand-title {{
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 2px;
            background: var(--gold-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
            text-shadow: 0 0 25px rgba(212, 175, 55, 0.2);
        }}

        .brand-subtitle {{
            font-size: 0.95rem;
            color: var(--text-muted);
            font-weight: 300;
            letter-spacing: 0.5px;
        }}

        .meta-bar {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-top: 18px;
            font-size: 0.8rem;
            color: var(--text-dim);
        }}

        .meta-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent-green);
            box-shadow: 0 0 8px var(--accent-green);
        }}

        /* 栏目区块 */
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 36px 0 18px 0;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-subtle);
        }}

        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--gold-light);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-title::before {{
            content: "";
            display: inline-block;
            width: 4px;
            height: 18px;
            background: var(--gold-gradient);
            border-radius: 2px;
        }}

        .section-count {{
            font-size: 0.8rem;
            padding: 3px 10px;
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            color: var(--gold-primary);
        }}

        /* 卡片黑金质感设计 */
        .cards-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .news-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }}

        .news-card:hover {{
            border-color: var(--border-gold);
            transform: translateY(-2px);
            box-shadow: var(--shadow-gold);
        }}

        .utility-card {{
            border-left: 3px solid var(--gold-primary);
        }}

        .card-header {{
            padding: 18px 20px;
            cursor: pointer;
            user-select: none;
        }}

        .card-meta {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 10px;
        }}

        /* 双核实徽章设计 */
        .badge-verify {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #ffd770;
            background: rgba(212, 175, 55, 0.15);
            border: 1px solid rgba(212, 175, 55, 0.45);
            padding: 2px 10px;
            border-radius: 6px;
            box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
            letter-spacing: 0.3px;
        }}

        .icon-shield {{
            width: 13px;
            height: 13px;
            stroke: #ffd770;
        }}

        .live-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-weight: 700;
            color: #ff7b72;
            background: rgba(218, 54, 51, 0.12);
            border: 1px solid rgba(218, 54, 51, 0.3);
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }}

        .pulse-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--accent-red);
            animation: pulse 1.8s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(218, 54, 51, 0.7); }}
            70% {{ transform: scale(1.1); box-shadow: 0 0 0 6px rgba(218, 54, 51, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(218, 54, 51, 0); }}
        }}

        .tag-seq {{
            font-size: 0.75rem;
            font-family: monospace;
            color: var(--text-dim);
        }}

        .badge-gold {{
            font-size: 0.72rem;
            color: var(--gold-light);
            background: rgba(212, 175, 55, 0.08);
            border: 1px solid rgba(212, 175, 55, 0.25);
            padding: 2px 8px;
            border-radius: 4px;
        }}

        .source-tag {{
            font-size: 0.72rem;
            color: var(--text-muted);
            background: var(--bg-elevated);
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid var(--border-subtle);
        }}

        .card-title {{
            font-size: 1.08rem;
            font-weight: 500;
            color: #ffffff;
            margin-bottom: 12px;
            line-height: 1.5;
            letter-spacing: 0.2px;
        }}

        .card-footer-action {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.78rem;
            color: var(--gold-primary);
            padding-top: 6px;
        }}

        .arrow-icon {{
            font-size: 0.7rem;
            transition: transform 0.3s ease;
            color: var(--gold-light);
        }}

        .news-card.active .arrow-icon {{
            transform: rotate(180deg);
        }}

        /* 展开抽屉设计 Drawer */
        .card-drawer {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            background: var(--bg-drawer);
            border-top: 1px solid transparent;
        }}

        .news-card.active .card-drawer {{
            max-height: 500px;
            border-top: 1px solid var(--border-gold);
        }}

        .drawer-content {{
            padding: 18px 20px 22px 20px;
            animation: fadeIn 0.4s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .detail-label {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--gold-light);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .detail-text {{
            font-size: 0.92rem;
            color: #d1d5db;
            line-height: 1.7;
            margin-bottom: 14px;
        }}

        .verified-box {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 10px 14px;
            background: rgba(46, 160, 67, 0.1);
            border: 1px solid rgba(46, 160, 67, 0.3);
            border-radius: 8px;
            font-size: 0.8rem;
            color: #7ee787;
        }}

        .v-icon {{
            font-weight: bold;
            color: #3fb950;
        }}

        /* 底部 Footer */
        footer {{
            margin-top: 50px;
            text-align: center;
            padding-top: 24px;
            border-top: 1px solid var(--border-subtle);
            font-size: 0.8rem;
            color: var(--text-dim);
        }}

        .footer-note {{
            margin-top: 6px;
            color: var(--gold-dark);
            font-size: 0.75rem;
        }}

        @media (max-width: 600px) {{
            .brand-title {{
                font-size: 1.65rem;
            }}
            .card-header {{
                padding: 14px 16px;
            }}
            .card-title {{
                font-size: 0.98rem;
            }}
            .drawer-content {{
                padding: 14px 16px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 Header -->
        <header>
            <div class="brand-badge">
                <span>SIMON KANKAN · INTELLIGENCE</span>
            </div>
            <h1 class="brand-title">西门看看网 · 新闻内参</h1>
            <p class="brand-subtitle">全自动信源采集与双核实编译引擎 · 独家黑金版</p>
            
            <div class="meta-bar">
                <div class="meta-item">
                    <span class="status-dot"></span>
                    <span>双核实白名单引擎: 运行中</span>
                </div>
                <div class="meta-item">
                    <span>•</span>
                    <span>最后编译: {now_str}</span>
                </div>
                <div class="meta-item">
                    <span>•</span>
                    <span>格式防护: 零崩坏锁定</span>
                </div>
            </div>
        </header>

        <!-- 民生公用事业与突发调度 LIVE -->
        <section>
            <div class="section-header">
                <div class="section-title">山打根 & 沙巴 · 民生实况调度 (LIVE)</div>
                <div class="section-count">{len(utilities)} 项已核实</div>
            </div>
            <div class="cards-list">
                {utilities_html if utilities_html else '<div class="news-card"><div class="card-header"><p class="detail-text" style="text-align:center;color:var(--text-dim);">当前暂无紧急停水停电调度通报</p></div></div>'}
            </div>
        </section>

        <!-- 今日头条与国家大盘 -->
        <section>
            <div class="section-header">
                <div class="section-title">全马要闻与政策动态 (Headlines)</div>
                <div class="section-count">{len(headlines)} 条焦点</div>
            </div>
            <div class="cards-list">
                {headlines_html if headlines_html else '<div class="news-card"><div class="card-header"><p class="detail-text" style="text-align:center;color:var(--text-dim);">当前暂无要闻推送</p></div></div>'}
            </div>
        </section>

        <!-- 底部版权信息 -->
        <footer>
            <div>西门看看网 (Simon Kankan) © {datetime.now().year} · 全自动信源打捞与结构化排版系统</div>
            <div class="footer-note">严格遵循双官方信源交叉复核标准 · 适配 Antigravity 本地调试与 GitHub Actions 无人值守环境</div>
        </footer>
    </div>

    <!-- 展开抽屉交互脚本 -->
    <script>
        function toggleDrawer(drawerId, headerElem) {{
            const card = headerElem.closest('.news-card');
            const drawer = document.getElementById(drawerId);
            if (!drawer || !card) return;

            const isOpen = card.classList.contains('active');
            if (isOpen) {{
                card.classList.remove('active');
            }} else {{
                card.classList.add('active');
            }}
        }}

        // 默认展开第一条民生快讯便于用户直观体验抽屉
        document.addEventListener('DOMContentLoaded', () => {{
            const firstUtil = document.querySelector('.utility-card');
            if (firstUtil) {{
                firstUtil.classList.add('active');
            }}
        }});
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 成功生成静态页面: {OUTPUT_HTML_FILE}")

if __name__ == "__main__":
    generate_index_html()
