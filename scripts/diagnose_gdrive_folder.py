#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Google Drive Folder Inventory Diagnostic (Phase D-15.3)
STRICTLY READ-ONLY DIAGNOSTIC SCRIPT (REVISED)

Purpose:
- Specifically inspect ONLY the two candidate Folder IDs:
  1) 18uRBmOQM5hTdeQvldILnC9_n4LZIs1kf (lowercase letter 'l')
  2) 18uRBmOQM5hTdeQv1dILnC9_n4LZIs1kf (digit '1')
- List all direct children inside each folder (strictly direct children only, NO global search).
- Check: file name, MIME type, File ID, created time, modified time, size, parents.
- Determine which Folder ID is the authentic folder.
- Check whether 2026-11-10 Markdown file or Google Doc exists.
Restrictions:
- STRICTLY READ-ONLY: Never modify, delete, upload or rename Drive files.
- Do NOT download or read article body content.
- 0 Global account search.
- 0 Gemini API calls. 0 QuotaManager reservations.
- 0 Production website modifications.
"""

import os
import sys
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MYT = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("diagnose_gdrive_folder")


def get_oauth_access_token() -> Optional[str]:
    refresh_token = os.getenv("GDRIVE_REFRESH_TOKEN", "").strip()
    client_id = os.getenv("GDRIVE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GDRIVE_CLIENT_SECRET", "").strip()

    if not (refresh_token and client_id and client_secret):
        logger.error("[AUTH ERROR] Missing one or more of GDRIVE_REFRESH_TOKEN, GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET")
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
                logger.info("[AUTH SUCCESS] Successfully obtained OAuth access token.")
                return access_token
    except Exception as e:
        logger.error(f"[AUTH ERROR] Failed to exchange refresh token: {e}")
    return None


def inspect_single_folder(access_token: str, folder_id: str, label: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    result = {
        "folder_id": folder_id,
        "label": label,
        "accessible": False,
        "folder_metadata": None,
        "error": None,
        "files_count": 0,
        "files": []
    }

    # 1. Fetch Folder Metadata
    f_url = f"https://www.googleapis.com/drive/v3/files/{folder_id}?fields=id,name,mimeType,trashed,parents"
    try:
        req = urllib.request.Request(f_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            f_meta = json.loads(resp.read().decode("utf-8"))
            result["accessible"] = True
            result["folder_metadata"] = f_meta
            logger.info(f"Folder '{folder_id}' [{label}] ACCESSIBLE: Name='{f_meta.get('name')}', MimeType='{f_meta.get('mimeType')}'")
    except urllib.error.HTTPError as e:
        result["error"] = f"HTTP {e.code}: {e.reason}"
        logger.warning(f"Folder '{folder_id}' [{label}] NOT accessible: HTTP {e.code} {e.reason}")
        return result
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Folder '{folder_id}' [{label}] check error: {e}")
        return result

    # 2. Query Strictly Direct Children Files
    # (Strict read-only query; NO global search, NO download of file bodies)
    query = f"'{folder_id}' in parents and trashed = false"
    list_url = f"https://www.googleapis.com/drive/v3/files?q={urllib.parse.quote(query)}&fields=files(id,name,mimeType,size,modifiedTime,createdTime,parents)&pageSize=100"

    try:
        req = urllib.request.Request(list_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_files = data.get("files", [])
            result["files_count"] = len(raw_files)

            for f in raw_files:
                name = f.get("name", "")
                mime = f.get("mimeType", "")
                is_gdoc = (mime == "application/vnd.google-apps.document")
                is_md = name.lower().endswith(".md") or mime in ["text/markdown", "text/plain"]
                doc_type = "Google Docs Document" if is_gdoc else ("Markdown File" if is_md else f"Other ({mime})")

                result["files"].append({
                    "id": f.get("id"),
                    "name": name,
                    "mime_type": mime,
                    "doc_type": doc_type,
                    "is_google_doc": is_gdoc,
                    "is_markdown": is_md,
                    "size_bytes": f.get("size", "N/A"),
                    "created_time": f.get("createdTime"),
                    "modified_time": f.get("modifiedTime"),
                    "parents": f.get("parents", []),
                    "contains_2026_11_10": "2026-11-10" in name
                })
            logger.info(f"Listed {len(raw_files)} direct children files inside '{folder_id}'.")
    except Exception as e:
        result["error"] = f"List files error: {e}"
        logger.error(f"Error listing direct children in folder '{folder_id}': {e}")

    return result


def run_diagnosis() -> int:
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    json_report_path = os.path.join(reports_dir, "gdrive_inventory_report.json")
    md_report_path = os.path.join(reports_dir, "gdrive_inventory_report.md")

    target_date = "2026-11-10"
    candidates = [
        ("18uRBmOQM5hTdeQvldILnC9_n4LZIs1kf", "候选 A（小写字母 l）"),
        ("18uRBmOQM5hTdeQv1dILnC9_n4LZIs1kf", "候选 B（数字 1）")
    ]

    logger.info("=" * 70)
    logger.info("Phase D-15.3 Google Drive Folder Inventory Diagnosis (Strict Read-Only)")
    logger.info("=" * 70)

    token = get_oauth_access_token()
    if not token:
        logger.error("DIAGNOSIS ABORTED: Google Drive credentials not available in environment.")
        with open(md_report_path, "w", encoding="utf-8") as f:
            f.write("# Phase D-15.3 Google Drive Inventory Diagnosis: FAILED\n\nReason: Missing credentials in environment.\n")
        return 1

    diagnosis_data = {
        "diagnosis_timestamp": datetime.now(MYT).isoformat(),
        "target_date": target_date,
        "folders": {}
    }

    for fid, label in candidates:
        logger.info(f"Inspecting candidate folder: {fid} ({label})")
        diagnosis_data["folders"][fid] = inspect_single_folder(token, fid, label)

    # Save JSON report
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(diagnosis_data, f, ensure_ascii=False, indent=2)

    # Build Markdown report
    lines = [
        "# Phase D-15.3 Google Drive 目录清单诊断报告 (Strict Read-Only)",
        "",
        f"- **诊断时间**: `{diagnosis_data['diagnosis_timestamp']}` (MYT)",
        f"- **目标核验日期**: `{target_date}`",
        f"- **OAuth 认证状态**: `SUCCESS`",
        "",
        "## 1. 两个候选 Folder ID 对比与可访问性",
        "",
        "| 候选 Folder ID | 标识说明 | 是否可访问 | 真实名称 | 直属文件总数 | 状态详情 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for fid, finfo in diagnosis_data["folders"].items():
        accessible = "✅ 正常可访问" if finfo["accessible"] else "❌ 无法访问"
        f_meta = finfo.get("folder_metadata") or {}
        f_name = f_meta.get("name", "N/A")
        cnt = finfo["files_count"]
        err = finfo["error"] or "OK"
        lines.append(f"| `{fid}` | {finfo['label']} | {accessible} | `{f_name}` | {cnt} | {err} |")

    lines.extend([
        "",
        "## 2. 各文件夹直属文件清单 (Direct Children Files)",
        ""
    ])

    for fid, finfo in diagnosis_data["folders"].items():
        lines.append(f"### 文件夹: `{fid}` — {finfo['label']}")
        if not finfo["accessible"]:
            lines.append(f"*该文件夹无法访问: {finfo['error']}*")
            lines.append("")
            continue

        files = finfo.get("files", [])
        if not files:
            lines.append("*该文件夹为空，无任何直属文件。*")
            lines.append("")
            continue

        lines.append("| # | 文件名 | File ID | MIME 类型 | 文档类型 | 大小(字节) | 创建时间 | 修改时间 | 是否含 2026-11-10 |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for idx, f in enumerate(files, 1):
            is_match = "⭐ 是" if f["contains_2026_11_10"] else "否"
            lines.append(
                f"| {idx} | `{f['name']}` | `{f['id']}` | `{f['mime_type']}` | {f['doc_type']} | "
                f"{f['size_bytes']} | {f['created_time']} | {f['modified_time']} | {is_match} |"
            )
        lines.append("")

    lines.extend([
        "## 3. 2026-11-10 目标文件匹配与分析",
        ""
    ])

    # Analyze 2026-11-10 specifically
    found_any_target = False
    for fid, finfo in diagnosis_data["folders"].items():
        if not finfo["accessible"]:
            continue
        matches = [f for f in finfo.get("files", []) if f["contains_2026_11_10"]]
        if matches:
            found_any_target = True
            lines.append(f"#### 在 `{fid}` ({finfo['label']}) 中匹配到的 2026-11-10 相关文件：")
            for m in matches:
                exact_flag = "【精确匹配目标 Markdown】" if m['name'] == f"西门看看网每日新闻_{target_date}.md" else ""
                lines.append(f"- **文件名**: `{m['name']}` {exact_flag}")
                lines.append(f"  - **File ID**: `{m['id']}`")
                lines.append(f"  - **文档类型**: {m['doc_type']} (`{m['mime_type']}`) - 是否真实 Markdown: `{'是' if m['is_markdown'] else '否'}`")
                lines.append(f"  - **创建时间**: `{m['created_time']}`")
                lines.append(f"  - **修改时间**: `{m['modified_time']}`")
            lines.append("")

    if not found_any_target:
        lines.append("> **结论**: 在两个候选文件夹中均未发现任何包含 `2026-11-10` 的文件。")
        lines.append("")

    lines.extend([
        "## 4. 安全合规确认",
        "",
        "- 全账户 Global Search: 否 (已完全禁用，严格只查直属父目录)",
        "- 新闻正文读取: 否 (仅读取元数据，未下载正文)",
        "- Google Drive 修改/移动/删除: 0 次 (严格只读)",
        "- Gemini API 调用: 0 次",
        "- QuotaManager 配额占用: 0 次",
        "- 生产数据及网站变动: 0 次"
    ])

    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Diagnostic report written to: {md_report_path}")
    logger.info("Phase D-15.3 Diagnosis completed cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(run_diagnosis())
