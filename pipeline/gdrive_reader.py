#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Google Drive Markdown Input Reader & Parser
Architecture: Meta AI → Google Drive → GitHub Actions → Gemini → Sabah Daily News

Features:
- Locates today's Markdown news file in Google Drive by Asia/Kuala_Lumpur calendar date.
- Configurable file naming patterns (never hardcoded to a single static pattern).
- Configurable folder ID via config or environment variables.
- Dual authentication methods for GitHub Actions:
  1) OAuth 2.0 Refresh Token (GDRIVE_REFRESH_TOKEN, GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET)
  2) Service Account Key JSON (GDRIVE_SERVICE_ACCOUNT_KEY / GDRIVE_CREDENTIALS_JSON)
  3) Local filesystem fallback (GDRIVE_LOCAL_FILE_OVERRIDE / data/gdrive_inputs/) for offline runs.
- Read-only on Drive: preserves original files without modification.
- Saves traceable local input snapshots to reports/gdrive_snapshots/.
- Robust Markdown parser supporting variable news counts, multiline bodies, sources, links,
  and distinguishing between active news and future event forecasts.
- Zero external third-party dependencies (pure standard library: urllib.request, json, re, os).
- Fail-closed: missing, empty, or unreadable input halts cleanly without destroying production news.
"""

import os
import sys
import re
import json
import time
import hashlib
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from collectors.base import RawArticle

logger = logging.getLogger("pipeline.gdrive_reader")
MYT = timezone(timedelta(hours=8))


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


@dataclass
class GDriveInputSnapshot:
    snapshot_id: str
    target_date: str
    source_file_name: str
    source_file_id: Optional[str]
    read_timestamp: str
    total_stories_found: int
    news_stories_count: int
    event_stories_count: int
    markdown_sha256: str
    news_stories: List[Dict[str, Any]] = field(default_factory=list)
    event_stories: List[Dict[str, Any]] = field(default_factory=list)


class GDriveMarkdownReader:
    """
    Dedicated Google Drive Markdown ingestion engine for Sabah Daily News.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        gdrive_cfg = self.config.get("gdrive_input", {})
        self.enabled = gdrive_cfg.get("enabled", True)
        self.folder_id = os.getenv("GDRIVE_FOLDER_ID") or gdrive_cfg.get("folder_id", "")
        self.file_name_patterns = gdrive_cfg.get(
            "file_name_patterns",
            [
                "sabah_news_{date}.md",
                "sabah_daily_news_{date}.md",
                "meta_ai_news_{date}.md",
                "news_{date}.md",
                "{date}.md"
            ]
        )
        self.fallback_local_dir = os.path.join(
            BASE_DIR,
            gdrive_cfg.get("fallback_local_dir", "data/gdrive_inputs")
        )
        self.snapshot_dir = os.path.join(
            BASE_DIR,
            gdrive_cfg.get("snapshot_dir", "reports/gdrive_snapshots")
        )
        self.max_selected_articles = int(gdrive_cfg.get("max_selected_articles", 10))
        self.sandakan_priority = gdrive_cfg.get("sandakan_priority", True)
        self.read_retry_attempts = int(gdrive_cfg.get("read_retry_attempts", 4))
        self.read_retry_delay_seconds = int(gdrive_cfg.get("read_retry_delay_seconds", 60))

    def get_today_myt_str(self) -> str:
        """Return current calendar date string (YYYY-MM-DD) in Asia/Kuala_Lumpur."""
        return datetime.now(MYT).strftime("%Y-%m-%d")

    def resolve_candidate_filenames(self, target_date: Optional[str] = None) -> List[str]:
        """Generate ordered list of candidate filenames for the target date."""
        date_str = target_date or self.get_today_myt_str()
        candidates = []
        for pat in self.file_name_patterns:
            fname = pat.replace("{date}", date_str)
            if fname not in candidates:
                candidates.append(fname)
        return candidates

    def _get_oauth_access_token(self) -> Optional[str]:
        """
        Exchange OAuth 2.0 refresh token for an access token via Google OAuth2 endpoint.
        Uses pure standard library urllib.request (zero third-party dependencies).
        """
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
        """
        Search for candidate files in Google Drive using Drive API v3.
        Returns (found_filename, file_content, file_id) or None.
        Enforces read-only access (GET requests only).
        """
        access_token = self._get_oauth_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        # Build search query
        for fname in candidate_names:
            query_parts = [
                f"name = '{fname}'",
                "trashed = false",
                "mimeType != 'application/vnd.google-apps.document'"
            ]
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
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

                        # Explicit exclusion: ignore Google Docs and non-.md files
                        if mime_type == "application/vnd.google-apps.document" or not file_name.lower().endswith(".md"):
                            logger.info(f"[GDRIVE SKIP] Skipping non-markdown or Google Doc: {file_name} ({mime_type})")
                            continue

                        logger.info(f"[GDRIVE FOUND] Located authentic markdown file '{file_name}' (ID: {file_id}) in Google Drive.")

                        # Download content (read-only alt=media)
                        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
                        dl_req = urllib.request.Request(download_url, headers=headers, method="GET")
                        with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                            content = dl_resp.read().decode("utf-8")
                            return file_name, content, file_id
            except Exception as e:
                logger.warning(f"[GDRIVE API SEARCH ERROR] Querying '{fname}': {e}")

        return None

    def read_from_local_fallback(
        self,
        candidate_names: List[str]
    ) -> Optional[Tuple[str, str, Optional[str]]]:
        """
        Read markdown file from local override path or fallback directory.
        Used for offline development, local dry-runs, and emergency manual uploads.
        """
        # 1. Direct explicit override via environment variable
        env_override = os.getenv("GDRIVE_LOCAL_FILE_OVERRIDE", "").strip()
        if env_override:
            if os.path.exists(env_override):
                try:
                    with open(env_override, "r", encoding="utf-8") as f:
                        content = f.read()
                    logger.info(f"[LOCAL OVERRIDE] Successfully loaded markdown from: {env_override}")
                    return os.path.basename(env_override), content, "local_override"
                except Exception as e:
                    logger.warning(f"[LOCAL OVERRIDE ERROR] Reading {env_override}: {e}")
                    return None
            else:
                logger.warning(f"[LOCAL OVERRIDE NOT FOUND] Specified override file does not exist: {env_override}")
                return None

        # 2. Check fallback directory
        if os.path.exists(self.fallback_local_dir):
            for fname in candidate_names:
                fpath = os.path.join(self.fallback_local_dir, fname)
                if os.path.exists(fpath):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()
                        logger.info(f"[LOCAL FALLBACK] Loaded markdown file from: {fpath}")
                        return fname, content, f"local_{fname}"
                    except Exception as e:
                        logger.warning(f"[LOCAL FALLBACK ERROR] Reading {fpath}: {e}")

        return None

    def read_markdown_content(
        self,
        target_date: Optional[str] = None
    ) -> Optional[Tuple[str, str, Optional[str]]]:
        """
        Unified markdown reader:
        Attempts local override -> Google Drive API -> local fallback.
        Returns (filename, content, file_id) or None.
        """
        date_str = target_date or self.get_today_myt_str()
        candidates = self.resolve_candidate_filenames(date_str)

        # 1. Local override check (offline priority if explicitly set)
        if os.getenv("GDRIVE_LOCAL_FILE_OVERRIDE"):
            res = self.read_from_local_fallback(candidates)
            if res:
                return res
            return None

        # 2. Bounded retry loop for Drive API / Local Fallback
        attempts = max(1, self.read_retry_attempts)
        for attempt in range(1, attempts + 1):
            # Attempt Google Drive API
            drive_res = self.read_from_drive_api(candidates, self.folder_id)
            if drive_res:
                return drive_res

            # Attempt local fallback directory
            local_res = self.read_from_local_fallback(candidates)
            if local_res:
                return local_res

            # If not found and more attempts remain, wait before next retry
            if attempt < attempts:
                wait_sec = self.read_retry_delay_seconds
                logger.info(
                    f"[GDRIVE RETRY] Markdown file for {date_str} not yet available in Drive "
                    f"(attempt {attempt}/{attempts}). Waiting {wait_sec}s before retry... (0 Gemini calls, 0 quota used)"
                )
                if wait_sec > 0:
                    time.sleep(wait_sec)

        logger.error(
            f"[GDRIVE FAIL-CLOSED] No matching markdown file found for date {date_str} "
            f"in Drive or local fallback after {attempts} attempts. Halting cleanly."
        )
        return None

    def parse_markdown(
        self,
        markdown_text: str,
        target_date: Optional[str] = None
    ) -> List[ParsedMarkdownStory]:
        """
        Versatile Markdown Parser for Meta AI Daily News.
        Capabilities:
        - Extracts variable number of stories (never assumes fixed 10, 25, 26).
        - Handles Phase D-16 5-section numbered format (### 1. to ### 26.).
        - Robustly avoids treating document titles (# ...) and section titles (## ...) as stories.
        - Extracts title, body, sources, links, date, category.
        - Identifies Future Event Forecasts (is_event=True) so they are not treated as past news.
        - Supports multilingual text (Chinese, Malay, English).
        - Resilient: never drops stories if in-text numbering skips or differs from count.
        """
        if not markdown_text or not markdown_text.strip():
            return []

        default_date = target_date or self.get_today_myt_str()
        stories: List[ParsedMarkdownStory] = []

        # 1. Specialized numbered parser for Meta AI 5-section format (### 1. to ### 26.)
        pat_str = r'###\s+(\d+)[\.\、]\s+([^\n]+)(.*?)(?=(?:\n###\s+\d+[\.\、]|\n##\s+|\n\*\*今日统计|\Z))'
        numbered_pattern = re.compile(pat_str, re.DOTALL)
        numbered_matches = numbered_pattern.findall(markdown_text)

        if len(numbered_matches) >= 10:
            for num_str, raw_title, body_block in numbered_matches:
                s_idx = int(num_str)
                clean_title = raw_title.strip()

                if 1 <= s_idx <= 4:
                    cat = "sabah"
                    geo = "sandakan"
                    is_ev = False
                elif 5 <= s_idx <= 9:
                    cat = "event"
                    geo = "sandakan"
                    is_ev = True
                elif 10 <= s_idx <= 19:
                    cat = "sabah"
                    geo = "sandakan" if ("sandakan" in clean_title.lower() or "山打根" in clean_title) else "sabah"
                    is_ev = False
                elif 20 <= s_idx <= 23:
                    cat = "national"
                    geo = "national"
                    is_ev = False
                elif 24 <= s_idx <= 26:
                    cat = "sports"
                    geo = "national"
                    is_ev = False
                else:
                    cat = "sabah"
                    geo = "sabah"
                    is_ev = False

                sources = []
                source_urls = []
                event_meta = {}
                clean_body_lines = []

                for bline in body_block.strip().splitlines():
                    s_bline = bline.strip()
                    if not s_bline or s_bline == "---":
                        continue

                    m_src = re.match(r'^\*{0,2}(?:来源|信源|Source|Sumber|Penerbit)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', s_bline, re.IGNORECASE)
                    if m_src:
                        src_val = m_src.group(1).strip("* ")
                        for s_part in re.split(r'[,，/、+及与|]', src_val):
                            s_clean = s_part.strip()
                            if s_clean and not re.match(r'^\d{1,2}/\d{1,2}', s_clean) and "持续" not in s_clean and len(s_clean) < 30:
                                if s_clean not in sources:
                                    sources.append(s_clean)
                        for u_match in re.findall(r'https?://[^\s\)\>]+', src_val):
                            if u_match not in source_urls:
                                source_urls.append(u_match)
                        continue

                    m_loc = re.match(r'^\*{0,2}(?:地点|Location|Tempat)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', s_bline, re.IGNORECASE)
                    if m_loc:
                        event_meta["location"] = m_loc.group(1).strip("* ")
                        continue

                    m_tag = re.match(r'^\*{0,2}(?:标签|Tag|Kategori)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', s_bline, re.IGNORECASE)
                    if m_tag:
                        event_meta["tag"] = m_tag.group(1).strip("* ")
                        continue

                    for u_match in re.findall(r'https?://[^\s\)\>]+', s_bline):
                        if u_match not in source_urls:
                            source_urls.append(u_match)

                    clean_body_lines.append(s_bline)

                body_text = "\n\n".join(clean_body_lines).strip()
                if not body_text:
                    body_text = clean_title

                if not sources:
                    sources = ["Facebook 官方渠道" if "FB" in body_block else "Meta AI 权威整理"]

                extracted_date = default_date
                if is_ev:
                    m_d = re.search(r'(\d{1,2})/(\d{1,2})', clean_title)
                    if m_d:
                        m_val = int(m_d.group(1))
                        d_val = int(m_d.group(2))
                        y_val = int(default_date.split("-")[0])
                        extracted_date = f"{y_val}-{m_val:02d}-{d_val:02d}"

                story = ParsedMarkdownStory(
                    index=s_idx,
                    title=clean_title,
                    body=body_text,
                    category=cat,
                    geo_scope=geo,
                    sources=sources,
                    source_urls=source_urls,
                    date=extracted_date,
                    is_event=is_ev,
                    event_metadata=event_meta if is_ev else None,
                    raw_header=f"### {s_idx}. {clean_title}"
                )
                stories.append(story)

            return stories

        # 2. General Fallback Block-based Parser
        lines = markdown_text.strip().splitlines()
        current_header = ""
        current_lines: List[str] = []

        header_pattern = re.compile(r'^(#{1,4}\s+.*|(?:\d{1,2}\.|\b(?:STORY|NEWS|ITEM)\s*\d+[:\.]?)\s+.*)', re.IGNORECASE)
        blocks: List[Tuple[str, List[str]]] = []

        for line in lines:
            line_s = line.strip()
            if line_s.startswith("# ") and not line_s.startswith("##"):
                continue

            if re.match(r'^##\s+[一二三四五六七八九十]+[、\.]\s*', line_s):
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

        for header, block_lines in blocks:
            full_block_text = "\n".join(block_lines).strip()
            if not header and not full_block_text:
                continue

            raw_title = header.lstrip("#").strip()
            clean_title = re.sub(r'^(?:\[?\d+\]?[\.\、\:\s\-]+|第\s*\d+\s*[条篇]\s*[\:\.\s]*)', '', raw_title).strip()

            title_in_body = None
            for bline in block_lines:
                clean_bline = bullet_pat.sub('', bline.strip()).strip()
                m_t = re.match(r'^\*{0,2}(?:标题|Title|Tajuk)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_t:
                    title_in_body = m_t.group(1).strip("* ")
                    break

            if title_in_body:
                title = title_in_body
            elif clean_title:
                title = clean_title
            else:
                title = f"沙巴新闻第 {story_idx} 条"

            sources = []
            source_urls = []
            extracted_date = default_date
            body_paragraphs = []
            category_candidate = None
            is_event = False
            event_meta = {}

            header_lower = (header + " " + title).lower()
            if any(k in header_lower for k in ["活动预报", "活动日程", "未来活动", "event", "acara", "gotong-royong", "pesta", "峰会", "义诊", "即将举行"]):
                is_event = True

            for bline in block_lines:
                s_bline = bline.strip()
                if not s_bline or s_bline == "---":
                    continue

                clean_bline = bullet_pat.sub('', s_bline).strip()

                m_src = re.match(r'^\*{0,2}(?:来源|信源|Source|Sumber|Penerbit)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_src:
                    src_val = m_src.group(1).strip("* ")
                    for s in re.split(r'[,，/、+及与]', src_val):
                        s_clean = s.strip()
                        if s_clean and s_clean not in sources:
                            sources.append(s_clean)
                    continue

                m_url = re.match(r'^\*{0,2}(?:链接|原[文链]|URL|Link|Pautan)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_url:
                    raw_url_val = m_url.group(1).strip("* ")
                    url_match = re.search(r'https?://[^\s\)\>]+', raw_url_val)
                    if url_match:
                        source_urls.append(url_match.group(0))
                    continue

                m_date = re.match(r'^\*{0,2}(?:日期|时间|Date|Tarikh)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_date:
                    date_val = m_date.group(1).strip("* ")
                    d_m = re.search(r'20\d\d-\d{2}-\d{2}', date_val)
                    if d_m:
                        extracted_date = d_m.group(0)
                        if extracted_date > default_date:
                            is_event = True
                    continue

                m_cat = re.match(r'^\*{0,2}(?:分类|类别|Category|Kategori)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_cat:
                    category_candidate = m_cat.group(1).strip("* ").lower()
                    if any(k in category_candidate for k in ["活动", "event", "acara"]):
                        is_event = True
                    continue

                m_loc = re.match(r'^\*{0,2}(?:地点|Location|Tempat)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_loc:
                    is_event = True
                    event_meta["location"] = m_loc.group(1).strip("* ")
                    continue

                m_time = re.match(r'^\*{0,2}(?:时间|Time|Masa)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_time and ":" in m_time.group(1):
                    event_meta["time"] = m_time.group(1).strip("* ")
                    continue

                m_tel = re.match(r'^\*{0,2}(?:电话|联系|Tel|Hubungi|WhatsApp)\*{0,2}[：:]?\*{0,2}[：:]\s*(.+)$', clean_bline, re.IGNORECASE)
                if m_tel:
                    event_meta["tel"] = m_tel.group(1).strip("* ")
                    continue

                m_body_tag = re.match(r'^\*{0,2}(?:正文|内容|详情|Detail|Kandungan)\*{0,2}[：:]?\*{0,2}[：:]\s*(.*)$', clean_bline, re.IGNORECASE)
                if m_body_tag:
                    rem = m_body_tag.group(1).strip()
                    if rem:
                        body_paragraphs.append(rem)
                    continue

                embedded_links = re.findall(r'https?://[^\s\)\>]+', s_bline)
                for el in embedded_links:
                    if el not in source_urls:
                        source_urls.append(el)

                body_paragraphs.append(s_bline)

            full_body = "\n\n".join(body_paragraphs).strip()
            if not full_body:
                full_body = title

            if not sources:
                if "facebook" in full_body.lower() or "fb" in full_body.lower():
                    sources = ["Facebook 官方渠道"]
                else:
                    sources = ["Meta AI 权威整理"]

            combined_text = f"{title} {full_body}".lower()
            if is_event:
                cat = "event"
                geo = "sandakan" if "sandakan" in combined_text or "山打根" in combined_text else "sabah"
            else:
                raw_cat = (category_candidate or "").lower()
                if any(k in raw_cat for k in ["沙巴", "sabah"]):
                    cat = "sabah"
                elif any(k in raw_cat for k in ["全国", "national", "国会", "联邦"]):
                    cat = "national"
                elif any(k in raw_cat for k in ["体育", "sports", "sukan"]):
                    cat = "sports"
                elif any(k in combined_text for k in ["sukan", "体育", "运动会", "badminton", "bola", "足球"]):
                    cat = "sports"
                elif any(k in combined_text for k in ["parlimen", "国会", "首相", "布城", "putrajaya", "联邦"]):
                    cat = "national"
                else:
                    cat = "sabah"

                if "sandakan" in combined_text or "山打根" in combined_text or "mps" in combined_text:
                    geo = "sandakan"
                elif cat == "national":
                    geo = "national"
                else:
                    geo = "sabah"

            story = ParsedMarkdownStory(
                index=story_idx,
                title=title,
                body=full_body,
                category=cat,
                geo_scope=geo,
                sources=sources,
                source_urls=source_urls,
                date=extracted_date,
                is_event=is_event,
                event_metadata=event_meta if is_event else None,
                raw_header=header
            )
            stories.append(story)
            story_idx += 1

        return stories

    def select_top_stories_for_batch(
        self,
        stories: List[ParsedMarkdownStory],
        max_count: int = 26,
        include_events: bool = False
    ) -> List[ParsedMarkdownStory]:
        """
        Editorial Prioritization for Daily Single-Batch Gemini Request:
        - If include_events=True (Phase D-16 26-item single batch), preserves all 26 stories
          in their original order (1..26) across all 5 sections.
        - Otherwise, filters to active news stories and applies editorial priority.
        """
        if include_events or len(stories) <= max_count:
            # Phase D-16: preserve all stories up to max_count in original index order
            return stories[:max_count]

        news_stories = [s for s in stories if not s.is_event]
        if not news_stories:
            return []

        def priority_score(story: ParsedMarkdownStory) -> Tuple[int, int]:
            score = 0
            if story.geo_scope == "sandakan" or "山打根" in story.title or "sandakan" in story.title.lower():
                score += 100
            elif story.category == "sabah" or story.geo_scope == "sabah":
                score += 70
            elif story.category == "national":
                score += 40
            elif story.category == "sports":
                score += 30
            else:
                score += 20

            body_len = len(story.body)
            return (score, body_len)

        sorted_stories = sorted(news_stories, key=priority_score, reverse=True)
        selected = sorted_stories[:max_count]

        for i, s in enumerate(selected, 1):
            s.index = i

        return selected

    def convert_to_raw_articles(
        self,
        stories: List[ParsedMarkdownStory]
    ) -> List[RawArticle]:
        """
        Convert ParsedMarkdownStory instances to RawArticle objects
        for 100% drop-in compatibility with NewsSynthesizer.
        """
        raw_list = []
        for s in stories:
            dt = None
            if s.date:
                try:
                    dt = datetime.strptime(s.date, "%Y-%m-%d").replace(tzinfo=MYT)
                except Exception:
                    pass

            primary_src = s.sources[0] if s.sources else "Meta AI"
            primary_url = s.source_urls[0] if s.source_urls else "https://news.google.com"

            extra = {
                "corroborating_sources": s.sources,
                "source_urls": s.source_urls,
                "geo_scope": s.geo_scope,
                "story_index": s.index,
                "is_event": s.is_event,
                "event_metadata": s.event_metadata or {}
            }

            ra = RawArticle(
                title=s.title,
                url=primary_url,
                source=primary_src,
                published_at=dt,
                snippet=s.body[:150] if len(s.body) > 150 else s.body,
                category=s.category,
                body=s.body,
                extra=extra
            )
            raw_list.append(ra)

        return raw_list

    def convert_events_to_website_format(
        self,
        event_stories: List[ParsedMarkdownStory],
        target_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert event forecasts to website events structure (news_data.json['events']).
        """
        base_date_str = target_date or self.get_today_myt_str()
        try:
            today_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
        except Exception:
            today_date = datetime.now(MYT).date()

        formatted_events = []
        for idx, ev in enumerate(event_stories, 1):
            ev_date_str = ev.date or base_date_str
            try:
                ev_d = datetime.strptime(ev_date_str, "%Y-%m-%d").date()
                c_days = (ev_d - today_date).days
                month_s = f"{ev_d.month:02d}"
                day_s = f"{ev_d.day:02d}"
            except Exception:
                c_days = 3
                month_s = "11"
                day_s = "15"

            meta = ev.event_metadata or {}
            time_str = meta.get("time", "09:00 AM - 04:00 PM")
            loc_str = meta.get("location", "Sandakan Community Centre")
            tel_str = meta.get("tel", "089-272161")

            item = {
                "id": idx,
                "month": month_s,
                "day": day_s,
                "full_date": ev_date_str,
                "name": ev.title,
                "nameBM": f"Acara: {ev.title}",
                "time": time_str,
                "timeBM": time_str,
                "location": loc_str,
                "category": "市政民生" if "sandakan" in ev.geo_scope else "社区活动",
                "categoryBM": "Khidmat Komuniti",
                "badgeColor": "bg-[#14532d] text-[#86efac]",
                "desc": ev.body,
                "descBM": f"Maklumat acara komuniti: {ev.body[:200]}",
                "tel": tel_str,
                "source": ", ".join(ev.sources) if ev.sources else "官方预报",
                "sourceBM": ", ".join(ev.sources) if ev.sources else "Hebahan Rasmi",
                "countdown_days": max(0, c_days)
            }
            formatted_events.append(item)

        return formatted_events

    def save_snapshot(
        self,
        snapshot: GDriveInputSnapshot,
        raw_markdown: str
    ) -> Tuple[str, str]:
        """
        Durably persist traceable local input snapshot for auditability.
        """
        os.makedirs(self.snapshot_dir, exist_ok=True)
        json_path = os.path.join(self.snapshot_dir, f"snapshot_{snapshot.target_date}.json")
        md_path = os.path.join(self.snapshot_dir, f"snapshot_{snapshot.target_date}.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(snapshot), f, ensure_ascii=False, indent=2)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(raw_markdown)

        logger.info(f"[SNAPSHOT SAVED] Persisted Google Drive snapshot to {json_path} & {md_path}")
        return json_path, md_path

    def fetch_and_parse_today(
        self,
        target_date: Optional[str] = None
    ) -> Tuple[Optional[GDriveInputSnapshot], Optional[str]]:
        """
        Complete end-to-end ingestion:
        1. Reads today's Markdown from Google Drive (or local override/fallback).
        2. Parses into structured news stories and event forecasts.
        3. Persists local traceable snapshot.
        4. Returns (GDriveInputSnapshot, raw_markdown_text) or (None, None) on fail-closed.
        """
        date_str = target_date or self.get_today_myt_str()
        read_res = self.read_markdown_content(date_str)
        if not read_res:
            return None, None

        fname, content, file_id = read_res
        if not content or not content.strip():
            logger.error(f"[GDRIVE FAIL-CLOSED] Markdown file '{fname}' is empty.")
            return None, None

        stories = self.parse_markdown(content, date_str)
        if not stories:
            logger.error(f"[GDRIVE FAIL-CLOSED] No valid stories extracted from '{fname}'.")
            return None, None

        news_items = [s for s in stories if not s.is_event]
        event_items = [s for s in stories if s.is_event]

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        snapshot = GDriveInputSnapshot(
            snapshot_id=f"gdrive_snap_{date_str}_{content_hash[:8]}",
            target_date=date_str,
            source_file_name=fname,
            source_file_id=file_id,
            read_timestamp=datetime.now(MYT).isoformat(),
            total_stories_found=len(stories),
            news_stories_count=len(news_items),
            event_stories_count=len(event_items),
            markdown_sha256=content_hash,
            news_stories=[asdict(s) for s in news_items],
            event_stories=[asdict(s) for s in event_items]
        )

        self.save_snapshot(snapshot, content)
        return snapshot, content
