import os
import re
import json
import time
import uuid
import urllib.request
import urllib.error
import subprocess
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from collectors.base import RawArticle
from pipeline.fact_verifier import BilingualFactValidator, WEEKDAY_ZH_MAP, WEEKDAY_BM_MAP
from pipeline.fact_schema import (
    StructuredArticle,
    HeadlineRecord,
    ClaimRecord,
    StylisticTransitions,
    FactItem,
    FactCategory,
    FactStatus,
    SemanticLifecycleState,
    NormalizedMonetaryValue,
    NormalizedDateValue
)

logger = logging.getLogger("pipeline.synthesizer")

# Authoritative named timezone for all quota calculations and publication dates
MYT_TZ = ZoneInfo("Asia/Kuala_Lumpur")


class QuotaCorruptionError(Exception):
    """Raised when the persistent quota state file is corrupt, malformed, or invalid."""
    pass


class QuotaManager:
    """
    Persistent, fail-closed Gemini API quota manager for Sabah Daily News.
    Enforces:
    - Maximum 5 Gemini HTTP requests per Malaysia calendar day (Asia/Kuala_Lumpur).
    - Maximum 1 Gemini HTTP request per pipeline run.
    - Authoritative remote state verification against origin/main.
    - Durable write-ahead reservation pushed to origin/main before each HTTP request.
    - Local offline execution cannot authorize Gemini calls (fail-closed).
    - Conditions B (missing remote), C (fetch failure), and D (corrupt remote) fail closed to Track B.
    - No refunds: any attempted request counts toward the daily budget.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        state_file_override: Optional[str] = None,
        execution_mode_override: Optional[str] = None
    ):
        self.config = config or {}
        quota_cfg = self.config.get("gemini_quota", {})

        # Configured limits bounded by safety invariants
        configured_daily = int(quota_cfg.get("daily_request_limit", 5))
        self.daily_request_limit = min(configured_daily, 5)

        configured_per_run = int(quota_cfg.get("per_run_request_limit", 1))
        self.per_run_request_limit = min(configured_per_run, 1)

        raw_models = quota_cfg.get("candidate_models")
        if raw_models and isinstance(raw_models, list) and len(raw_models) > 0:
            self.candidate_models = [str(raw_models[0])]
        else:
            self.candidate_models = ["gemini-3.5-flash-lite"]

        self.state_file = state_file_override or quota_cfg.get("state_file", "config/gemini_quota_state.json")
        self.fail_closed = quota_cfg.get("fail_closed", True)
        self.allow_first_time_init = quota_cfg.get("allow_first_time_init", False)

        # Execution mode: CI_PRODUCTION, LOCAL_OFFLINE, or MOCK_TEST
        if execution_mode_override:
            self.execution_mode = execution_mode_override
        else:
            configured_mode = quota_cfg.get("execution_mode") or os.getenv("GEMINI_EXECUTION_MODE")
            if configured_mode:
                self.execution_mode = configured_mode
            elif os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true":
                self.execution_mode = "CI_PRODUCTION"
            else:
                self.execution_mode = "LOCAL_OFFLINE"

        # In-memory execution tracker for this pipeline instance
        self.run_requests_count = 0

    def get_today_myt_str(self) -> str:
        """Return current calendar date string (YYYY-MM-DD) in Asia/Kuala_Lumpur."""
        return datetime.now(MYT_TZ).strftime("%Y-%m-%d")

    def _build_fresh_state(self) -> Dict[str, Any]:
        """Generate a valid, fresh quota state dictionary for today."""
        now_myt = datetime.now(MYT_TZ)
        return {
            "schema_version": "1.0",
            "timezone": "Asia/Kuala_Lumpur",
            "date": now_myt.strftime("%Y-%m-%d"),
            "reserved_count": 0,
            "daily_limit": self.daily_request_limit,
            "reservations": [],
            "last_updated": now_myt.isoformat(),
            "status": "IDLE",
            "initialization_mode": "AUTHORIZED_INITIALIZATION"
        }

    def _validate_state_schema(self, state: Any) -> None:
        """Strict validation of quota state schema. Raises QuotaCorruptionError on violation."""
        if not isinstance(state, dict):
            raise QuotaCorruptionError("Quota state root must be a JSON object.")

        if state.get("schema_version") != "1.0":
            raise QuotaCorruptionError(f"Unsupported schema_version: {state.get('schema_version')}")

        state_date = state.get("date")
        if not isinstance(state_date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", state_date):
            raise QuotaCorruptionError(f"Malformed date in quota state: {state_date}")

        reserved_count = state.get("reserved_count")
        if not isinstance(reserved_count, int) or reserved_count < 0 or reserved_count > 5:
            raise QuotaCorruptionError(f"Invalid reserved_count: {reserved_count} (must be int 0..5)")

        daily_limit = state.get("daily_limit")
        if not isinstance(daily_limit, int) or daily_limit > 5:
            raise QuotaCorruptionError(f"Invalid daily_limit: {daily_limit}")

        reservations = state.get("reservations")
        if not isinstance(reservations, list):
            raise QuotaCorruptionError("reservations field must be a list.")

    def _rollover_state(self, state: Dict[str, Any], today_str: str) -> Dict[str, Any]:
        """Perform calendar day rollover in Asia/Kuala_Lumpur."""
        now_iso = datetime.now(MYT_TZ).isoformat()
        state["date"] = today_str
        state["reserved_count"] = 0
        state["reservations"] = []
        state["daily_limit"] = self.daily_request_limit
        state["last_updated"] = now_iso
        state["status"] = "IDLE"
        return state

    def load_and_validate_local_state(self) -> Dict[str, Any]:
        """
        Load and validate the local quota state file.
        Fails closed on any schema violation, negative count, count > 5, or invalid date.
        """
        today_str = self.get_today_myt_str()

        if not os.path.exists(self.state_file):
            fresh = self._build_fresh_state()
            self.save_state_local(fresh)
            return fresh

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            raise QuotaCorruptionError(f"Failed to read or parse quota state JSON: {e}")

        self._validate_state_schema(state)

        # Check for Malaysia calendar day rollover locally
        if state.get("date") != today_str:
            state = self._rollover_state(state, today_str)
            self.save_state_local(state)

        return state

    def fetch_authoritative_remote_state(self) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Fetch and strictly validate authoritative remote state from origin/main.
        Distinguishes:
        - Condition A: First-time initialization, explicitly authorized.
        - Condition B: Existing quota state missing from origin/main -> FAIL CLOSED.
        - Condition C: Remote fetch failure -> FAIL CLOSED.
        - Condition D: Corrupted remote state -> FAIL CLOSED.
        Returns: (state_dict_or_None, condition_code)
        """
        try:
            # 1. Verify current branch is main or active test branch
            active_branch = os.getenv("GITHUB_REF_NAME") or "main"
            res_br = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=False)
            current_branch = res_br.stdout.strip()
            if current_branch and current_branch not in ("main", active_branch):
                logger.error(f"[QUOTA FAIL-CLOSED] Unexpected active branch '{current_branch}', expected 'main' or '{active_branch}'.")
                return None, "UNEXPECTED_BRANCH"

            # 2. Fetch origin metadata
            res_fetch = subprocess.run(["git", "fetch", "origin", active_branch, "--quiet"], capture_output=True, text=True, check=False)
            if res_fetch.returncode != 0:
                logger.error(f"[QUOTA FAIL-CLOSED: Condition C] Remote fetch failure: {res_fetch.stderr.strip()}")
                return None, "CONDITION_C_FETCH_FAILURE"

            # 3. Check if state file exists in active branch or origin/main
            git_path = self.state_file.replace("\\", "/")
            res_show = subprocess.run(["git", "show", f"origin/{active_branch}:{git_path}"], capture_output=True, text=True, check=False)
            if res_show.returncode != 0 and active_branch != "main":
                res_show = subprocess.run(["git", "show", f"origin/main:{git_path}"], capture_output=True, text=True, check=False)

            if res_show.returncode != 0:
                if self.allow_first_time_init:
                    logger.info("[QUOTA Condition A] First-time initialization explicitly authorized.")
                    return self._build_fresh_state(), "CONDITION_A_FIRST_TIME_INIT"
                else:
                    logger.error(f"[QUOTA FAIL-CLOSED: Condition B] State file missing from origin/{active_branch} and origin/main.")
                    return None, "CONDITION_B_MISSING_REMOTE"

            # 4. Parse remote content
            try:
                state = json.loads(res_show.stdout)
            except Exception as e:
                logger.error(f"[QUOTA FAIL-CLOSED: Condition D] Corrupted remote state JSON: {e}")
                return None, "CONDITION_D_CORRUPTED_REMOTE"

            # 5. Validate schema strictly
            try:
                self._validate_state_schema(state)
            except QuotaCorruptionError as e:
                logger.error(f"[QUOTA FAIL-CLOSED: Condition D] Remote state schema invalid: {e}")
                return None, "CONDITION_D_CORRUPTED_REMOTE"

            # 6. Check for Malaysia calendar day rollover on remote state
            today_str = self.get_today_myt_str()
            if state.get("date") != today_str:
                logger.info(f"New Malaysia calendar day detected on remote ({state.get('date')} -> {today_str}). Resetting daily counter.")
                state = self._rollover_state(state, today_str)

            return state, "REMOTE_VALID"

        except Exception as e:
            logger.error(f"[QUOTA FAIL-CLOSED] Unexpected exception during remote state verification: {e}")
            return None, "UNEXPECTED_EXCEPTION"

    def save_state_local(self, state: Dict[str, Any]) -> None:
        """Write state to state_file durably with UTF-8 encoding."""
        os.makedirs(os.path.dirname(os.path.abspath(self.state_file)), exist_ok=True)
        temp_file = f"{self.state_file}.tmp.{uuid.uuid4().hex[:6]}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, self.state_file)

    def persist_remote_reservation(self, state: Dict[str, Any]) -> bool:
        """
        Durably write and push the reservation to origin/main with strict index isolation.
        Pre-conditions:
        1. Pre-staging check: git diff --cached --name-only must be completely empty.
           If any staged files exist, abort immediately without modifying index.
        2. Stage only the exact state file: git add <state_file>.
        3. Post-staging check: git diff --cached --name-only must contain exactly [<state_file>].
           If any other path is staged, abort immediately before commit and push.
        4. Commit and push: commit exactly that one file with [skip ci], push origin main.
        Never uses force push, rebase, reset, stash, or clean.
        """
        try:
            # 1. Pre-staging check: verify Git index is completely clean
            cmd_check_pre = ["git", "diff", "--cached", "--name-only"]
            res_pre = subprocess.run(cmd_check_pre, capture_output=True, text=True, check=False)
            if res_pre.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Failed to inspect Git cached index: {res_pre.stderr}")
                return False

            pre_staged = [line.strip() for line in res_pre.stdout.strip().splitlines() if line.strip()]
            if pre_staged:
                logger.error(
                    f"[GIT ISOLATION ABORT] Pre-staged files detected in Git index: {pre_staged}. "
                    "Refusing to commit to prevent accidental commit of unrelated work. Aborting reservation."
                )
                return False

            # 2. Write state locally
            self.save_state_local(state)

            # 3. Stage ONLY the exact quota state file
            git_path = self.state_file.replace("\\", "/")
            cmd_add = ["git", "add", git_path]
            res_add = subprocess.run(cmd_add, capture_output=True, text=True, check=False)
            if res_add.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Git add failed for {git_path}: {res_add.stderr}")
                return False

            # 4. Post-staging verification: index must contain exactly and only git_path
            cmd_check_post = ["git", "diff", "--cached", "--name-only"]
            res_post = subprocess.run(cmd_check_post, capture_output=True, text=True, check=False)
            if res_post.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Failed to verify post-stage index: {res_post.stderr}")
                return False

            post_staged = [line.strip().replace("\\", "/") for line in res_post.stdout.strip().splitlines() if line.strip()]
            expected_normalized = git_path.lstrip("./")
            normalized_post_staged = [p.lstrip("./") for p in post_staged]

            if normalized_post_staged != [expected_normalized]:
                logger.error(
                    f"[GIT ISOLATION ABORT] Staged index mismatch! Expected strictly {[expected_normalized]}, "
                    f"found {normalized_post_staged}. Aborting before commit/push."
                )
                return False

            # 5. Commit isolated quota reservation
            cmd_commit = ["git", "commit", "-m", "ci: write-ahead gemini quota reservation [skip ci]"]
            res_commit = subprocess.run(cmd_commit, capture_output=True, text=True, check=False)
            if res_commit.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Git commit failed: {res_commit.stderr}")
                return False

            # 6. Push to origin with strict branch isolation (never push to main from test branch)
            active_branch = os.getenv("GITHUB_REF_NAME") or "main"
            cmd_push = ["git", "push", "origin", f"HEAD:{active_branch}"]
            res_push = subprocess.run(cmd_push, capture_output=True, text=True, check=False)
            if res_push.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Git push failed or was rejected: {res_push.stderr}")
                return False

            return True
        except Exception as e:
            logger.error(f"[GIT ISOLATION ABORT] Exception during remote reservation persistence: {e}")
            return False

    def reserve_slot(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Write-Ahead Reservation: Reserves a single quota slot BEFORE any HTTP request begins.
        - Enforces execution mode: LOCAL_OFFLINE cannot authorize Gemini (fail closed to Track B).
        - In CI_PRODUCTION: fetches authoritative remote state, verifies origin/main, reserves slot,
          and pushes ONLY the exact quota state file to origin/main before authorization.
        - In MOCK_TEST: performs reservation through mocked remote persistence.
        - Returns reservation record on success; returns None on any failure.
        """
        # 1. Enforce maximum 1 request per pipeline execution run
        if self.run_requests_count >= self.per_run_request_limit:
            logger.warning(f"[QUOTA GATE] Per-run request limit ({self.per_run_request_limit}) reached.")
            return None

        # 2. Check execution mode
        if self.execution_mode == "LOCAL_OFFLINE":
            logger.warning(
                "[QUOTA FAIL-CLOSED] Local offline execution does not possess remote write-ahead authority. "
                "Gemini calls prohibited. Routing to Track B."
            )
            return None

        # 3. Obtain authoritative state
        if self.execution_mode in ("CI_PRODUCTION", "MOCK_TEST"):
            state, condition = self.fetch_authoritative_remote_state()
            if not state:
                logger.error(f"[QUOTA FAIL-CLOSED] Authoritative remote state check failed ({condition}). Aborting Track A.")
                return None
        else:
            logger.error(f"[QUOTA FAIL-CLOSED] Unrecognized execution mode: '{self.execution_mode}'. Aborting Track A.")
            return None

        # 4. Enforce daily limit (maximum 5 requests per Malaysia day)
        if state["reserved_count"] >= self.daily_request_limit:
            logger.warning(
                f"[QUOTA GATE] Daily quota limit ({self.daily_request_limit}) exhausted for date {state['date']} "
                f"(current reserved: {state['reserved_count']})."
            )
            return None

        # 5. Construct reservation record
        now_myt = datetime.now(MYT_TZ)
        res_id = f"res_{state['date']}_{state['reserved_count'] + 1}_{uuid.uuid4().hex[:8]}"
        state["reserved_count"] += 1
        res_record = {
            "reservation_id": res_id,
            "timestamp": now_myt.isoformat(),
            "model": model,
            "status": "RESERVED"
        }
        state["reservations"].append(res_record)
        state["last_updated"] = now_myt.isoformat()
        state["status"] = "RESERVED"

        # 6. Save local state
        self.save_state_local(state)

        # 7. Write-Ahead Remote Persistence
        if not self.persist_remote_reservation(state):
            logger.error("[QUOTA FAIL-CLOSED] Remote write-ahead reservation failed or rejected. Aborting Track A.")
            res_record["status"] = "FAILED_REMOTE_PERSISTENCE"
            self.save_state_local(state)
            return None

        self.run_requests_count += 1
        logger.info(
            f"[QUOTA RESERVED & PERSISTED] Slot {state['reserved_count']}/{self.daily_request_limit} "
            f"durably registered: {res_id} ({model})"
        )
        return res_record

    def finalize_slot(self, res_id: str, status: str) -> None:
        """
        Update the reservation record status (e.g. COMPLETED, FAILED_HTTP_429, FAILED_TIMEOUT).
        Quota count is NEVER decremented (no refunds for attempted requests).
        """
        try:
            state = self.load_and_validate_local_state()
            found = False
            for r in state.get("reservations", []):
                if r.get("reservation_id") == res_id:
                    r["status"] = status
                    found = True
                    break
            state["last_updated"] = datetime.now(MYT_TZ).isoformat()
            state["status"] = status if found else state.get("status", "IDLE")
            self.save_state_local(state)
        except Exception as e:
            logger.error(f"Failed to finalize quota slot {res_id}: {e}")


class NewsSynthesizer:
    def __init__(self, config: Optional[Dict[str, Any]] = None, quota_mgr: Optional[QuotaManager] = None):
        self.config = config or {}
        self.quota_mgr = quota_mgr or QuotaManager(self.config)
        self.validator = BilingualFactValidator()
        self.min_headlines_threshold = self.config.get("system", {}).get("min_headlines_threshold", 10)

    def validate_article_parity(
        self,
        article: Dict[str, Any],
        canonical_facts: Optional[Dict[str, FactItem]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate cross-lingual factual parity for a synthesized headline dictionary.
        Converts the dictionary into a StructuredArticle and executes the full
        BilingualFactValidator.validate_structured_article() contract.
        Enforces identical fact gate across Track A and Track B.
        """
        category = article.get("category", "sabah")
        title_zh = article.get("title", "")
        title_bm = article.get("titleBM", "")
        detail_zh = article.get("detail", "")
        detail_bm = article.get("detailBM", "")
        source = article.get("source", "")
        url = article.get("url", "")

        facts = canonical_facts or {}
        fids = [fid for fid, f in facts.items() if f.status == FactStatus.VERIFIED]

        structured = StructuredArticle(
            article_id=article.get("id", f"art_{category}"),
            category=category,
            headline=HeadlineRecord(zh_text=title_zh, bm_text=title_bm, fact_ids=fids),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=fids,
                    semantic_state=SemanticLifecycleState.INFORMATIONAL,
                    zh_text=detail_zh,
                    bm_text=detail_bm
                )
            ],
            narrative_claims=[],
            transitions=StylisticTransitions(),
            source_url=url,
            publisher=source
        )

        res = self.validator.validate_structured_article(structured, facts)
        return res.is_valid, res.errors

    def _clean_markdown_json(self, raw_text: str) -> Optional[List[Dict[str, Any]]]:
        try:
            # Strip markdown code blocks
            text = re.sub(r'^```(?:json)?\s*', '', raw_text.strip(), flags=re.MULTILINE)
            text = re.sub(r'```$', '', text.strip(), flags=re.MULTILINE)
            # Find the outer JSON array
            m = re.search(r'\[.*\]', text, re.DOTALL)
            if m:
                items = json.loads(m.group(0))
                if isinstance(items, list):
                    return items
        except Exception as e:
            logger.warning(f"Error parsing Gemini JSON: {e}")
        return None

    def synthesize_track_a_gemini(
        self,
        api_key: str,
        today_iso: str,
        articles: List[RawArticle]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Track A: LLM synthesis using Gemini API with Grounding.
        Enforces:
        - Exactly ONE candidate model: gemini-3.5-flash-lite (configurable).
        - Exactly ONE HTTP request attempt per run.
        - Write-ahead remote reservation durably recorded before the request is sent.
        - Immediate fallback to Track B on any error (HTTP 429, 401, 403, 404, network, timeout).
        - No retries. No Pro model fallback.
        """
        if not api_key:
            return None

        # Determine single candidate model
        candidate_models = self.quota_mgr.candidate_models
        model = candidate_models[0] if candidate_models else "gemini-3.5-flash-lite"

        # 1. Write-Ahead Reservation BEFORE HTTP execution
        reservation = self.quota_mgr.reserve_slot(model)
        if not reservation:
            logger.warning("[TRACK A ABORTED] Quota reservation denied, exhausted, or unpersisted. Routing to Track B.")
            return None

        res_id = reservation["reservation_id"]

        snippets = []
        for i, a in enumerate(articles[:30]):
            sources_str = ", ".join(a.extra.get("corroborating_sources", [a.source]))
            snippets.append(f"{i+1}. [{a.category.upper()}] {a.title} ({sources_str}) - {a.snippet[:120]}")

        context_block = "\n".join(snippets)

        prompt = f"""
你是《西门看看网》首席采编记者。今天是马来西亚时间 {today_iso}。
基于以下真实采集的最新新闻线索（涵盖过去 24-36 小时沙巴州、山打根与全马真实大事件）：
{context_block}

请精选并编译为 15~24 条深度报道，必须严格遵守以下规则：
1. 真实性铁律：必须取材自上述提供的真实线索，保留所有具体款项金额、数字、机构名称及官方回应；
2. 双语深度对等：
   - detail: 中文深度段落，包含背景脉络与具体事实，250~350字；
   - detailBM: 马来文等量多段落深度报道，120~200 perkataan，严禁敷衍概括！
3. 分类配额：sabah (5-8条), national (5-8条), sports (3-5条), general (2-4条)；
4. 格式必须为合法 JSON 数组：
[
  {{
    "category": "sabah",
    "title": "中文主标题 [官方来源1 + 官方来源2 双核实]",
    "titleBM": "Tajuk Berita Bahasa Melayu",
    "detail": "中文深度正文...",
    "detailBM": "Teks berita mendalam Bahasa Melayu...",
    "sources": ["官方来源1", "官方来源2"],
    "url": "https://...",
    "image_url": null
  }}
]
请直接输出 JSON 数组，严禁任何额外说明。
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        # 2. Execute EXACTLY ONE HTTP request with no multi-model cascade or retry
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                items = self._clean_markdown_json(text)
                if items and len(items) >= self.min_headlines_threshold:
                    for itm in items:
                        itm["image_url"] = None
                    self.quota_mgr.finalize_slot(res_id, "COMPLETED")
                    logger.info(f"Successfully generated {len(items)} articles via Gemini ({model})")
                    return items
                else:
                    self.quota_mgr.finalize_slot(res_id, "FAILED_INSUFFICIENT_ITEMS")
                    logger.warning(f"Gemini output had fewer than {self.min_headlines_threshold} articles. Immediate abort.")
                    return None
        except urllib.error.HTTPError as e:
            self.quota_mgr.finalize_slot(res_id, f"FAILED_HTTP_{e.code}")
            logger.warning(f"Gemini HTTP {e.code} error: {e}. Immediate abort of Track A (no retry).")
            return None
        except urllib.error.URLError as e:
            self.quota_mgr.finalize_slot(res_id, "FAILED_TIMEOUT_OR_NETWORK")
            logger.warning(f"Gemini network or timeout error: {e}. Immediate abort of Track A (no retry).")
            return None
        except Exception as e:
            self.quota_mgr.finalize_slot(res_id, "FAILED_UNEXPECTED")
            logger.warning(f"Gemini unexpected error: {e}. Immediate abort of Track A (no retry).")
            return None

    def record_token_usage(
        self,
        token_record: Dict[str, Any],
        log_path: Optional[str] = None
    ) -> None:
        """Durably record Gemini API token usage metadata to JSONL log."""
        target_path = log_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "reports",
            "token_usage_observation.jsonl"
        )
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            with open(target_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(token_record, ensure_ascii=False) + "\n")
            logger.info(f"[TOKEN MONITOR] Appended token usage to: {target_path}")
        except Exception as e:
            logger.warning(f"[TOKEN MONITOR] Failed to write token usage log: {e}")

    def synthesize_track_a_single_batch(
        self,
        api_key: str,
        today_iso: str,
        batch_stories: List[RawArticle],
        usage_log_path: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Phase D-11 Core Architecture: Single-Batch Gemini Request for Daily Top-10 Edition.
        Enforces:
        - Exactly ONE Gemini HTTP request for the entire batch (up to 10 stories).
        - Model: gemini-3.5-flash-lite only.
        - Write-ahead remote quota reservation (1 slot).
        - Max output tokens: 8192 (comfortable headroom for 10 stories).
        - Post-response validation: finishReason == 'STOP', no truncation, D-7 fact verifier.
        - Captures usageMetadata to reports/token_usage_observation.jsonl.
        - Fail-closed: Zero retries, zero model cascade, zero fake-news fallback.
        """
        if not api_key:
            logger.warning("[TRACK A ABORTED] No API key provided.")
            return None

        if not batch_stories:
            logger.warning("[TRACK A ABORTED] Empty batch stories list.")
            return None

        candidate_models = self.quota_mgr.candidate_models
        model = candidate_models[0] if candidate_models else "gemini-3.5-flash-lite"

        # 1. Write-Ahead Quota Reservation BEFORE HTTP execution
        reservation = self.quota_mgr.reserve_slot(model)
        if not reservation:
            logger.warning("[TRACK A ABORTED] Quota reservation denied or failed. Aborting Track A.")
            return None

        res_id = reservation["reservation_id"]

        # 2. Format Consolidated Batch Context
        story_blocks = []
        for i, art in enumerate(batch_stories[:10], 1):
            sources_str = ", ".join(art.extra.get("corroborating_sources", [art.source]))
            body_text = (art.body or art.snippet or art.title).strip()
            # Truncate each source body to 3000 chars to avoid exceeding input context
            if len(body_text) > 3000:
                body_text = body_text[:3000] + "..."
            story_blocks.append(
                f"=== 故事 {i} [{art.category.upper()}] ===\n"
                f"原标题: {art.title}\n"
                f"信源: {sources_str} ({art.url})\n"
                f"发布时间: {art.published_at.isoformat() if art.published_at else '当日'}\n"
                f"真实正文素材:\n{body_text}\n"
            )

        context_block = "\n".join(story_blocks)

        prompt = f"""你是《西门看看网》首席双语采编主任。今天是马来西亚时间 {today_iso}。
以下是今日经过严格地理与事实核实遴选的沙巴与全马重大新闻素材（共 {len(batch_stories[:10])} 篇一手完整正文素材）：

{context_block}

【任务要求】
请在单次响应中，为上述 {len(batch_stories[:10])} 篇新闻分别撰写完整的双语深度报道（中文与马来文严格事实对等）。
严禁分批输出！严禁捏造未经原文提及的人名、款项、日期或机构！

规则：
1. 真实性铁律：必须取材自上述提供的真实正文，保留所有具体款项金额、数字、机构名称及官方回应；
2. 双语深度对等：
   - detail: 中文深度段落，包含背景脉络与具体事实，250~350字；
   - detailBM: 马来文等量深度报道，120~180 perkataan（标准 Bahasa Melayu，严禁以 'Laporan Berita:' 粗糙拼凑！）；
3. 标题对等：title 为中文主标题，titleBM 为精准马来文主标题；
4. 输出格式必须为合法 JSON 数组：
[
  {{
    "story_index": 1,
    "category": "sabah",
    "title": "中文主标题",
    "titleBM": "Tajuk Berita Bahasa Melayu",
    "detail": "中文深度正文...",
    "detailBM": "Teks berita mendalam Bahasa Melayu...",
    "source_url": "https://...",
    "publisher": "..."
  }}
]
直接输出 JSON 数组，严禁在开头或结尾添加任何其他文本说明。
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json"
            }
        }

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        http_code = None
        res_json = None
        finish_reason = "UNKNOWN"

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                http_code = resp.getcode()
                raw_body = resp.read().decode("utf-8")
                res_json = json.loads(raw_body)
        except urllib.error.HTTPError as e:
            http_code = e.code
            self.quota_mgr.finalize_slot(res_id, f"FAILED_HTTP_{e.code}")
            logger.warning(f"[TRACK A FAILED] Gemini HTTP {e.code} error: {e}. Immediate abort.")
            return None
        except urllib.error.URLError as e:
            self.quota_mgr.finalize_slot(res_id, "FAILED_TIMEOUT_OR_NETWORK")
            logger.warning(f"[TRACK A FAILED] Gemini network error: {e}. Immediate abort.")
            return None
        except Exception as e:
            self.quota_mgr.finalize_slot(res_id, "FAILED_UNEXPECTED")
            logger.warning(f"[TRACK A FAILED] Unexpected error: {e}. Immediate abort.")
            return None

        # 3. Post-Response Inspection & Token Logging
        usage_meta = res_json.get("usageMetadata", {}) if res_json else {}
        candidates = res_json.get("candidates", []) if res_json else []

        if candidates:
            finish_reason = candidates[0].get("finishReason", "UNKNOWN")

        # Extract generated items
        items = []
        if candidates and finish_reason == "STOP":
            try:
                part_text = candidates[0]["content"]["parts"][0]["text"]
                items = self._clean_markdown_json(part_text) or []
            except Exception as e:
                logger.warning(f"[TRACK A PARSE ERROR] Failed to parse Gemini response JSON: {e}")

        # Check truncation fail-closed
        if finish_reason == "MAX_TOKENS":
            self.quota_mgr.finalize_slot(res_id, "FAILED_TRUNCATED")
            logger.error("[TRACK A TRUNCATED] Finish reason was MAX_TOKENS. Truncated output discarded.")
            return None

        # 4. Bind Authoritative Application Metadata & Validate with D-7
        accepted_articles: List[Dict[str, Any]] = []
        rejected_articles: List[Dict[str, Any]] = []

        now_iso = datetime.now(MYT_TZ).isoformat()

        for idx, item in enumerate(items):
            # Match with original RawArticle
            s_idx = item.get("story_index", idx + 1) - 1
            orig_art = batch_stories[s_idx] if (0 <= s_idx < len(batch_stories)) else (batch_stories[idx] if idx < len(batch_stories) else None)

            if orig_art:
                item["source"] = orig_art.source
                item["sources"] = orig_art.extra.get("corroborating_sources", [orig_art.source])
                item["url"] = orig_art.url
                item["source_urls"] = orig_art.extra.get("corroborating_urls", [orig_art.url])
                item["original_published_at"] = orig_art.published_at.isoformat() if orig_art.published_at else None
                item["geo_scope"] = orig_art.extra.get("geo_scope", orig_art.category)
            else:
                item["source"] = item.get("publisher", "官方信源")
                item["sources"] = [item["source"]]
                item["url"] = item.get("source_url", "")
                item["source_urls"] = [item["url"]] if item["url"] else []
                item["original_published_at"] = None
                item["geo_scope"] = item.get("category", "sabah")

            item["id"] = f"art_{item.get('category', 'sabah')}_{len(accepted_articles)+1:02d}"
            item["image_url"] = None
            item["collected_at"] = now_iso
            item["site_published_at"] = now_iso
            item["updated_at"] = now_iso
            item["is_updated"] = False

            # D-7 Full Fact Validation Gate
            is_valid, errs = self.validate_article_parity(item)
            if is_valid:
                item["validation_status"] = "VERIFIED"
                accepted_articles.append(item)
            else:
                logger.warning(f"[FACT GATE REJECTED] {item.get('title')}: {errs}")
                rejected_articles.append({"article": item, "errors": errs})

        # 5. Record Token Observation
        token_entry = {
            "timestamp_myt": datetime.now(MYT_TZ).isoformat(),
            "model": model,
            "reservation_id": res_id,
            "http_status": http_code,
            "finish_reason": finish_reason,
            "prompt_token_count": usage_meta.get("promptTokenCount", "UNAVAILABLE"),
            "candidates_token_count": usage_meta.get("candidatesTokenCount", "UNAVAILABLE"),
            "total_token_count": usage_meta.get("totalTokenCount", "UNAVAILABLE"),
            "thoughts_token_count": usage_meta.get("thoughtsTokenCount", "UNAVAILABLE"),
            "stories_input_count": len(batch_stories[:10]),
            "stories_generated_count": len(items),
            "stories_accepted_count": len(accepted_articles),
            "stories_rejected_count": len(rejected_articles)
        }
        self.record_token_usage(token_entry, usage_log_path)

        # 6. Finalize Quota Slot
        if len(accepted_articles) >= self.min_headlines_threshold:
            self.quota_mgr.finalize_slot(res_id, "COMPLETED")
            logger.info(f"[TRACK A SUCCESS] Generated and verified {len(accepted_articles)} articles.")
            return accepted_articles
        else:
            self.quota_mgr.finalize_slot(res_id, "FAILED_INSUFFICIENT_ITEMS")
            logger.warning(
                f"[TRACK A INSUFFICIENT] Accepted {len(accepted_articles)} articles, "
                f"below threshold ({self.min_headlines_threshold}). Failing closed."
            )
            return None

    def synthesize_track_b_standalone(
        self,
        today_iso: str,
        articles: List[RawArticle]
    ) -> List[Dict[str, Any]]:
        """
        Track B (Preserved Data Structuring):
        Exposes clean, authentic confirmed headlines and existing snippets/bodies.
        DOES NOT SYNTHESIZE FAKE NEWS BOILERPLATE.
        """
        now_myt = datetime.now(MYT_TZ)
        now_iso = now_myt.isoformat()
        synthesized: List[Dict[str, Any]] = []

        for idx, art in enumerate(articles[:10], 1):
            c_title = art.title.strip()
            sources = art.extra.get("corroborating_sources", [art.source])
            cat = art.category or "sabah"

            # Clean substantive body or lead paragraph
            clean_body = (art.body or art.snippet or c_title).strip()

            synthesized.append({
                "id": f"art_{cat}_{idx:02d}",
                "category": cat,
                "title": c_title,
                "titleBM": art.extra.get("titleBM", ""),
                "detail": clean_body,
                "detailBM": art.extra.get("detailBM", ""),
                "source": art.source,
                "sources": sources,
                "url": art.url,
                "source_urls": art.extra.get("corroborating_urls", [art.url]),
                "image_url": None,
                "original_published_at": art.published_at.isoformat() if art.published_at else None,
                "collected_at": art.extra.get("collected_at", now_iso),
                "site_published_at": now_iso,
                "updated_at": now_iso,
                "is_updated": False,
                "geo_scope": art.extra.get("geo_scope", "sabah")
            })

        return synthesized

    def synthesize(
        self,
        today_iso: str,
        articles: List[RawArticle],
        api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Single-Batch Dispatch Entry Point.
        If Track A succeeds, returns verified batch.
        If Track A fails or has no key, FAILS CLOSED: Zero fallback to fake-news boilerplate.
        """
        logger.info(f"Synthesizer input: {len(articles)} canonical articles")

        if api_key:
            logger.info("Executing Track A: Single-Batch Gemini Request...")
            gemini_results = self.synthesize_track_a_single_batch(
                api_key=api_key,
                today_iso=today_iso,
                batch_stories=articles
            )
            if gemini_results and len(gemini_results) >= self.min_headlines_threshold:
                return gemini_results

        # Production policy: Do not generate fake-news template boilerplate
        logger.warning(
            "[SYNTHESIZER FAIL-CLOSED] Gemini API synthesis unavailable or failed. "
            "Policy strictly prohibits fake news template fallback. Returning 0 articles."
        )
        return []

        # Production policy: Do not generate fake-news template boilerplate
        logger.warning(
            "[SYNTHESIZER FAIL-CLOSED] Gemini API synthesis unavailable or failed. "
            "Policy strictly prohibits fake news template fallback. Returning 0 articles."
        )
        return []
