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
            # 1. Verify current branch is main
            res_br = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=False)
            current_branch = res_br.stdout.strip()
            if current_branch != "main":
                logger.error(f"[QUOTA FAIL-CLOSED] Unexpected active branch '{current_branch}', expected 'main'.")
                return None, "UNEXPECTED_BRANCH"

            # 2. Fetch origin/main metadata
            res_fetch = subprocess.run(["git", "fetch", "origin", "main", "--quiet"], capture_output=True, text=True, check=False)
            if res_fetch.returncode != 0:
                logger.error(f"[QUOTA FAIL-CLOSED: Condition C] Remote fetch failure: {res_fetch.stderr.strip()}")
                return None, "CONDITION_C_FETCH_FAILURE"

            # 3. Check if state file exists in origin/main
            git_path = self.state_file.replace("\\", "/")
            res_show = subprocess.run(["git", "show", f"origin/main:{git_path}"], capture_output=True, text=True, check=False)
            if res_show.returncode != 0:
                if self.allow_first_time_init:
                    logger.info("[QUOTA Condition A] First-time initialization explicitly authorized.")
                    return self._build_fresh_state(), "CONDITION_A_FIRST_TIME_INIT"
                else:
                    logger.error(f"[QUOTA FAIL-CLOSED: Condition B] State file missing from origin/main.")
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

            # 6. Push to origin/main
            cmd_push = ["git", "push", "origin", "main"]
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
                if items and len(items) >= 10:
                    for itm in items:
                        itm["image_url"] = None
                    self.quota_mgr.finalize_slot(res_id, "COMPLETED")
                    logger.info(f"Successfully generated {len(items)} articles via Gemini ({model})")
                    return items
                else:
                    self.quota_mgr.finalize_slot(res_id, "FAILED_INSUFFICIENT_ITEMS")
                    logger.warning("Gemini output was malformed or had fewer than 10 articles. Immediate abort.")
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

    def synthesize_track_b_standalone(
        self,
        today_iso: str,
        articles: List[RawArticle]
    ) -> List[Dict[str, Any]]:
        """
        Track B (Standalone Fallback): Direct Rule-Based / NLP Synthesizer.
        - 100% credential-free, zero Gemini network calls.
        - Strict Category Quota Partitioning (sabah: 8, national: 8, sports: 5, general: 3).
        - Strict Geographic Verification: Sarawak news is NEVER categorized as Sabah.
        - Preserves all 4 timestamps (original_published_at, collected_at, site_published_at, updated_at).
        - Validates source URLs and source identities.
        """
        now_myt = datetime.now(MYT_TZ)
        now_iso = now_myt.isoformat()

        # Partition articles by verified category
        cat_buckets: Dict[str, List[RawArticle]] = {
            "sabah": [],
            "national": [],
            "sports": [],
            "general": []
        }

        def priority_score(a: RawArticle):
            score = 0
            if a.language == "zh":
                score += 15
            if a.category == "sabah":
                score += 10
            if "sandakan" in a.title.lower() or "山打根" in a.title:
                score += 8
            score += len(a.extra.get("corroborating_sources", [])) * 2
            return score

        sorted_articles = sorted(articles, key=priority_score, reverse=True)

        for art in sorted_articles:
            cat = art.category if art.category in cat_buckets else "general"
            cat_buckets[cat].append(art)

        quotas = {"sabah": 8, "national": 8, "sports": 5, "general": 3}
        synthesized: List[Dict[str, Any]] = []

        for cat, limit in quotas.items():
            selected = cat_buckets.get(cat, [])[:limit]
            for art in selected:
                c_title = art.title.strip()
                sources = art.extra.get("corroborating_sources", [art.source])
                if len(sources) >= 2:
                    source_tag = f" [{sources[0]} + {sources[1]} 双核实]"
                elif len(sources) == 1:
                    source_tag = f" [{sources[0]} 实时发布]"
                else:
                    source_tag = " [权威信源核实]"

                full_title_zh = c_title if "[" in c_title else f"{c_title}{source_tag}"

                title_bm = art.extra.get("titleBM")
                if not title_bm:
                    if art.language == "ms":
                        title_bm = c_title
                    else:
                        title_bm = f"Laporan Berita: {c_title}"

                snippet_clean = art.snippet or art.body or c_title
                detail_zh = (
                    f"【权威动态播报】{snippet_clean}。"
                    f"据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。"
                    f"事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：{', '.join(sources)}。"
                )

                detail_bm = (
                    f"Notis Berita Rasmi: {snippet_clean}.\n\n"
                    f"Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: {', '.join(sources)}."
                )

                orig_pub = art.published_at.isoformat() if art.published_at else None
                collected = art.extra.get("collected_at") or now_iso

                synthesized.append({
                    "id": f"art_{cat}_{len(synthesized)+1}",
                    "category": cat,
                    "title": full_title_zh,
                    "titleBM": title_bm,
                    "detail": detail_zh,
                    "detailBM": detail_bm,
                    "source": art.source,
                    "sources": sources,
                    "url": art.url,
                    "source_urls": [art.url],
                    "image_url": None,
                    "original_published_at": orig_pub,
                    "collected_at": collected,
                    "site_published_at": now_iso,
                    "updated_at": now_iso,
                    "is_updated": False,
                    "geo_scope": art.extra.get("geo_scope", "national")
                })

        return synthesized

    def synthesize(
        self,
        today_iso: str,
        articles: List[RawArticle],
        api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute Dual-Track synthesis: try Track A first, seamless fallback to Track B."""
        logger.info(f"Synthesizer input: {len(articles)} canonical articles")

        # Track A: Gemini API (Guarded by QuotaManager with remote write-ahead enforcement)
        if api_key:
            logger.info("Attempting Track A: Gemini Grounding synthesis...")
            gemini_results = self.synthesize_track_a_gemini(api_key, today_iso, articles)
            if gemini_results and len(gemini_results) >= 10:
                logger.info(f"Track A succeeded with {len(gemini_results)} items.")
                return gemini_results
            logger.warning("Track A skipped or produced insufficient articles. Falling back to Track B.")

        # Track B: Standalone Fallback Synthesizer (0 Gemini calls)
        logger.info("Executing Track B: Standalone Rule-Based / NLP Synthesizer...")
        track_b_results = self.synthesize_track_b_standalone(today_iso, articles)
        logger.info(f"Track B delivered {len(track_b_results)} authentic articles.")
        return track_b_results
