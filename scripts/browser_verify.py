#!/usr/bin/env python3
"""
Sandakan Events — Browser Verification Runner
Executes real Google Chrome in headless mode against a local HTTP server
to capture actual screenshot evidence across desktop, mobile, theme,
and feed states.
"""

import os
import sys
import time
import json
import shutil
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
PORT = 8989
BASE_URL = f"http://127.0.0.1:{PORT}"
OUT_DIR = os.path.abspath("reports/screenshots")
os.makedirs(OUT_DIR, exist_ok=True)


class QuietHTTPHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress console noise


def run_server():
    server = HTTPServer(("127.0.0.1", PORT), QuietHTTPHandler)
    server.serve_forever()


def capture_screenshot(url: str, output_path: str, width: int = 1440, height: int = 900):
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        "--virtual-time-budget=3000",
        f"--screenshot={output_path}",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        size_kb = os.path.getsize(output_path) / 1024
        print(f"  [OK] Captured: {os.path.basename(output_path)} ({width}x{height}, {size_kb:.1f} KB)")
        return True
    else:
        print(f"  [ERROR] Failed to capture: {output_path}. Err: {res.stderr}")
        return False


def main():
    if not os.path.exists(CHROME_PATH):
        print(f"Chrome executable not found at {CHROME_PATH}")
        sys.exit(1)

    print("==================================================================")
    print(" SANDAKAN EVENTS — REAL BROWSER VERIFICATION (GOOGLE CHROME)")
    print("==================================================================")

    # 1. Start HTTP Server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    print(f"Local test server listening at {BASE_URL}")

    # Ensure frontend feed exists
    from event_engine.frontend_adapter import export_frontend_feed
    export_frontend_feed("events_data.json", "events_frontend.json")

    results = []

    # 1. Desktop Dark Mode (Chinese)
    p1 = os.path.join(OUT_DIR, "01_desktop_dark_zh.png")
    results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=dark&lang=zh", p1, 1440, 900))

    # 2. Desktop Light Mode (Chinese)
    p2 = os.path.join(OUT_DIR, "02_desktop_light_zh.png")
    results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=light&lang=zh", p2, 1440, 900))

    # 3. Desktop Dark Mode (Bahasa Malaysia)
    p3 = os.path.join(OUT_DIR, "03_desktop_dark_bm.png")
    results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=dark&lang=BM", p3, 1440, 900))

    # 4. Mobile Viewport (iPhone / Pixel: 390x844)
    p4 = os.path.join(OUT_DIR, "04_mobile_dark_zh.png")
    results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=dark&lang=zh", p4, 390, 844))

    # 5. Mobile Viewport Light Mode (BM)
    p5 = os.path.join(OUT_DIR, "05_mobile_light_bm.png")
    results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=light&lang=BM", p5, 390, 844))

    # 6. Search Filter Verification
    p6_s = os.path.join(OUT_DIR, "08_desktop_search_filter.png")
    results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=dark&lang=zh&search=Marathon", p6_s, 1440, 900))

    # 7. Category Filter Verification
    p7_c = os.path.join(OUT_DIR, "09_desktop_category_filter.png")
    results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=dark&lang=zh&category=Sports%20Logistics%20%26%20Expo", p7_c, 1440, 900))

    # 8. Empty Feed State Verification
    shutil.copy("events_frontend.json", "events_frontend.json.bak")
    try:
        empty_payload = {
            "metadata": {"title": "Empty Feed", "total_approved_events": 0, "feed_valid": True},
            "events": []
        }
        with open("events_frontend.json", "w", encoding="utf-8") as f:
            json.dump(empty_payload, f)
        
        p6 = os.path.join(OUT_DIR, "06_desktop_empty_feed.png")
        results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=dark&lang=zh", p6, 1440, 900))
    finally:
        shutil.copy("events_frontend.json.bak", "events_frontend.json")

    # 9. Missing Feed State (404) Verification
    try:
        os.remove("events_frontend.json")
        p7 = os.path.join(OUT_DIR, "07_desktop_missing_feed_error.png")
        results.append(capture_screenshot(f"{BASE_URL}/events.html?theme=dark&lang=zh", p7, 1440, 900))
    finally:
        shutil.move("events_frontend.json.bak", "events_frontend.json")

    print("\n--- BROWSER VERIFICATION SUMMARY ---")
    print(f"Total Browser Render Captures: {len(results)}")
    print(f"Successful Captures: {sum(results)}/{len(results)}")
    print(f"Screenshots saved to: {OUT_DIR}")
    print("==================================================================")


if __name__ == "__main__":
    main()
