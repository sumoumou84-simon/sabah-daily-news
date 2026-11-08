import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("pipeline.circuit_breaker")

class CircuitBreakerException(Exception):
    """Raised when publication sanity checks fail to prevent corrupted production deployments."""
    pass

class CircuitBreaker:
    def __init__(self, min_threshold: int = 10):
        self.min_threshold = min_threshold

    def inspect_and_guard(
        self,
        today_iso: str,
        new_headlines: List[Dict[str, Any]],
        existing_news_file: str,
        existing_archive_file: str
    ) -> bool:
        """
        Non-destructive Hard Barrier:
        1. Checks len(new_headlines) >= min_threshold.
        2. Checks that new_headlines are not empty.
        3. Checks that new_headlines do not 100% duplicate yesterday's headlines.
        If any check fails:
           - Immediately raises CircuitBreakerException.
           - Leaves existing news_data.json and index.html 100% intact.
        """
        count = len(new_headlines)
        logger.info(f"Circuit Breaker checking publication payload: {count} articles")

        # 1. Minimum Threshold Check
        if count < self.min_threshold:
            err_msg = (
                f"🚨 [CIRCUIT BREAKER TRIGGERED] Article count ({count}) is below minimum safety threshold ({self.min_threshold})! "
                f"ABORTING publication to prevent blank frontpage incident. Existing production edition preserved."
            )
            logger.critical(err_msg)
            raise CircuitBreakerException(err_msg)

        # 2. Check against yesterday's duplicate trap
        if os.path.exists(existing_news_file):
            try:
                with open(existing_news_file, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    old_date = old_data.get("date")
                    old_headlines = old_data.get("headlines", [])

                    if old_date != today_iso and old_headlines:
                        old_titles = {h.get("title", "").strip() for h in old_headlines if h.get("title")}
                        new_titles = {h.get("title", "").strip() for h in new_headlines if h.get("title")}
                        
                        overlap = old_titles & new_titles
                        if len(overlap) == len(new_titles) and len(new_titles) > 0:
                            err_msg = (
                                f"🚨 [CIRCUIT BREAKER TRIGGERED] New payload is a 100% duplicate of previous day ({old_date})! "
                                f"ABORTING publication to prevent stale re-publication."
                            )
                            logger.critical(err_msg)
                            raise CircuitBreakerException(err_msg)
            except CircuitBreakerException:
                raise
            except Exception as e:
                logger.warning(f"Circuit breaker could not read existing file for comparison: {e}")

        logger.info("✅ Circuit Breaker checks passed successfully. Safe to publish.")
        return True
