#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Dedicated Read-Only Google Drive Verification Script (Phase D-15.4)
Author: Sabah Daily News Pipeline
Restrictions:
- Google Drive read-only access only.
- 0 Gemini API requests.
- 0 QuotaManager reservations.
- 0 Git commits / pushes during test execution.
- 0 Website data modifications.
- Self-contained: runs reliably on any environment with zero third-party dependencies.
"""

import os
import sys
import re
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MYT = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("test_gdrive_read_only")


@dataclass
class ParsedMarkdownStory:
    index: int
    title: str
    body: str
    category: str = "sabah"
    geo_scope: str = "sabah"
    sources: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    date: str = ""
    is_event: bool = False
    event_metadata: Optional[Dict[str, Any]] = None
    raw_header: str = ""


class SelfContainedGDriveReader:
    """Self-contained Google Drive Markdown reader and parser."""

    def __init__(self, folder_id: Optional[str] = None):
        env_fid = os.getenv("GDRIVE_FOLDER_ID", "").strip()
        self.folder_id = env_fid or folder_id or "18uRBmOQM5hTdeQvldILnC9_n4LZIs1kf"
        self.file_name_patterns = [
            "西门看看网每日新闻_{date}.md",
            "sabah_news_{date}.md",
            "sabah_daily_news_{date}.md",
            "meta_ai_news_{date}.md",
            "news_{date}.md",
            "{date}.md"
        ]

    def get_today_myt_str(self) -> str:
        return datetime.now(MYT).strftime("%Y-%m-%d")

    def resolve_candidate_filenames(self, target_date: Optional[str] = None) -> List[str]:
        date_str = target_date or self.get_today_myt_str()
        candidates = []
        for pat in self.file_name_patterns:
            fname = pat.replace("{date}", date_str)
            if fname not in candidates:
                candidates.append(fname)
        return candidates

    def _get_oauth_access_token(self) -> Optional[str]:
        refresh_token = os.getenv("GDRIVE_REFRESH_TOKEN", "").strip()
        client_id = os.getenv("GDRIVE_CLIENT_ID", "").strip()
        client_secret = os.getenv("GDRIVE_CLIENT_SECRET", "").strip()

        if not (refresh_token and client_id and client_secret):
            return None

        token_url = "https://oauth2.googleapis.com/token"
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(token_url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                access_token = res_data.get("access_token")
                if access_token:
                    logger.info("[GDRIVE AUTH] Successfully acquired OAuth access token via refresh token.")
                    return access_token
        except Exception as e:
            logger.warning(f"[GDRIVE AUTH] Failed to exchange refresh token: {e}")
        return None

    def read_from_drive_api(
        self,
        candidate_names: List[str],
        folder_id: Optional[str] = None
    ) -> Optional[Tuple[str, str, Optional[str]]]:
        access_token = self._get_oauth_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        fid = folder_id or self.folder_id

        # 1. Primary search: inside specified folder
        for fname in candidate_names:
            query_parts = [
                f"name = '{fname}'",
                "trashed = false",
                "mimeType != 'application/vnd.google-apps.document'"
            ]
            if fid:
                query_parts.append(f"'{fid}' in parents")
            q_str = " and ".join(query_parts)

            url = f"https://www.googleapis.com/drive/v3/files?q={urllib.parse.quote(q_str)}&fields=files(id,name,mimeType,size)&pageSize=10"
            try:
                req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    files = data.get("files", [])
                    for f_item in files:
                        file_id = f_item.get("id")
                        file_name = f_item.get("name", "")
                        mime_type = f_item.get("mimeType", "")

                        if mime_type == "application/vnd.google-apps.document" or not file_name.lower().endswith(".md"):
                            logger.info(f"[GDRIVE SKIP] Skipping non-markdown or Google Doc: {file_name} ({mime_type})")
                            continue

                        logger.info(f"[GDRIVE FOUND] Located authentic markdown file '{file_name}' (ID: {file_id}) in Google Drive folder '{fid}'.")

                        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
                        dl_req = urllib.request.Request(download_url, headers=headers, method="GET")
                        with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                            content = dl_resp.read().decode("utf-8")
                            return file_name, content, file_id
            except Exception as e:
                logger.warning(f"[GDRIVE API SEARCH ERROR] Querying '{fname}' in '{fid}': {e}")

        # 2. Secondary fallback search without parent constraint if direct search yielded no match
        logger.info("[GDRIVE FALLBACK] Primary parent query returned no file; checking exact file match across account...")
        for fname in candidate_names:
            q_str = f"name = '{fname}' and trashed = false and mimeType != 'application/vnd.google-apps.document'"
            url = f"https://www.googleapis.com/drive/v3/files?q={urllib.parse.quote(q_str)}&fields=files(id,name,mimeType,size,parents)&pageSize=5"
            try:
                req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    files = data.get("files", [])
                    for f_item in files:
                        file_id = f_item.get("id")
                        file_name = f_item.get("name", "")
                        mime_type = f_item.get("mimeType", "")

                        if mime_type == "application/vnd.google-apps.document" or not file_name.lower().endswith(".md"):
                            continue

                        logger.info(f"[GDRIVE FOUND VIA FALLBACK] Located authentic markdown file '{file_name}' (ID: {file_id}, Parents: {f_item.get('parents')}).")
                        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
                        dl_req = urllib.request.Request(download_url, headers=headers, method="GET")
                        with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                            content = dl_resp.read().decode("utf-8")
                            return file_name, content, file_id
            except Exception as e:
                logger.warning(f"[GDRIVE FALLBACK SEARCH ERROR] Querying '{fname}': {e}")

        return None

    def _normalize_category(self, raw_cat: str) -> str:
        cat_lower = raw_cat.strip().lower()
        if any(k in cat_lower for k in ["沙巴", "山打根", "亚庇", "sabah", "sandakan", "negeri", "wilayah"]):
            return "sabah"
        if any(k in cat_lower for k in ["全国", "国内", "中央", "national", "negara", "persekutuan", "政经", "财经", "parlimen"]):
            return "national"
        if any(k in cat_lower for k in ["国际", "世界", "海外", "international", "world", "antarabangsa"]):
            return "general"
        if any(k in cat_lower for k in ["体育", "运动", "sport", "sukan", "bola", "badminton", "sukma"]):
            return "sports"
        if any(k in cat_lower for k in ["活动", "预告", "日程", "event", "acara", "kalendar"]):
            return "event"
        return "sabah"

    def _determine_geo_scope(self, text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in ["山打根", "sandakan", "西必洛", "sepilok", "森森", "sim-sim"]):
            return "sandakan"
        if any(k in text_lower for k in ["沙巴", "sabah", "亚庇", "kota kinabalu", "兵南邦", "penampang", "斗湖", "tawau"]):
            return "sabah"
        return "national"

    def parse_markdown(
        self,
        markdown_text: str,
        target_date: Optional[str] = None
    ) -> List[ParsedMarkdownStory]:
        if not markdown_text or not markdown_text.strip():
            return []

        default_date = target_date or self.get_today_myt_str()
        stories: List[ParsedMarkdownStory] = []

        lines = markdown_text.strip().splitlines()
        current_header = ""
        current_lines: List[str] = []

        header_pattern = re.compile(
            r'^(#{1,4}\s+.*|(?:\d{1,2}\.|\b(?:STORY|NEWS|ITEM)\s*\d+[:\.]?)\s+.*)',
            re.IGNORECASE
        )
        blocks: List[Tuple[str, List[str]]] = []

        for line in lines:
            line_s = line.strip()
            # Skip top-level document title
            if re.match(r'^#\s+(?:20\d\d|沙巴|西门|每日新闻|Daily\s+News).*', line_s, re.IGNORECASE) and not blocks and not current_lines:
                continue

            if header_pattern.match(line_s):
                if current_lines:
                    blocks.append((current_header, current_lines))
                    current_lines = []
                current_header = line_s
            else:
                if current_header or line_s:
                    current_lines.append(line)

        if current_header or current_lines:
            blocks.append((current_header, current_lines))

        # Handle --- delimiter fallback if few blocks
        if len(blocks) <= 1 and len(lines) > 20:
            hr_splits = re.split(r'\n\s*---\s*\n', markdown_text)
            if len(hr_splits) > 1:
                blocks = []
                for split_part in hr_splits:
                    part_lines = split_part.strip().splitlines()
                    if part_lines:
                        blocks.append((part_lines[0], part_lines[1:]))

        story_idx = 1
        bullet_pat = re.compile(r'^(?:[-+•]\s*|\*\s+)')
        current_active_section = "sabah"

        for header, block_lines in blocks:
            full_block_text = "\n".join(block_lines).strip()
            if not header and not full_block_text:
                continue

            raw_title = header.lstrip("#").strip()
            clean_title = re.sub(r'^(?:\[?\d+\]?[\.\、\:\s\-]+|第\s*\d+\s*[条篇]\s*[\:\.\s]*)', '', raw_title).strip()

            # Check if this header is just a section divider (e.g. "## 一、沙巴与山打根要闻")
            sec_match = re.search(r'(?:一|二|三|四|五|六|[1-6])[\s\、\.\:：]+(.*)', clean_title)
            is_section_divider = False
            if sec_match:
                sec_name = sec_match.group(1).strip()
                if any(k in sec_name for k in ["沙巴", "山打根", "要闻", "全国", "国际", "体育", "活动", "预告"]):
                    # If this block has no substantive body, treat as a section header update
                    if len(full_block_text) < 10 or not any(k in full_block_text for k in ["来源", "内容", "正文", "http"]):
                        current_active_section = self._normalize_category(sec_name)
                        is_section_divider = True

            if is_section_divider:
                continue

            title_in_body = None
            for bline in block_lines:
                clean_bline = bullet_pat.sub('', bline.strip()).strip()
                m_t = re.match(r'^\*{0,2}(?:标题|Title|Tajuk)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_t:
                    title_in_body = m_t.group(1).strip("* ")
                    break

            title = title_in_body or clean_title or f"每日新闻第 {story_idx} 条"

            sources = []
            source_urls = []
            extracted_date = default_date
            body_paragraphs = []
            category_candidate = None
            is_event = (current_active_section == "event")
            event_meta = {}

            header_lower = (header + " " + title).lower()
            if any(k in header_lower for k in ["活动预报", "活动预告", "活动日程", "未来活动", "event", "acara", "gotong-royong", "pesta", "峰会", "义诊", "即将举行", "开放报名"]):
                is_event = True

            for bline in block_lines:
                s_bline = bline.strip()
                if not s_bline or s_bline == "---":
                    continue

                clean_bline = bullet_pat.sub('', s_bline).strip()

                # Sources
                m_src = re.match(r'^\*{0,2}(?:来源|信源|Source|Sumber|Penerbit)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_src:
                    src_val = m_src.group(1).strip("* ")
                    for s in re.split(r'[,，/、+及与]', src_val):
                        s_clean = s.strip()
                        if s_clean and s_clean not in sources:
                            sources.append(s_clean)
                    continue

                # Links
                m_url = re.match(r'^\*{0,2}(?:链接|原[文链]|URL|Link|Pautan)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_url:
                    raw_url_val = m_url.group(1).strip("* ")
                    url_match = re.search(r'https?://[^\s\)\>]+', raw_url_val)
                    if url_match:
                        source_urls.append(url_match.group(0))
                    continue

                # Date
                m_date = re.match(r'^\*{0,2}(?:日期|时间|Date|Tarikh)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_date:
                    date_val = m_date.group(1).strip("* ")
                    d_m = re.search(r'20\d\d-\d{2}-\d{2}', date_val)
                    if d_m:
                        extracted_date = d_m.group(0)
                        if extracted_date > default_date:
                            is_event = True
                    continue

                # Category
                m_cat = re.match(r'^\*{0,2}(?:分类|类别|板块|Category|Kategori)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_cat:
                    category_candidate = m_cat.group(1).strip("* ").lower()
                    if any(k in category_candidate for k in ["活动", "event", "acara"]):
                        is_event = True
                    continue

                # Event fields
                m_loc = re.match(r'^\*{0,2}(?:地点|Location|Tempat)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_loc:
                    is_event = True
                    event_meta["location"] = m_loc.group(1).strip("* ")
                    continue

                # Body
                m_content = re.match(r'^\*{0,2}(?:正文|内容|Content|Kandungan|摘要|Detail|Ringkasan)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_content:
                    body_paragraphs.append(m_content.group(1).strip())
                    continue

                if not clean_bline.startswith("#"):
                    body_paragraphs.append(clean_bline)

            final_body = "\n\n".join(body_paragraphs).strip()
            if not final_body:
                final_body = full_block_text

            category = self._normalize_category(category_candidate or current_active_section)
            geo_scope = self._determine_geo_scope(title + " " + final_body)

            story = ParsedMarkdownStory(
                index=story_idx,
                title=title,
                body=final_body,
                category=category,
                geo_scope=geo_scope,
                sources=sources if sources else ["西门看看网综合采编"],
                source_urls=source_urls,
                date=extracted_date,
                is_event=is_event,
                event_metadata=event_meta if event_meta else None,
                raw_header=header
            )
            stories.append(story)
            story_idx += 1

        return stories


def run_gdrive_read_test(target_date: str = "2026-11-10", local_file_fallback: Optional[str] = None) -> int:
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    report_md_path = os.path.join(reports_dir, "test_gdrive_parse_report.md")
    report_json_path = os.path.join(reports_dir, "test_gdrive_parse_report.json")
    downloaded_md_path = os.path.join(reports_dir, "test_gdrive_downloaded.md")

    reader = SelfContainedGDriveReader()

    logger.info("=" * 60)
    logger.info(f"Phase D-15.4 Read-Only Google Drive Verification for Date: {target_date}")
    logger.info(f"Target Folder ID: {reader.folder_id}")
    logger.info(f"Preferred File Pattern: {reader.file_name_patterns[0]}")
    logger.info("=" * 60)

    # Offline local testing flag
    if local_file_fallback and os.path.exists(local_file_fallback):
        logger.info(f"[LOCAL TEST MODE] Reading offline fixture: {local_file_fallback}")
        with open(local_file_fallback, "r", encoding="utf-8") as f:
            content = f.read()
        file_name = os.path.basename(local_file_fallback)
        file_id = "local_test_fixture"
    else:
        # Real Google Drive API Mode
        token = reader._get_oauth_access_token()
        if not token:
            msg = (
                "AUTHENTICATION FAILED: Missing required Google Drive OAuth credentials in environment.\n"
                "Required GitHub Secrets: GDRIVE_REFRESH_TOKEN, GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET."
            )
            logger.error(msg)
            with open(report_md_path, "w", encoding="utf-8") as f:
                f.write(f"# Phase D-15.4 Google Drive Read Test Failure\n\n**Date**: {target_date}\n\n**Status**: {msg}\n")
            return 1

        candidates = reader.resolve_candidate_filenames(target_date)
        logger.info(f"Searching candidate filenames in Drive folder: {candidates}")

        res = reader.read_from_drive_api(candidates, reader.folder_id)
        if not res:
            msg = f"FILE NOT FOUND: No matching markdown file found in folder {reader.folder_id} for date {target_date}."
            logger.error(msg)
            with open(report_md_path, "w", encoding="utf-8") as f:
                f.write(f"# Phase D-15.4 Google Drive Read Test Failure\n\n**Date**: {target_date}\n\n**Status**: {msg}\n")
            return 1

        file_name, content, file_id = res

    file_bytes = len(content.encode("utf-8"))
    logger.info(f"Downloaded / Loaded file: '{file_name}' (ID: {file_id}, Size: {file_bytes} bytes)")

    with open(downloaded_md_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Saved downloaded markdown to: {downloaded_md_path}")

    # Parse markdown stories
    stories = reader.parse_markdown(content, target_date)
    news_stories = [s for s in stories if not s.is_event]
    event_stories = [s for s in stories if s.is_event]

    section_breakdown: Dict[str, int] = {}
    for s in news_stories:
        cat = s.category
        section_breakdown[cat] = section_breakdown.get(cat, 0) + 1

    logger.info(f"Parsed total stories: {len(stories)}")
    logger.info(f"Active news stories count: {len(news_stories)}")
    logger.info(f"Future event announcements count: {len(event_stories)}")
    logger.info(f"Section breakdown: {section_breakdown}")

    report_data = {
        "target_date": target_date,
        "verification_time_myt": datetime.now(MYT).isoformat(),
        "folder_id": reader.folder_id,
        "file_name": file_name,
        "file_id": file_id,
        "file_size_bytes": file_bytes,
        "total_stories_found": len(stories),
        "news_stories_count": len(news_stories),
        "event_stories_count": len(event_stories),
        "sections": section_breakdown,
        "gemini_api_calls": 0,
        "quota_reservations": 0,
        "news_stories": [
            {
                "index": s.index,
                "title": s.title,
                "category": s.category,
                "geo_scope": s.geo_scope,
                "sources": s.sources,
                "source_urls": s.source_urls,
                "body_length_chars": len(s.body),
                "body_preview": s.body[:150] + "..." if len(s.body) > 150 else s.body
            }
            for s in news_stories
        ],
        "event_stories": [
            {
                "index": s.index,
                "title": s.title,
                "event_date": s.date,
                "event_metadata": s.event_metadata,
                "body": s.body
            }
            for s in event_stories
        ]
    }

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    lines = [
        f"# Phase D-15.4 Google Drive Read Test Report",
        f"",
        f"- **Target Date**: `{target_date}`",
        f"- **Verification Time**: `{report_data['verification_time_myt']}`",
        f"- **Drive Folder ID**: `{reader.folder_id}`",
        f"- **Downloaded File Name**: `{file_name}`",
        f"- **File ID**: `{file_id}`",
        f"- **File Size**: `{file_bytes} bytes`",
        f"- **Total Items Parsed**: `{len(stories)}`",
        f"  - Active News Items: `{len(news_stories)}`",
        f"  - Future Event Announcements: `{len(event_stories)}`",
        f"",
        f"## Section Breakdown",
        f"",
    ]
    for sec, cnt in section_breakdown.items():
        lines.append(f"- **{sec}**: {cnt} items")
    lines.append(f"- **events**: {len(event_stories)} items")

    lines.extend([
        f"",
        f"## Active News Items Detail",
        f"",
    ])
    for item in report_data["news_stories"]:
        lines.append(f"### {item['index']}. {item['title']}")
        lines.append(f"- **Category / Scope**: `{item['category']}` / `{item['geo_scope']}`")
        lines.append(f"- **Sources**: {', '.join(item['sources']) if item['sources'] else 'N/A'}")
        lines.append(f"- **Links**: {', '.join(item['source_urls']) if item['source_urls'] else 'N/A'}")
        lines.append(f"- **Body Character Count**: {item['body_length_chars']}")
        lines.append(f"- **Body Preview**: {item['body_preview']}")
        lines.append(f"")

    if event_stories:
        lines.extend([
            f"## Future Event Announcements",
            f"",
        ])
        for ev in report_data["event_stories"]:
            lines.append(f"### Event #{ev['index']}: {ev['title']}")
            lines.append(f"- **Target Event Date**: `{ev['event_date']}`")
            lines.append(f"- **Details**: {ev['body']}")
            lines.append(f"")

    lines.extend([
        f"## Safety Verification",
        f"",
        f"- **Gemini API Requests**: 0",
        f"- **QuotaManager Reservations**: 0",
        f"- **Website Publishing**: NONE (artifacts only)",
        f"- **Git Status**: 0 commits / 0 pushes during execution",
    ])

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Generated comprehensive markdown report at: {report_md_path}")
    logger.info("Phase D-15.4 read-only test completed successfully with 0 Gemini calls.")
    return 0


if __name__ == "__main__":
    t_date = os.getenv("TARGET_DATE") or "2026-11-10"
    local_fb = None
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--local-file="):
            local_fb = sys.argv[1].split("=", 1)[1]
        else:
            t_date = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2].startswith("--local-file="):
        local_fb = sys.argv[2].split("=", 1)[1]
    sys.exit(run_gdrive_read_test(t_date, local_fb))
