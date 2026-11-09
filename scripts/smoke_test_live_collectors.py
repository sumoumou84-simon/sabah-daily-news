#!/usr/bin/env python3
"""
Live Smoke Test for Sabah Tourism Board and Ticket2U Live Collectors
Performs real HTTP requests and records diagnostic metrics.
"""

import os
import sys
import json
from datetime import datetime

# Add root project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from event_engine.collectors.stb_collector import STBCollector
from event_engine.collectors.ticket2u_collector import Ticket2UCollector
from event_engine.engine import SandakanEventEngine
from event_engine.time_engine import MYT


def run_smoke_test():
    print("==================================================================")
    print(" LIVE SMOKE TEST — GENUINE HTTP EVENT COLLECTORS")
    print(f" Timestamp: {datetime.now(MYT).isoformat()}")
    print("==================================================================")

    # 1. Test Sabah Tourism Board Collector Live
    print("\n--- 1. SABAH TOURISM BOARD (STB) LIVE TEST ---")
    stb = STBCollector(timeout=10, max_retries=1, use_live_network=True)
    stb_index_fetch = stb.fetch_url(stb.base_url)
    print(f"STB Index URL: {stb.base_url}")
    print(f"STB HTTP Status: {stb_index_fetch.status_code}")
    print(f"STB Content Length: {len(stb_index_fetch.content) if stb_index_fetch.content else 0} bytes")
    if stb_index_fetch.error:
        print(f"STB Fetch Error: {stb_index_fetch.error}")

    # Discover and parse live
    stb_events = stb.collect()
    print(f"STB Events Discovered & Parsed for Sandakan: {len(stb_events)}")
    if stb_events:
        for idx, ev in enumerate(stb_events, 1):
            print(f"  [{idx}] {ev['official_name_en']} | Dates: {ev.get('start_date')} to {ev.get('end_date')} | Precision: {ev.get('time_precision')} | Venue: {ev.get('venue_name')}")
    if stb.collector_warnings:
        print(f"STB Warnings logged: {len(stb.collector_warnings)}")
        for w in stb.collector_warnings[:5]:
            print(f"  * {w}")

    # 2. Test Ticket2U Collector Live
    print("\n--- 2. TICKET2U MALAYSIA LIVE TEST ---")
    t2u = Ticket2UCollector(timeout=10, max_retries=1, use_live_network=True)
    t2u_home_fetch = t2u.fetch_url(t2u.base_url)
    print(f"Ticket2U Base URL: {t2u.base_url}")
    print(f"Ticket2U HTTP Status: {t2u_home_fetch.status_code}")
    print(f"Ticket2U Content Length: {len(t2u_home_fetch.content) if t2u_home_fetch.content else 0} bytes")

    # Probe Candidate URL live
    cand_url = "https://www.ticket2u.com.my/event/38600"
    t2u_cand_fetch = t2u.fetch_url(cand_url)
    print(f"Candidate Event URL: {cand_url}")
    print(f"Candidate HTTP Status: {t2u_cand_fetch.status_code}")
    if t2u_cand_fetch.error:
        print(f"Candidate Fetch Result: {t2u_cand_fetch.error}")

    t2u_events = t2u.collect()
    print(f"Ticket2U Events Parsed: {len(t2u_events)}")
    if t2u.collector_warnings:
        print(f"Ticket2U Warnings logged: {len(t2u.collector_warnings)}")
        for w in t2u.collector_warnings:
            print(f"  * {w}")

    print("\n==================================================================")
    print(" LIVE SMOKE TEST COMPLETE")
    print("==================================================================")


if __name__ == "__main__":
    run_smoke_test()
