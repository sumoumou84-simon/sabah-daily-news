#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Phase D-3: Single API Request, Three Complete News Articles
- Uses existing candidate model: gemini-3.5-flash-lite.
- Uses existing QuotaManager for durable write-ahead reservation to origin/main.
- Feeds 3 verified, independently scraped source articles with full body text.
- Sends EXACTLY ONE HTTP request without Google Search Grounding tool (pure editorial compilation).
- If HTTP 429 or any error occurs, captures complete raw error body and metadata.
- Never retries. Never exposes API keys.
- Completely isolated from news_data.json, index.html, and website deployment.
"""

import os
import sys
import re
import json
import logging
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.synthesizer import QuotaManager, MYT_TZ

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("scripts.generate_three_articles_d3")


def mask_secret(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'(key=)[A-Za-z0-9_-]{10,}', r'\1[MASKED_SECRET]', text)


# The Three Verified Source Stories Scraped from See Hua Daily News on 2026-11-08 / 2026-11-09
SOURCE_STORIES = [
    {
        "id": "story_1_sandakan_local",
        "category": "Sandakan Municipal / Local Affairs",
        "url": "https://news.seehua.com/post/1601871/",
        "title": "沙巴地政运动会山打根开幕 携手提升市容迎接2027旅游年",
        "published_at": "2026-11-08T15:05:59+08:00",
        "publisher": "诗华日报沙巴版",
        "location": "山打根 (Sandakan) 县级综合体育馆",
        "verified_text": (
            "「第14届（2026年）沙巴州地方政府运动会（SKTS）」昨晚在山打根县级综合体育馆隆重开幕，"
            "来自州房政部和属下机构，以及全州各县市议会的8支队伍齐聚山打根，通过体育竞技促进交流和增进情谊，"
            "并加强各地方政府之间的合作关系。开幕仪式由本州地政及房屋部长拿督莫哈末阿里芬太平局绅主持，山打根市议会主席沃特肯森陪同。"
            "出席观礼嘉宾计有：山打根区国会议员黄诗怡、京那巴鲁油棕集团主席兼双溪马尼拉区州议员拿督哈泽慕沙及国会上议员拿督安娜贝儿，"
            "以及州房政部助理部长、常务秘书等相关部门高官等。\n\n"
            "仪式以触碰电子启动球掀开序幕，阿里芬随后移交大会纪念版吉祥物及纪念锦旗予各参赛队伍。当晚也安排皇家海军军鼓乐队演奏和火焰表演，"
            "本地歌手演唱和传统舞蹈表演，以及烟花秀。阿里芬致开幕词时呼吁州内各地方政府加强合作，提升各地区环境卫生、市容、吸引力及安全水平，"
            "以迎接「2027年沙巴旅游年」。他说，地方政府在旅游年筹备工作中扮演重要角色，必须团结一致和积极创新，确保各地区及城镇拥有整洁、优美和安全的环境。\n\n"
            "阿里芬较后接受媒体访问时表示，本届运动会吸引超过2000名代表团成员到访山打根，预计将带动当地一周的经济活动。"
            "山打根市议会主席沃特肯森致欢迎词时指出，本届运动会汇聚来自25个地方政府的代表团，预计可为当地酒店、餐饮及零售业带来商机。"
            "他估计，若2358名到访者每人消费1000令吉，可为山打根带来约235万8000令吉经济效益，并呼吁各参赛队伍在当地消费，支持本地商家。"
            "他也感谢阿里芬批准山打根市议会申请，允许当地低风险商业活动营业至24小时，以进一步刺激地方经济。各项赛事将持续至下周五（13日）。"
        )
    },
    {
        "id": "story_2_state_policy_infrastructure",
        "category": "Sabah State Government & Infrastructure Policy",
        "url": "https://news.seehua.com/post/1601838/",
        "title": "沙巴预算案12月4日提呈 哈芝芝：着重解决民生问题",
        "published_at": "2026-11-08T14:18:43+08:00",
        "publisher": "诗华日报沙巴版",
        "location": "亚庇 (Kota Kinabalu)",
        "verified_text": (
            "首席部长拿督斯里哈芝芝诺今日说，定于下月4日提呈的2027年沙巴财政预算案，将是一份惠及人民及推动本州发展、令人期待的预算案。\n\n"
            "他说，虽然目前不便透露预算案的具体内容，但可以肯定的是，预算案将着重解决沙巴长期面对的各种民生问题，包括水供、电力及道路设施等。"
            "“我不想在预算案提呈前透露太多，但我要强调，这将是一份对沙巴人民及本州发展有利的预算案。”\n\n"
            "哈芝芝在出席屠妖节庆典时表示，希望这个象征光明与祝福的节日，不仅为印度社群带来喜悦，也让沙巴各族群共同感受节日的欢乐与祝福。"
            "各族群不分背景共同欢庆不同节日，正是马来西亚多元社会应有的精神。“让我们继续维护这份团结精神，为大家的共同利益而努力。”\n\n"
            "较早前，哈芝芝与夫人拿汀斯里朱莉雅沙拉，在沙巴印度工商会主席拿督V. 佐迪及其他贵宾陪同下，主持切蛋糕仪式。"
            "随后，哈芝芝也代表沙巴印度工商会移交援助金予沙巴盲人协会及位于斗亚兰的Jireh儿童之家。这项庆典吸引超过1400人出席。"
            "出席者包括副首长拿督斯里邦佐津昆沙南及拿督斯里马西迪曼俊、州内阁部长、州秘书拿督再奴丁阿曼、州议员及各界社团领袖。"
        )
    },
    {
        "id": "story_3_public_interest_rural_development",
        "category": "Sabah Public-Interest / Economy & Rural Development",
        "url": "https://news.seehua.com/post/1602269/",
        "title": "沙今年18村获批昌明领养甘榜计划 穆斯达法：获900万建设基础设施",
        "published_at": "2026-11-09T10:31:40+08:00",
        "publisher": "诗华日报沙巴版",
        "location": "哥打马鲁都 (Kota Marudu) 甘榜哥隆孔 (Kampung Golongkong)",
        "verified_text": (
            "沙巴今年再有18个甘榜获得批准参与昌明领养甘榜计划（KAM），获批拨款总额达900万令吉。\n\n"
            "首相署（沙巴及砂拉越事务）部长拿督穆斯达法沙末指出，哥打马鲁都的甘榜哥隆孔是今年获批的18个甘榜之一，获得50万令吉拨款，用于提升4项基本基础设施。"
            "他说，沙巴于2025年共有11个甘榜获批参与这项计划，获得1015万令吉拨款，而2026年则有另外18个甘榜获得批准。\n\n"
            "他表示，甘榜哥隆孔利用50万令吉拨款，成功完成4项工程，包括兴建新礼堂、建设足球场、安装街灯，以及将碎石路提升为混凝土道路。"
            "“虽然拨款只有50万令吉，但领养甘榜计划管理团队成功完成4项并不简单的工程。最重要的是善用拨款，让更多基本基础设施建设得以落实。”\n\n"
            "穆斯达法在主持甘榜哥隆孔昌明领养甘榜计划竣工工程移交仪式时表示，援引财政部数据，沙巴是全国昌明领养甘榜计划申请数量最低的州属之一，"
            "但沙巴实际上比其他州属更需要获得更多拨款，以扩大这项计划的乡区发展效益。政府遴选领养甘榜时，应优先考虑仍被发展浪潮边缘化的地区，包括哥打马鲁都县部分甘榜。"
            "他希望获得提升的基础设施能够激励当地青年积极参与社区活动，并呼吁村民继续发扬团结合作精神，与政府携手推动计划。"
        )
    }
]


def build_consolidated_prompt(today_str: str) -> str:
    stories_context = []
    for i, s in enumerate(SOURCE_STORIES, 1):
        stories_context.append(
            f"=== 故事 {i}：{s['category']} ===\n"
            f"标题: {s['title']}\n"
            f"来源: {s['publisher']} ({s['url']})\n"
            f"发布时间: {s['published_at']}\n"
            f"事发地点: {s['location']}\n"
            f"真实原文素材:\n{s['verified_text']}\n"
        )
    context_block = "\n".join(stories_context)

    prompt = (
        f"今天是马来西亚时间 {today_str}。你是《西门看看网》首席资深新闻采编与翻译主任。\n"
        "以下是经人工走访核实获取的 3 篇沙巴重要新闻一手真实素材：\n\n"
        f"{context_block}\n"
        "【任务要求】\n"
        "请在单次响应中，为上述 3 篇新闻分别撰写完整的双语深度报道（中文与马来文对等）。\n"
        "必须严格遵守以下采编原则：\n"
        "1. 绝不虚构：严禁捏造未经原文提及的人名、款项金额、职务、日期、引述言论或因果结论；\n"
        "2. 篇幅充实：每篇中文完整报道 280-400 字，客观准确，段落层次分明；每篇马来文完整报道 150-250 字（Bahasa Melayu piawai），严禁敷衍略述！\n"
        "3. 明确区分：清楚区分发布日期与事件发生日期，区分已证实事实与官方尚在规划推进事项；\n"
        "4. 输出格式：必须输出合法的 JSON 数组，包含 3 个对象，格式严格如下：\n"
        "[\n"
        "  {\n"
        "    \"story_id\": 1,\n"
        "    \"category\": \"sandakan_local\",\n"
        "    \"headline_zh\": \"中文新闻主标题\",\n"
        "    \"headline_bm\": \"Tajuk Berita Bahasa Melayu\",\n"
        "    \"summary_zh\": \"中文要点摘要（2-3句话）\",\n"
        "    \"summary_bm\": \"Ringkasan Berita Bahasa Melayu\",\n"
        "    \"full_article_zh\": \"完整的中文深度报道正文（280-400字）...\",\n"
        "    \"full_article_bm\": \"Teks berita mendalam penuh Bahasa Melayu (150-250 perkataan)...\",\n"
        "    \"publication_date\": \"原文发布日期\",\n"
        "    \"event_date\": \"事件发生具体日期/时段\",\n"
        "    \"location\": \"发生地点\",\n"
        "    \"key_figures\": [\"涉及官员与重要人物名单及职位\"],\n"
        "    \"key_data_points\": [\"核心数字、拨款金额、参与人数等\"],\n"
        "    \"original_url\": \"对应原文链接\",\n"
        "    \"verified_facts\": [\"经核实核心事实清单\"],\n"
        "    \"unconfirmed_or_limitations\": \"任何受限信息或待后续落实事项\"\n"
        "  }\n"
        "]\n"
        "请直接输出合法的 JSON 数组，严禁在开头或结尾添加任何其他文本说明。"
    )
    return prompt


def run_phase_d3(
    api_key_override: Optional[str] = None,
    config_override: Optional[Dict[str, Any]] = None,
    execution_mode_override: Optional[str] = None
) -> Dict[str, Any]:
    logger.info("=================================================================")
    logger.info("📰 Sabah Daily News — Phase D-3: Single Request Three Articles Generation")
    logger.info("=================================================================")

    config_path = os.path.join(BASE_DIR, "config", "news_config.json")
    config = config_override or {}
    if not config and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    api_key = (
        api_key_override
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    ).strip()

    if not api_key:
        logger.error("[PREFLIGHT ABORT] No GEMINI_API_KEY detected in environment. Emitting 0 HTTP requests.")
        return {
            "status": "ABORTED_NO_CREDENTIALS",
            "http_requests_sent": 0,
            "quota_reserved": False,
            "detail": "Secure Gemini credential unavailable."
        }

    # 1. Quota Manager Reservation
    quota_mgr = QuotaManager(
        config=config,
        execution_mode_override=execution_mode_override
    )
    candidate_models = quota_mgr.candidate_models
    model = candidate_models[0] if candidate_models else "gemini-3.5-flash-lite"

    now_myt = datetime.now(MYT_TZ)
    today_str = now_myt.strftime("%Y-%m-%d")

    logger.info(f"Target Model:     {model}")
    logger.info(f"Execution Mode:   {quota_mgr.execution_mode}")
    logger.info(f"Current Date:     {today_str}")

    logger.info("[QUOTA GATE] Attempting durable write-ahead reservation for Phase D-3 (slot 3 of 5)...")
    reservation = quota_mgr.reserve_slot(model)
    if not reservation:
        logger.error("[QUOTA GATE REJECTED] Reservation denied, exhausted, or unpersisted. Aborting (0 HTTP calls).")
        return {
            "status": "ABORTED_RESERVATION_FAILED",
            "http_requests_sent": 0,
            "quota_reserved": False,
            "detail": "Quota reservation failed."
        }

    res_id = reservation["reservation_id"]
    logger.info(f"[QUOTA GATE GRANTED] Reservation durably secured: {res_id}")

    # 2. Build Consolidated Prompt (No Search Grounding Tool)
    prompt_text = build_consolidated_prompt(today_str)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    # 3. Submit EXACTLY ONE HTTP Request
    logger.info(f"[HTTP DISPATCH] Sending EXACTLY ONE request to {model} for 3 complete articles (timeout=45s)...")
    http_code = None
    res_json = None
    raw_error_body = None

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            http_code = resp.getcode()
            body_str = resp.read().decode("utf-8")
            res_json = json.loads(body_str)
            logger.info(f"[HTTP SUCCESS] Received HTTP {http_code}.")
    except urllib.error.HTTPError as e:
        http_code = e.code
        try:
            raw_error_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw_error_body = str(e.reason)
        logger.error(f"[HTTP ERROR {http_code}] {e.reason}\nRaw Google Error Body:\n{mask_secret(raw_error_body)}")
    except urllib.error.URLError as e:
        raw_error_body = f"URLError: {str(e.reason)}"
        logger.error(f"[NETWORK ERROR] {raw_error_body}")
    except Exception as e:
        raw_error_body = f"Unexpected Exception: {str(e)}"
        logger.error(f"[UNEXPECTED ERROR] {raw_error_body}")

    # 4. Finalize Quota Slot
    final_status = "COMPLETED" if (res_json and http_code == 200) else (f"FAILED_HTTP_{http_code}" if http_code else "FAILED_NETWORK")
    quota_mgr.finalize_slot(res_id, final_status)
    if quota_mgr.execution_mode == "CI_PRODUCTION":
        try:
            res_pre = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=False)
            if res_pre.returncode == 0 and not res_pre.stdout.strip():
                subprocess.run(["git", "add", quota_mgr.state_file], check=False)
                res_post = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=False)
                staged = [line.strip() for line in res_post.stdout.strip().splitlines() if line.strip()]
                norm_state = os.path.normpath(quota_mgr.state_file).replace("\\", "/")
                if len(staged) == 1 and norm_state.endswith(staged[0]):
                    commit_msg = f"ci: finalize gemini quota reservation {res_id} ({final_status}) [skip ci]"
                    subprocess.run(["git", "commit", "-m", commit_msg], check=False)
                    subprocess.run(["git", "push", "origin", "main"], check=False)
                    logger.info(f"[QUOTA FINALIZED & PERSISTED] Slot {res_id} marked {final_status} on origin/main.")
        except Exception as pe:
            logger.warning(f"Could not push finalized quota state: {pe}")

    # 5. Extract and Validate Output Articles
    generated_articles = []
    if res_json:
        try:
            raw_reply = res_json["candidates"][0]["content"]["parts"][0]["text"]
            clean_reply = re.sub(r'^```(?:json)?\s*', '', raw_reply.strip(), flags=re.MULTILINE)
            clean_reply = re.sub(r'```$', '', clean_reply.strip(), flags=re.MULTILINE)
            m = re.search(r'\[.*\]', clean_reply, re.DOTALL)
            if m:
                generated_articles = json.loads(m.group(0))
        except Exception as e:
            logger.error(f"Error parsing generated articles JSON: {e}")

    # 6. Save Diagnostic Artifact
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_file = os.path.join(reports_dir, f"phase_d3_three_articles_{now_myt.strftime('%Y%m%d_%H%M%S')}.json")

    report_payload = {
        "timestamp_myt": now_myt.isoformat(),
        "model_used": model,
        "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "reservation_id": res_id,
        "http_requests_sent": 1,
        "http_status_code": http_code,
        "success": bool(generated_articles),
        "raw_error_body": mask_secret(raw_error_body) if raw_error_body else None,
        "articles_count": len(generated_articles),
        "articles": generated_articles,
        "source_stories_verified": SOURCE_STORIES,
        "production_integrity_check": {
            "news_data_modified": False,
            "index_html_modified": False,
            "website_published": False
        }
    }

    try:
        with open(report_file, "w", encoding="utf-8") as rf:
            json.dump(report_payload, rf, indent=2, ensure_ascii=False)
        logger.info(f"✅ Diagnostic artifact saved to: {report_file}")
    except Exception as e:
        logger.error(f"Failed to write artifact file: {e}")

    # 7. Write GitHub Step Summary
    step_summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        try:
            with open(step_summary_path, "a", encoding="utf-8") as sf:
                sf.write("## 📰 Phase D-3: Single API Request, Three Complete News Articles\n\n")
                sf.write(f"- **Execution Time (MYT):** `{now_myt.strftime('%Y-%m-%d %H:%M:%S')}`\n")
                sf.write(f"- **Model Used:** `{model}` (Standard generateContent, 0 Search Grounding tools)\n")
                sf.write(f"- **Reservation ID:** `{res_id}`\n")
                sf.write(f"- **HTTP Status:** `{http_code}`\n")
                sf.write(f"- **Articles Generated:** `{len(generated_articles)} / 3`\n\n")

                if raw_error_body:
                    sf.write(f"### ❌ Error Response Diagnostic\n```json\n{mask_secret(raw_error_body)}\n```\n\n")

                if generated_articles:
                    for idx, art in enumerate(generated_articles, 1):
                        sf.write(f"### 📄 Article {idx}: {art.get('headline_zh')}\n")
                        sf.write(f"**Tajuk BM:** {art.get('headline_bm')}\n\n")
                        sf.write(f"- **Category:** `{art.get('category')}` | **Location:** `{art.get('location')}`\n")
                        sf.write(f"- **Publication Date:** `{art.get('publication_date')}` | **Event Date:** `{art.get('event_date')}`\n")
                        sf.write(f"- **Original Source URL:** [{art.get('original_url')}]({art.get('original_url')})\n\n")
                        sf.write(f"#### 中文深度报道全文\n{art.get('full_article_zh')}\n\n")
                        sf.write(f"#### Teks Penuh Berita Bahasa Melayu\n{art.get('full_article_bm')}\n\n")
                        sf.write(f"**核心事实要素:** {', '.join(art.get('key_data_points', []))}\n\n")
                        sf.write("---\n\n")
        except Exception as e:
            logger.warning(f"Failed to write to GITHUB_STEP_SUMMARY: {e}")

    return report_payload


if __name__ == "__main__":
    res = run_phase_d3()
    if not res.get("success"):
        sys.exit(1)
