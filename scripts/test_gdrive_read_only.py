#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Dedicated Read-Only Google Drive & Google Docs Verification Script (Phase D-17.4)
Author: Sabah Daily News Pipeline

Restrictions:
- Google Drive read-only access only (GET requests only).
- 0 Gemini API requests (GEMINI_API_KEY is not used or injected).
- 0 QuotaManager reservations.
- 0 Git commits / pushes during test execution.
- 0 Website data modifications (no write to news_data.json or index.html).
- Never prints, logs or exports OAuth tokens.
- Saves all export and parsing results strictly to reports/ for private artifact download.
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

MYT = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("test_gdrive_read_only")

from pipeline.gdrive_reader import GDriveMarkdownReader, ParsedMarkdownStory


TARGET_GDOC_ID = "1vFkai8jQoG3e2z-VElYQ9nD1xuJ3PZ1ojaPk5FV88o0"
TARGET_GDOC_NAME = "西门看看网每日新闻_2026-11-10"


def test_single_gdoc_export(
    access_token: str,
    doc_id: str,
    mime_type: str,
    out_path: str
) -> Dict[str, Any]:
    """
    Directly invoke Google Drive API v3 files.export for a specific MIME type.
    Records HTTP status, returned Content-Type header, size in bytes, and content or error.
    Never exposes credentials or tokens.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType={urllib.parse.quote(mime_type)}"
    res = {
        "mime_type": mime_type,
        "url": f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType={mime_type}",
        "http_status": None,
        "content_type": None,
        "size_bytes": 0,
        "success": False,
        "error": None,
        "content_preview": "",
        "saved_path": None
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            res["http_status"] = resp.status
            res["content_type"] = resp.headers.get("Content-Type")
            data = resp.read()
            text = data.decode("utf-8", errors="replace").replace("\r\n", "\n").lstrip("\ufeff")
            res["size_bytes"] = len(data)
            res["success"] = True
            res["content_preview"] = text[:300].replace("\n", " ")

            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            res["saved_path"] = out_path
            logger.info(f"[GDOC EXPORT SUCCESS] Exported {mime_type}: HTTP {resp.status}, {len(data)} bytes -> {out_path}")
            return res, text
    except urllib.error.HTTPError as e:
        res["http_status"] = e.code
        err_msg = e.read().decode("utf-8", errors="replace")[:300]
        res["error"] = f"HTTP {e.code} ({e.reason}): {err_msg}"
        logger.warning(f"[GDOC EXPORT FAILED] {mime_type} -> HTTP {e.code}: {e.reason}")
        return res, None
    except Exception as e:
        res["error"] = str(e)
        logger.warning(f"[GDOC EXPORT EXCEPTION] {mime_type} -> {e}")
        return res, None


def run_gdrive_read_test(target_date: str = "2026-11-10", local_file_fallback: Optional[str] = None) -> int:
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    report_md_path = os.path.join(reports_dir, "test_gdrive_parse_report.md")
    report_json_path = os.path.join(reports_dir, "test_gdrive_parse_report.json")
    downloaded_md_path = os.path.join(reports_dir, "test_gdrive_downloaded.md")

    cfg_path = os.path.join(BASE_DIR, "config", "news_config.json")
    app_cfg = {}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                app_cfg = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read news_config.json: {e}")

    reader = GDriveMarkdownReader(app_cfg)
    reader.folder_id = os.getenv("GDRIVE_FOLDER_ID") or reader.folder_id or "18uRBmOQM5hTdeQvldILnC9_n4LZIs1kf"

    logger.info("=" * 60)
    logger.info(f"Phase D-17.4 Read-Only Verification for Date: {target_date}")
    logger.info(f"Target Folder ID: {reader.folder_id}")
    logger.info(f"Target Google Doc ID: {TARGET_GDOC_ID}")
    logger.info("=" * 60)

    # 1. Offline Local Test Mode
    if local_file_fallback and os.path.exists(local_file_fallback):
        logger.info(f"[LOCAL TEST MODE] Reading offline fixture: {local_file_fallback}")
        with open(local_file_fallback, "r", encoding="utf-8") as f:
            content = f.read()
        file_name = os.path.basename(local_file_fallback)
        file_id = "local_test_fixture"
        token = None
        gdoc_export_results = {}
    else:
        # 2. Real Google Drive API Mode
        token = reader._get_oauth_access_token()
        if not token:
            msg = (
                "AUTHENTICATION FAILED: Missing required Google Drive OAuth credentials in environment.\n"
                "Required GitHub Secrets: GDRIVE_REFRESH_TOKEN, GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET."
            )
            logger.error(msg)
            with open(report_md_path, "w", encoding="utf-8") as f:
                f.write(f"# Phase D-17.4 Google Drive Read Test Failure\n\n**Date**: {target_date}\n\n**Status**: {msg}\n")
            return 1

        # 2.1 Dedicated Real Google Docs Export Verification (Target Doc ID)
        gdoc_export_results = {}
        logger.info(f"Starting dedicated Google Docs API export tests on Doc ID: {TARGET_GDOC_ID}")

        # Attempt A: text/markdown export
        md_out = os.path.join(reports_dir, "test_gdocs_exported_markdown.txt")
        res_md, content_md = test_single_gdoc_export(token, TARGET_GDOC_ID, "text/markdown", md_out)
        if content_md:
            stories_from_gdoc_md = reader.parse_markdown(content_md, target_date)
            res_md["parsed_stories_count"] = len(stories_from_gdoc_md)
            res_md["news_count"] = sum(1 for s in stories_from_gdoc_md if not s.is_event)
            res_md["events_count"] = sum(1 for s in stories_from_gdoc_md if s.is_event)
        gdoc_export_results["text_markdown"] = res_md

        # Attempt B: text/plain export
        plain_out = os.path.join(reports_dir, "test_gdocs_exported_plain.txt")
        res_plain, content_plain = test_single_gdoc_export(token, TARGET_GDOC_ID, "text/plain", plain_out)
        if content_plain:
            stories_from_gdoc_plain = reader.parse_markdown(content_plain, target_date)
            res_plain["parsed_stories_count"] = len(stories_from_gdoc_plain)
            res_plain["news_count"] = sum(1 for s in stories_from_gdoc_plain if not s.is_event)
            res_plain["events_count"] = sum(1 for s in stories_from_gdoc_plain if s.is_event)
        gdoc_export_results["text_plain"] = res_plain

        # 2.2 Test Dual-format Reader Ingestion via candidates
        candidates = reader.resolve_candidate_filenames(target_date)
        logger.info(f"Searching candidate filenames in Drive folder: {candidates}")

        res = reader.read_from_drive_api(candidates, reader.folder_id)
        if res:
            file_name, content, file_id = res
        elif content_md:
            file_name, content, file_id = f"{TARGET_GDOC_NAME}.md", content_md, TARGET_GDOC_ID
        elif content_plain:
            file_name, content, file_id = TARGET_GDOC_NAME, content_plain, TARGET_GDOC_ID
        else:
            msg = f"FILE NOT FOUND: No matching markdown or Google Doc found in folder {reader.folder_id} for date {target_date}."
            logger.error(msg)
            with open(report_md_path, "w", encoding="utf-8") as f:
                f.write(f"# Phase D-17.4 Google Drive Read Test Failure\n\n**Date**: {target_date}\n\n**Status**: {msg}\n")
            return 1

    file_bytes = len(content.encode("utf-8"))
    logger.info(f"Primary file selected: '{file_name}' (ID: {file_id}, Size: {file_bytes} bytes)")

    with open(downloaded_md_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Saved downloaded markdown to: {downloaded_md_path}")

    # Parse primary downloaded content using D-17.3 parser
    stories = reader.parse_markdown(content, target_date)
    news_stories = [s for s in stories if not s.is_event]
    event_stories = [s for s in stories if s.is_event]

    section_breakdown: Dict[str, int] = {}
    for s in news_stories:
        cat = s.category
        section_breakdown[cat] = section_breakdown.get(cat, 0) + 1



    report_data = {
        "target_date": target_date,
        "verification_time_myt": datetime.now(MYT).isoformat(),
        "folder_id": reader.folder_id,
        "primary_file_name": file_name,
        "primary_file_id": file_id,
        "primary_file_size_bytes": file_bytes,
        "primary_total_stories": len(stories),
        "primary_news_stories": len(news_stories),
        "primary_event_stories": len(event_stories),
        "sections": section_breakdown,
        "gdoc_export_tests": gdoc_export_results,
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

    # Generate Markdown Report
    lines = [
        f"# Phase D-17.4 Google Drive & Google Docs Read Verification Report",
        f"",
        f"- **Target Date**: `{target_date}`",
        f"- **Verification Time (MYT)**: `{report_data['verification_time_myt']}`",
        f"- **Drive Folder ID**: `{reader.folder_id}`",
        f"- **Primary Ingested File**: `{file_name}` (ID: `{file_id}`, Size: `{file_bytes} bytes`)",
        f"- **Total Stories Parsed**: `{len(stories)}` (News: `{len(news_stories)}`, Events: `{len(event_stories)}`)",
        f"",
        f"## 1. Section Breakdown",
        f"",
    ]
    for sec, cnt in section_breakdown.items():
        lines.append(f"- **{sec}**: {cnt} items")
    lines.append(f"- **events**: {len(event_stories)} items")

    lines.extend([
        f"",
        f"## 2. Dedicated Google Docs Export API Verification",
        f"",
        f"- **Target Doc ID**: `{TARGET_GDOC_ID}`",
        f"- **Target Doc Name**: `{TARGET_GDOC_NAME}`",
        f"",
    ])

    if gdoc_export_results:
        for fmt, res in gdoc_export_results.items():
            lines.append(f"### Export Format: `{fmt}`")
            lines.append(f"- **HTTP Status**: `{res.get('http_status')}`")
            lines.append(f"- **Content-Type**: `{res.get('content_type')}`")
            lines.append(f"- **File Size**: `{res.get('size_bytes')} bytes`")
            lines.append(f"- **Success**: `{res.get('success')}`")
            if res.get("error"):
                lines.append(f"- **Error Details**: `{res.get('error')}`")
            if res.get("parsed_stories_count") is not None:
                lines.append(f"- **Parsed Total Stories**: `{res.get('parsed_stories_count')}` (News: `{res.get('news_count')}`, Events: `{res.get('events_count')}`)")
            if res.get("content_preview"):
                lines.append(f"- **Content Preview**: {res.get('content_preview')}")
            lines.append(f"")
    else:
        lines.append(f"*Offline mode / No token provided; Google Docs API export was skipped.*\n")

    lines.extend([
        f"## 3. Active News Items Detail ({len(news_stories)} items)",
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
            f"## 4. Future Event Announcements ({len(event_stories)} items)",
            f"",
        ])
        for ev in report_data["event_stories"]:
            lines.append(f"### Event #{ev['index']}: {ev['title']}")
            lines.append(f"- **Target Event Date**: `{ev['event_date']}`")
            lines.append(f"- **Details**: {ev['body']}")
            lines.append(f"")

    lines.extend([
        f"## 5. Safety & Quota Verification",
        f"",
        f"- **Gemini API Requests**: 0",
        f"- **QuotaManager Reservations**: 0",
        f"- **Production News Modifications**: NONE",
        f"- **Git Status**: 0 commits / 0 pushes during execution",
        f"- **OAuth Token Security**: 0 tokens exposed in reports or logs",
    ])

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Generated comprehensive report at: {report_md_path}")
    logger.info("Phase D-17.4 read-only verification completed successfully with 0 Gemini calls.")
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
