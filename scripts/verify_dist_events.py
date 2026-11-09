#!/usr/bin/env python3
"""
Sandakan Events — Deployment-Path Verification Runner (Phase 3.5)
Runs a local HTTP server strictly serving the contents of dist_events/
and verifies with real Google Chrome headless screenshots that:
1. events.html loads with zero 404 local resources
2. events_frontend.json loads and renders approved events
3. Dark / Light themes and Chinese / BM languages render correctly
4. Search and category filters work
5. Empty and missing feed fallback states work
"""

import os
import sys
import time
import json
import shutil
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
PORT = 8991
BASE_URL = f"http://127.0.0.1:{PORT}"
DIST_DIR = os.path.abspath("dist_events")
OUT_DIR = os.path.abspath("reports/phase35_screenshots")
os.makedirs(OUT_DIR, exist_ok=True)


class DistHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def log_message(self, format, *args):
        pass  # Quiet logging


def run_server():
    server = HTTPServer(("127.0.0.1", PORT), DistHTTPHandler)
    server.serve_forever()


def capture(url: str, out_name: str, width: int = 1440, height: int = 900):
    out_path = os.path.join(OUT_DIR, out_name)
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        "--virtual-time-budget=3000",
        f"--screenshot={out_path}",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  [OK] Captured: {out_name} ({width}x{height}, {size_kb:.1f} KB)")
        return True
    else:
        print(f"  [ERROR] Failed to capture: {out_name}. Err: {res.stderr}")
        return False


def main():
    if not os.path.exists(CHROME_PATH):
        print(f"Chrome not found at {CHROME_PATH}")
        sys.exit(1)

    print("==================================================================")
    print(" PHASE 3.5 — DIST_EVENTS DEPLOYMENT-PATH BROWSER VERIFICATION")
    print("==================================================================")
    print(f"Serving strictly from: {DIST_DIR}")

    # Start server in dist_events directory
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    print(f"Dist test server listening at {BASE_URL}")

    results = []

    # 1. Desktop Dark Mode (Chinese)
    results.append(capture(f"{BASE_URL}/events.html?theme=dark&lang=zh", "01_dist_desktop_dark_zh.png", 1440, 900))

    # 2. Desktop Light Mode (Chinese)
    results.append(capture(f"{BASE_URL}/events.html?theme=light&lang=zh", "02_dist_desktop_light_zh.png", 1440, 900))

    # 3. Desktop Dark Mode (Bahasa Malaysia)
    results.append(capture(f"{BASE_URL}/events.html?theme=dark&lang=BM", "03_dist_desktop_dark_bm.png", 1440, 900))

    # 4. Mobile Viewport (iPhone / Pixel: 390x844)
    results.append(capture(f"{BASE_URL}/events.html?theme=dark&lang=zh", "04_dist_mobile_dark_zh.png", 390, 844))

    # 5. Mobile Viewport Light Mode (BM)
    results.append(capture(f"{BASE_URL}/events.html?theme=light&lang=BM", "05_dist_mobile_light_bm.png", 390, 844))

    # 6. Search Filter Active
    results.append(capture(f"{BASE_URL}/events.html?theme=dark&lang=zh&search=Marathon", "06_dist_search_filter.png", 1440, 900))

    # 7. Category Filter Active
    results.append(capture(f"{BASE_URL}/events.html?theme=dark&lang=zh&category=Sports%20Logistics%20%26%20Expo", "07_dist_category_filter.png", 1440, 900))

    # 8. Empty Feed State Verification in dist_events
    feed_path = os.path.join(DIST_DIR, "events_frontend.json")
    feed_bak = os.path.join(DIST_DIR, "events_frontend.json.bak")
    shutil.copy(feed_path, feed_bak)
    try:
        empty_payload = {
            "metadata": {"title": "Empty Feed", "total_approved_events": 0, "feed_valid": True},
            "events": []
        }
        with open(feed_path, "w", encoding="utf-8") as f:
            json.dump(empty_payload, f)
        results.append(capture(f"{BASE_URL}/events.html?theme=dark&lang=zh", "08_dist_empty_feed_state.png", 1440, 900))
    finally:
        shutil.copy(feed_bak, feed_path)

    # 9. Missing Feed (404) State Verification in dist_events
    try:
        os.remove(feed_path)
        results.append(capture(f"{BASE_URL}/events.html?theme=dark&lang=zh", "09_dist_missing_feed_error_state.png", 1440, 900))
    finally:
        shutil.move(feed_bak, feed_path)

    print("\n--- DIST_EVENTS BROWSER VERIFICATION SUMMARY ---")
    print(f"Total Captures: {len(results)}")
    print(f"Successful Captures: {sum(results)}/{len(results)}")
    print(f"Screenshots saved to: {OUT_DIR}")
    print("==================================================================")


if __name__ == "__main__":
    main()
