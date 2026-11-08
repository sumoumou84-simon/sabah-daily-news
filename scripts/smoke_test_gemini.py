#!/usr/bin/env python3
"""
scripts/smoke_test_gemini.py
Isolated Gemini API smoke test entry point for Sabah Daily News.
Enforces:
- Independent of agent_reach_editor.py and news pipeline.
- Single candidate model: gemini-3.5-flash-lite.
- Default mode: Safe (0 HTTP requests).
- Real HTTP request requires explicit flag: --execute-authorized-test.
- Strict write-ahead remote quota reservation via QuotaManager before sending HTTP packet.
- Fails closed on missing, corrupted, or inaccessible remote state.
- Zero retries. Zero alternate models. Zero refunds on error or timeout.
- Never prints credentials or response bodies.
- Zero modifications to news_data.json, index.html, or production publishing artifacts.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.synthesizer import QuotaManager, MYT_TZ

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scripts.smoke_test_gemini")

CANDIDATE_MODEL = "gemini-3.5-flash-lite"


def mask_key(key: Optional[str]) -> str:
    """Safely mask key for diagnostic logs without leaking value."""
    if not key:
        return "<NONE>"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def run_gemini_smoke_test(
    execute: bool = False,
    config: Optional[Dict[str, Any]] = None,
    api_key_override: Optional[str] = None,
    execution_mode_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute isolated Gemini smoke test with strict quota safety.
    Returns diagnostic summary dictionary.
    """
    result: Dict[str, Any] = {
        "status": "NOT_RUN",
        "model": CANDIDATE_MODEL,
        "execute_flag": execute,
        "reservation_id": None,
        "quota_reserved": False,
        "http_request_attempted": False,
        "http_code": None,
        "error": None
    }

    # 1. Default safe mode check
    if not execute:
        logger.info("[SAFE DEFAULT] Execute flag not set. Running in dry-run mode (0 HTTP requests).")
        result["status"] = "DRY_RUN_SAFE"
        return result

    # 2. Credential availability check
    api_key = api_key_override or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or not api_key.strip():
        logger.warning("[ABORT] No Gemini API key detected in environment. Emitting 0 HTTP requests.")
        result["status"] = "ABORTED_NO_CREDENTIALS"
        result["error"] = "No API key configured"
        return result

    api_key = api_key.strip()

    # 3. Initialize QuotaManager with candidate model
    cfg = config or {}
    if "gemini_quota" not in cfg:
        cfg["gemini_quota"] = {}
    cfg["gemini_quota"]["candidate_models"] = [CANDIDATE_MODEL]
    cfg["gemini_quota"]["daily_request_limit"] = 5
    cfg["gemini_quota"]["per_run_request_limit"] = 1

    qm = QuotaManager(
        cfg,
        execution_mode_override=execution_mode_override
    )

    # 4. Durable Write-Ahead Reservation Gate
    logger.info(f"[QUOTA GATE] Attempting write-ahead reservation for model '{CANDIDATE_MODEL}'...")
    reservation = qm.reserve_slot(CANDIDATE_MODEL)
    if not reservation:
        logger.error("[QUOTA GATE DENIED] Remote reservation failed, state missing/corrupt, or quota exhausted. Aborting.")
        result["status"] = "ABORTED_RESERVATION_FAILED"
        result["error"] = "Quota reservation rejected by QuotaManager"
        return result

    res_id = reservation["reservation_id"]
    result["reservation_id"] = res_id
    result["quota_reserved"] = True
    logger.info(f"[QUOTA GATE GRANTED] Reservation secured: {res_id}")

    # 5. Dispatch EXACTLY ONE minimal HTTP ping request
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{CANDIDATE_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Respond with PONG"}]}]
    }

    result["http_request_attempted"] = True
    logger.info(f"[HTTP DISPATCH] Sending exactly ONE ping request to {CANDIDATE_MODEL} (timeout=15s)...")

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            http_code = resp.getcode()
            result["http_code"] = http_code
            result["status"] = "SUCCESS"
            qm.finalize_slot(res_id, "COMPLETED")
            logger.info(f"[HTTP SUCCESS] Received HTTP {http_code}. Quota slot finalized as COMPLETED.")
            return result

    except urllib.error.HTTPError as e:
        result["http_code"] = e.code
        result["status"] = f"FAILED_HTTP_{e.code}"
        result["error"] = f"HTTP Error {e.code}"
        qm.finalize_slot(res_id, f"FAILED_HTTP_{e.code}")
        logger.warning(f"[HTTP ERROR] Received HTTP {e.code}. Quota slot permanently consumed (no refund).")
        return result

    except urllib.error.URLError as e:
        result["status"] = "FAILED_TIMEOUT_OR_NETWORK"
        result["error"] = str(e.reason)
        qm.finalize_slot(res_id, "FAILED_TIMEOUT_OR_NETWORK")
        logger.warning(f"[NETWORK ERROR] Network or timeout error: {e.reason}. Quota slot permanently consumed.")
        return result

    except Exception as e:
        result["status"] = "FAILED_UNEXPECTED"
        result["error"] = str(e)
        qm.finalize_slot(res_id, "FAILED_UNEXPECTED")
        logger.warning(f"[UNEXPECTED ERROR] Unexpected failure: {e}. Quota slot permanently consumed.")
        return result


def main():
    parser = argparse.ArgumentParser(description="Isolated Gemini Smoke Test Entry Point")
    parser.add_argument(
        "--execute-authorized-test",
        action="store_true",
        help="Explicit flag required to authorize sending a real HTTP request."
    )
    args = parser.parse_args()

    res = run_gemini_smoke_test(execute=args.execute_authorized_test)
    print("\n=== GEMINI SMOKE TEST DIAGNOSTIC REPORT ===")
    print(f"Status:                 {res['status']}")
    print(f"Model:                  {res['model']}")
    print(f"Execute Flag:           {res['execute_flag']}")
    print(f"Quota Reserved:         {res['quota_reserved']}")
    print(f"Reservation ID:         {res['reservation_id']}")
    print(f"HTTP Attempted:         {res['http_request_attempted']}")
    print(f"HTTP Code:              {res['http_code']}")
    print(f"Error Diagnostic:       {res['error']}")
    print("===========================================\n")

    if res["status"] in ("SUCCESS", "DRY_RUN_SAFE"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
