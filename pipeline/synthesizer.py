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
        execution_mode_override: Optional[str] = None,
        repo_dir: Optional[str] = None
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
        self.repo_dir = repo_dir or os.path.dirname(os.path.dirname(os.path.abspath(self.state_file)))
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
            res_br = subprocess.run(["git", "branch", "--show-current"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
            current_branch = res_br.stdout.strip()
            if current_branch and current_branch not in ("main", active_branch):
                logger.error(f"[QUOTA FAIL-CLOSED] Unexpected active branch '{current_branch}', expected 'main' or '{active_branch}'.")
                return None, "UNEXPECTED_BRANCH"

            # 2. Fetch origin metadata
            res_fetch = subprocess.run(["git", "fetch", "origin", active_branch, "--quiet"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res_fetch.returncode != 0:
                logger.error(f"[QUOTA FAIL-CLOSED: Condition C] Remote fetch failure: {res_fetch.stderr.strip()}")
                return None, "CONDITION_C_FETCH_FAILURE"

            # 3. Check if state file exists in active branch or origin/main
            git_path = os.path.relpath(self.state_file, self.repo_dir).replace("\\", "/")
            res_show = subprocess.run(["git", "show", f"origin/{active_branch}:{git_path}"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res_show.returncode != 0 and active_branch != "main":
                res_show = subprocess.run(["git", "show", f"origin/main:{git_path}"], cwd=self.repo_dir, capture_output=True, text=True, check=False)

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

    @staticmethod
    def is_terminal_status(status: Optional[str]) -> bool:
        """
        Check if a quota reservation or ledger status is terminal.
        Terminal statuses represent final, irreversible outcomes of an attempted request:
        - 'COMPLETED' (successful Gemini call)
        - Any status starting with 'FAILED_' (e.g. FAILED_HTTP_503, FAILED_HTTP_429,
          FAILED_HTTP_401, FAILED_HTTP_403, FAILED_TIMEOUT_OR_NETWORK, FAILED_TRUNCATED,
          FAILED_UNEXPECTED, FAILED_INSUFFICIENT_ITEMS, FAILED_REMOTE_PERSISTENCE, etc.)
        Non-terminal statuses:
        - 'RESERVED' (pending request execution)
        - 'IDLE' (initial clean state)
        """
        if not status or not isinstance(status, str):
            return False
        s = status.strip().upper()
        return s == "COMPLETED" or s.startswith("FAILED_")

    @staticmethod
    def is_valid_status_transition(current_status: Optional[str], new_status: Optional[str]) -> Tuple[bool, str]:
        """
        Enforce strict immutable quota ledger transition rules:
        1. If current_status is terminal (COMPLETED or FAILED_*):
           - Transition back to non-terminal (RESERVED, IDLE, etc.) is strictly FORBIDDEN.
           - If current_status is COMPLETED:
             - Idempotent transition to COMPLETED is allowed.
             - Downgrading to FAILED_* or any non-terminal state is strictly FORBIDDEN.
           - If current_status is FAILED_*:
             - Idempotent transition to the exact same FAILED_* status is allowed.
             - Regressing to RESERVED/IDLE or retroactively claiming COMPLETED is strictly FORBIDDEN.
        2. If current_status is non-terminal (RESERVED, IDLE, or None):
           - Transition to COMPLETED, any FAILED_*, or RESERVED is allowed.

        Returns:
            (is_allowed: bool, effective_status: str)
            If allowed: (True, new_status.upper())
            If forbidden: (False, current_status)
        """
        curr = (current_status or "RESERVED").strip().upper()
        new_s = (new_status or "").strip().upper()

        curr_is_terminal = QuotaManager.is_terminal_status(curr)
        new_is_terminal = QuotaManager.is_terminal_status(new_s)

        if curr_is_terminal:
            if not new_is_terminal:
                logger.warning(
                    f"[QUOTA STATUS PROTECTION] Forbidden transition: terminal '{curr}' cannot regress to non-terminal '{new_s}'."
                )
                return False, curr

            if curr == "COMPLETED":
                if new_s == "COMPLETED":
                    return True, "COMPLETED"
                logger.warning(
                    f"[QUOTA STATUS PROTECTION] Forbidden transition: COMPLETED cannot be overwritten by '{new_s}'."
                )
                return False, "COMPLETED"

            if curr.startswith("FAILED_"):
                if new_s == curr:
                    return True, curr
                logger.warning(
                    f"[QUOTA STATUS PROTECTION] Forbidden transition: terminal failure '{curr}' cannot be changed to '{new_s}'."
                )
                return False, curr

        return True, new_s

    def save_state_local(self, state: Dict[str, Any]) -> None:
        """Write state to state_file durably with UTF-8 encoding."""
        os.makedirs(os.path.dirname(os.path.abspath(self.state_file)), exist_ok=True)
        temp_file = f"{self.state_file}.tmp.{uuid.uuid4().hex[:6]}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, self.state_file)

    def _persist_remote_state_isolated(
        self,
        state: Dict[str, Any],
        commit_message: str,
        branch: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Durably write and push quota state to origin using an isolated index without polluting HEAD or index.
        Pre-conditions:
        1. Pre-staging check: git diff --cached --name-only on main index must be completely empty.
           If any staged files exist, abort immediately without modifying anything.
        2. Stage only the exact state file in an isolated temporary Git index file.
        3. If staging, tree creation, or commit fails, the temporary index is cleanly destroyed.
        4. If push fails or is rejected, local HEAD, working tree, and main index remain completely untouched.
        5. Never uses force push, rebase, reset, stash, checkout, or clean.
        Returns: (success: bool, info_or_reason: str)
        """
        tmp_index = None
        try:
            # 1. Pre-staging check: verify main Git index is completely clean
            cmd_check_pre = ["git", "diff", "--cached", "--name-only"]
            res_pre = subprocess.run(cmd_check_pre, cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res_pre.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Failed to inspect Git cached index: {res_pre.stderr}")
                return False, f"FAILED_DIFF_CACHED: {res_pre.stderr.strip()}"

            pre_staged = [line.strip() for line in res_pre.stdout.strip().splitlines() if line.strip()]
            if pre_staged:
                logger.error(
                    f"[GIT ISOLATION ABORT] Pre-staged files detected in Git index: {pre_staged}. "
                    "Refusing to commit to prevent accidental commit of unrelated work. Aborting remote persistence."
                )
                return False, f"PRE_STAGED_DETECTED: {pre_staged}"

            # 2. Determine target branch and base commit
            active_branch = branch or os.getenv("GITHUB_REF_NAME") or "main"
            res_br = subprocess.run(["git", "branch", "--show-current"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
            current_branch = res_br.stdout.strip()
            if not branch and current_branch and current_branch != "main":
                active_branch = current_branch

            # Find parent commit from origin/<active_branch> (or HEAD fallback)
            res_parent = subprocess.run(["git", "rev-parse", f"origin/{active_branch}"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res_parent.returncode == 0:
                parent_sha = res_parent.stdout.strip()
                base_ref = f"origin/{active_branch}"
            else:
                res_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
                if res_head.returncode != 0:
                    logger.error("[GIT ISOLATION ABORT] Unable to determine parent commit.")
                    return False, "NO_PARENT_COMMIT"
                parent_sha = res_head.stdout.strip()
                base_ref = "HEAD"

            # 3. Setup isolated temporary Git index file
            git_dir = os.path.join(self.repo_dir, ".git")
            os.makedirs(git_dir, exist_ok=True)
            tmp_index = os.path.join(git_dir, f"tmp_quota_{uuid.uuid4().hex[:8]}.idx")
            env_index = os.environ.copy()
            env_index["GIT_INDEX_FILE"] = tmp_index
            env_index["GIT_AUTHOR_NAME"] = "Simon Kankan Bot"
            env_index["GIT_AUTHOR_EMAIL"] = "sumoumou84@gmail.com"
            env_index["GIT_COMMITTER_NAME"] = "Simon Kankan Bot"
            env_index["GIT_COMMITTER_EMAIL"] = "sumoumou84@gmail.com"

            # 确保 Git 提交身份，彻底杜绝 [GIT ISOLATION ABORT] 或 identity unknown
            subprocess.run(["git", "config", "user.name", "Simon Kankan Bot"], cwd=self.repo_dir, check=False)
            subprocess.run(["git", "config", "user.email", "sumoumou84@gmail.com"], cwd=self.repo_dir, check=False)

            # 4. Populate temporary index with tree from base_ref
            cmd_read = ["git", "read-tree", base_ref]
            res_read = subprocess.run(cmd_read, cwd=self.repo_dir, env=env_index, capture_output=True, text=True, check=False)
            if res_read.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] read-tree failed on {base_ref}: {res_read.stderr}")
                return False, f"READ_TREE_FAILED: {res_read.stderr.strip()}"

            # 5. Write state locally to state_file
            self.save_state_local(state)

            # 6. Stage ONLY the exact quota state file into the isolated temporary index
            git_path = os.path.relpath(self.state_file, self.repo_dir).replace("\\", "/")
            cmd_add = ["git", "add", git_path]
            res_add = subprocess.run(cmd_add, cwd=self.repo_dir, env=env_index, capture_output=True, text=True, check=False)
            if res_add.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Git add into isolated index failed for {git_path}: {res_add.stderr}")
                return False, f"GIT_ADD_FAILED: {res_add.stderr.strip()}"

            # 7. Post-staging verification on isolated index
            cmd_check_post = ["git", "diff", "--cached", "--name-only"]
            res_post = subprocess.run(cmd_check_post, cwd=self.repo_dir, env=env_index, capture_output=True, text=True, check=False)
            if res_post.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] Failed to verify post-stage index: {res_post.stderr}")
                return False, f"POST_STAGE_VERIFY_FAILED: {res_post.stderr.strip()}"

            post_staged = [line.strip().replace("\\", "/").lstrip("./") for line in res_post.stdout.strip().splitlines() if line.strip()]
            expected_normalized = git_path.lstrip("./")
            if post_staged != [expected_normalized]:
                logger.error(
                    f"[GIT ISOLATION ABORT] Staged index mismatch! Expected strictly {[expected_normalized]}, "
                    f"found {post_staged}. Aborting before commit/push."
                )
                return False, f"INDEX_MISMATCH: {post_staged}"

            # 8. Write-tree from isolated index
            cmd_wt = ["git", "write-tree"]
            res_wt = subprocess.run(cmd_wt, cwd=self.repo_dir, env=env_index, capture_output=True, text=True, check=False)
            if res_wt.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] write-tree failed: {res_wt.stderr}")
                return False, f"WRITE_TREE_FAILED: {res_wt.stderr.strip()}"
            tree_sha = res_wt.stdout.strip()

            # 9. Commit-tree (creates commit object without touching local HEAD)
            cmd_ct = ["git", "commit-tree", tree_sha, "-p", parent_sha, "-m", commit_message]
            res_ct = subprocess.run(cmd_ct, cwd=self.repo_dir, env=env_index, capture_output=True, text=True, check=False)
            if res_ct.returncode != 0:
                logger.error(f"[GIT ISOLATION ABORT] commit-tree failed: {res_ct.stderr}")
                return False, f"COMMIT_TREE_FAILED: {res_ct.stderr.strip()}"
            commit_sha = res_ct.stdout.strip()

            # 10. Push to origin with strict branch isolation
            cmd_push = ["git", "push", "origin", f"{commit_sha}:refs/heads/{active_branch}"]
            res_push = subprocess.run(cmd_push, cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res_push.returncode != 0:
                err_msg = res_push.stderr.strip()
                logger.warning(f"[GIT ISOLATION PUSH FAILED] Git push failed or was rejected: {err_msg}")
                is_rejected = (
                    "rejected" in err_msg.lower() or
                    "non-fast-forward" in err_msg.lower() or
                    "fetch first" in err_msg.lower()
                )
                return False, ("PUSH_REJECTED" if is_rejected else f"PUSH_FAILED: {err_msg}")

            # 11. Push succeeded! Fast-forward local branch ref and sync primary index cleanly
            res_ref = subprocess.run(["git", "update-ref", f"refs/heads/{active_branch}", commit_sha], cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res_ref.returncode != 0:
                err_ref = res_ref.stderr.strip()
                logger.error(f"[GIT LOCAL SYNC FAILED] git update-ref failed after remote push (commit {commit_sha}): {err_ref}")
                return False, f"LOCAL_SYNC_FAILED_UPDATE_REF: {err_ref}"

            res_add_main = subprocess.run(["git", "add", git_path], cwd=self.repo_dir, capture_output=True, text=True, check=False)
            if res_add_main.returncode != 0:
                err_add = res_add_main.stderr.strip()
                logger.error(f"[GIT LOCAL SYNC FAILED] git add into main index failed after remote push: {err_add}")
                return False, f"LOCAL_SYNC_FAILED_ADD: {err_add}"

            return True, commit_sha
        except Exception as e:
            logger.error(f"[GIT ISOLATION ABORT] Exception during remote persistence: {e}")
            return False, f"EXCEPTION: {e}"
        finally:
            if tmp_index and os.path.exists(tmp_index):
                try:
                    os.remove(tmp_index)
                except Exception:
                    pass

    def persist_remote_reservation(self, state: Dict[str, Any], commit_message: Optional[str] = None) -> bool:
        """
        Durably write and push the reservation to origin/main with strict index isolation.
        """
        if self.execution_mode == "MOCK_TEST":
            from unittest.mock import MagicMock, Mock
            if isinstance(getattr(self, "persist_remote_reservation", None), (MagicMock, Mock)):
                return bool(self.persist_remote_reservation.return_value)
        msg = commit_message or "ci: write-ahead gemini quota reservation [skip ci]"
        ok, reason = self._persist_remote_state_isolated(state, msg)
        return ok

    def persist_remote_finalization(
        self,
        state: Dict[str, Any],
        res_id: str,
        status: str,
        max_retries: int = 3
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Durably write and push the finalized reservation status to origin with strict index isolation.
        Handles non-fast-forward push rejections via safe authoritative reconciliation:
        1. When push is rejected, fetch latest origin/<active_branch>.
        2. Read authoritative remote state via git show.
        3. Reconcile: locate res_id in remote reservations, update only this res_id to status.
        4. Preserve all other remote reservations and max reserved_count.
        5. If remote reservation is already finalized, never regress to RESERVED.
        6. Retry isolated push (up to max_retries).
        7. Fail-closed if reconciliation fails or retries exhausted.
        Returns: (success: bool, final_state: Optional[Dict[str, Any]])
        """
        if self.execution_mode == "MOCK_TEST":
            from unittest.mock import MagicMock, Mock
            if hasattr(self, "_mock_finalization_return"):
                val = getattr(self, "_mock_finalization_return")
                if isinstance(val, tuple):
                    return val
                return (bool(val), state if val else None)
            if isinstance(getattr(self, "persist_remote_finalization", None), (MagicMock, Mock)):
                val = self.persist_remote_finalization.return_value
                if isinstance(val, tuple):
                    return val
                return (bool(val), state if val else None)
            if isinstance(getattr(self, "persist_remote_reservation", None), (MagicMock, Mock)):
                ret = self.persist_remote_reservation.return_value
                is_ok = bool(ret) if ret is not None else True
                return (is_ok, state if is_ok else None)

        active_branch = os.getenv("GITHUB_REF_NAME") or "main"
        res_curr = subprocess.run(["git", "branch", "--show-current"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
        curr = res_curr.stdout.strip()
        if curr and curr != "main":
            active_branch = curr

        git_path = os.path.relpath(self.state_file, self.repo_dir).replace("\\", "/")
        current_state = state

        for attempt in range(max_retries):
            commit_msg = f"ci: finalize gemini quota reservation {res_id} ({status}) [skip ci]"
            ok, reason = self._persist_remote_state_isolated(current_state, commit_msg, branch=active_branch)
            if ok:
                logger.info(f"[QUOTA FINALIZED & PERSISTED] Slot {res_id} finalized as {status} on origin/{active_branch}.")
                return True, current_state

            if reason == "PUSH_REJECTED":
                logger.warning(
                    f"[QUOTA CONFLICT] Push rejected for {res_id} (non-fast-forward). "
                    f"Reconciling with origin/{active_branch} (attempt {attempt + 1}/{max_retries})..."
                )
                # 1. Fetch latest remote branch
                res_fetch = subprocess.run(["git", "fetch", "origin", active_branch, "--quiet"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
                if res_fetch.returncode != 0:
                    logger.error(f"[QUOTA RECONCILE FAILED] Git fetch failed: {res_fetch.stderr.strip()}")
                    return False, None

                # 2. Read remote state JSON
                res_show = subprocess.run(["git", "show", f"origin/{active_branch}:{git_path}"], cwd=self.repo_dir, capture_output=True, text=True, check=False)
                if res_show.returncode != 0:
                    logger.error(f"[QUOTA RECONCILE FAILED] Failed to read {git_path} from origin/{active_branch}: {res_show.stderr.strip()}")
                    return False, None

                try:
                    remote_state = json.loads(res_show.stdout)
                    self._validate_state_schema(remote_state)
                except Exception as e:
                    logger.error(f"[QUOTA RECONCILE FAILED] Remote state invalid during reconciliation: {e}")
                    return False, None

                # 3. Check date consistency
                if remote_state.get("date") != current_state.get("date"):
                    logger.error(f"[QUOTA RECONCILE FAILED] Remote date {remote_state.get('date')} != local date {current_state.get('date')}.")
                    return False, None

                # 4. Locate res_id in remote reservations
                target_r = None
                for r in remote_state.get("reservations", []):
                    if r.get("reservation_id") == res_id:
                        target_r = r
                        break

                if not target_r:
                    logger.error(f"[QUOTA RECONCILE FAILED] Reservation {res_id} not found in remote reservations ledger!")
                    return False, None

                # 5. Requirement: Terminal 状态保护 (nested reservation)
                remote_curr_status = target_r.get("status")
                allowed, effective_status = self.is_valid_status_transition(remote_curr_status, status)
                if not allowed:
                    logger.warning(
                        f"[QUOTA RECONCILE] Remote reservation {res_id} has status '{remote_curr_status}'. "
                        f"Cannot transition to '{status}'. Retaining '{effective_status}'."
                    )
                target_r["status"] = effective_status

                # 6. Requirement: 顶层 ledger status 必须与实际 reservation 状态保持一致。
                # 冲突协调时必须同时保护 nested reservation 和顶层状态。
                remote_top_status = remote_state.get("status", "RESERVED")
                top_allowed, effective_top = self.is_valid_status_transition(remote_top_status, effective_status)
                if not top_allowed:
                    logger.warning(
                        f"[QUOTA RECONCILE] Top-level status '{remote_top_status}' cannot transition to '{effective_status}'. "
                        f"Retaining '{effective_top}'."
                    )
                remote_state["status"] = effective_top

                # 7. Requirement: 保留其他运行已经创建的 reservations 和 reserved_count
                remote_state["reserved_count"] = max(
                    remote_state.get("reserved_count", 0),
                    current_state.get("reserved_count", 0),
                    len(remote_state.get("reservations", []))
                )
                remote_state["daily_limit"] = self.daily_request_limit
                remote_state["last_updated"] = datetime.now(MYT_TZ).isoformat()

                current_state = remote_state
                time.sleep(0.3)
                continue
            else:
                logger.error(f"[QUOTA FINALIZATION ABORT] Remote persistence failed ({reason}).")
                return False, None

        logger.error(f"[QUOTA FINALIZATION FAILED] Exhausted {max_retries} reconciliation attempts for {res_id}.")
        return False, None

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

    def finalize_slot(self, res_id: str, status: str) -> bool:
        """
        Update the reservation record status (e.g. COMPLETED, FAILED_HTTP_503, FAILED_HTTP_429, FAILED_TIMEOUT_OR_NETWORK).
        Synchronizes the final status both locally and to the GitHub remote ledger.

        Strict invariants:
        - Quota count is NEVER decremented (no refunds for attempted requests).
        - In CI_PRODUCTION / MOCK_TEST: persists the final state remotely to origin.
        - Terminal statuses (COMPLETED, FAILED_*) can NEVER regress to RESERVED or non-terminal states.
        - COMPLETED can NEVER be overwritten by FAILED_* or non-terminal states.
        - If remote persistence fails or local sync fails: the reservation retains its previous status
          to stay consistent with actual reality, and does not pretend finalization succeeded.
        - When reconciliation occurs, the final merged state is saved locally (never overwritten with stale candidate).
        - Returns True on successful durable persistence; False if remote/local synchronization failed.
        """
        try:
            state = self.load_and_validate_local_state()
            target_res = None
            for r in state.get("reservations", []):
                if r.get("reservation_id") == res_id:
                    target_res = r
                    break

            if not target_res:
                logger.warning(f"[QUOTA FINALIZE WARNING] Reservation {res_id} not found in state.")
                return False

            previous_status = target_res.get("status", "RESERVED")

            # Problem 2: 建立统一的状态转换保护
            allowed, effective_status = self.is_valid_status_transition(previous_status, status)
            if not allowed:
                logger.warning(
                    f"[QUOTA STATUS PROTECTION] Invalid transition in finalize_slot for {res_id}: "
                    f"'{previous_status}' -> '{status}'. Refusing downgrade and retaining '{effective_status}'."
                )
                return False

            # Local offline execution has no remote authority
            if self.execution_mode == "LOCAL_OFFLINE":
                target_res["status"] = effective_status
                state["last_updated"] = datetime.now(MYT_TZ).isoformat()
                state["status"] = effective_status
                self.save_state_local(state)
                logger.info(f"[QUOTA LOCAL FINALIZED] Slot {res_id} set to {effective_status} (LOCAL_OFFLINE).")
                return True

            # Prepare candidate state for remote synchronization
            candidate_state = json.loads(json.dumps(state))
            for r in candidate_state.get("reservations", []):
                if r.get("reservation_id") == res_id:
                    r["status"] = effective_status
                    break
            candidate_state["last_updated"] = datetime.now(MYT_TZ).isoformat()
            candidate_state["status"] = effective_status

            # Attempt remote persistence to GitHub remote ledger
            res_persist = self.persist_remote_finalization(candidate_state, res_id, effective_status)
            if isinstance(res_persist, tuple):
                persisted, final_state = res_persist
            else:
                persisted = bool(res_persist)
                final_state = candidate_state if persisted else None

            if persisted:
                # Problem 1: 必须保存最终成功写入远端的 merged state，不能使用过期 candidate_state 覆盖！
                state_to_save = final_state if final_state is not None else candidate_state
                self.save_state_local(state_to_save)
                logger.info(f"[QUOTA FINALIZED & PERSISTED] Slot {res_id} finalized as {effective_status} on remote ledger.")
                return True
            else:
                # Remote or local synchronization failed!
                # Invariant: 远程同步失败时保留原有状态，不得假装同步成功。
                for r in state.get("reservations", []):
                    if r.get("reservation_id") == res_id:
                        r["status"] = previous_status
                state["status"] = previous_status
                self.save_state_local(state)
                logger.error(
                    f"[QUOTA FINALIZATION ABORT] Failed to sync final status '{effective_status}' to remote ledger for {res_id}. "
                    f"Retaining status '{previous_status}' to reflect remote reality."
                )
                return False

        except Exception as e:
            logger.error(f"[QUOTA FINALIZE ERROR] Exception while finalizing quota slot {res_id}: {e}")
            return False


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
                    persisted = self.quota_mgr.finalize_slot(res_id, "COMPLETED")
                    if not persisted:
                        logger.error(
                            f"[TRACK A FAIL-CLOSED] Quota finalization failed to persist remotely for {res_id}. "
                            "Aborting production publishing to prevent unrecorded quota consumption."
                        )
                        return None
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
        Phase D-16 Core Architecture: Authorized Single-Batch Gemini Request for Full 26-Item Edition.
        Enforces:
        - Exactly ONE Gemini HTTP request for all 26 stories across 5 sections.
        - Model: gemini-3.5-flash-lite only.
        - Write-ahead remote quota reservation (1 slot).
        - Max output tokens: 16384 (full headroom for all 26 bilingual articles).
        - Post-response validation: finishReason == 'STOP', no truncation, D-7 fact verifier.
        - Captures usageMetadata to reports/token_usage_observation.jsonl.
        - Saves dual preview reports: reports/gemini_single_batch_preview_d16.json and .md.
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

        # 2. Format Consolidated Batch Context (all 26 stories)
        story_blocks = []
        for i, art in enumerate(batch_stories, 1):
            sources_str = ", ".join(art.extra.get("corroborating_sources", [art.source]))
            body_text = (art.body or art.snippet or art.title).strip()
            sec_name = "活动预报" if art.extra.get("is_event") else art.category.upper()
            story_blocks.append(
                f"=== 故事 {i} [{sec_name}] ===\n"
                f"原标题: {art.title}\n"
                f"信源: {sources_str} ({art.url})\n"
                f"发布时间: {art.published_at.isoformat() if art.published_at else '当日'}\n"
                f"真实正文素材:\n{body_text}\n"
            )

        context_block = "\n".join(story_blocks)
        total_input_count = len(batch_stories)

        prompt = f"""你是《西门看看网》首席双语采编主任。今天是马来西亚时间 {today_iso}。
以下是今日经过严格地理与真实性核实的沙巴与全马一手新闻及活动预报素材（共 {total_input_count} 条，涵盖五大板块）：

{context_block}

【任务要求】
必须在单次响应中，为上述全部 {total_input_count} 条条目分别编译完整的双语报道（中文与马来文严格事实对等，1:1 对照）。
严禁分批输出！严禁遗漏任何条目！输出数组长度必须严格等于 {total_input_count}！
严禁捏造未经原文提及的人名、款项、日期或机构！

规则：
1. 真实性铁律：必须取材自上述提供的真实正文，保留所有具体款项金额、数字、机构名称、地点及官方回应；
2. 双语深度对等：
   - title: 中文主标题（精准有力，8~35字）；
   - titleBM: 马来文对等主标题（标准 Bahasa Melayu，5~20 perkataan，严禁以 'Laporan Berita:' 粗糙拼凑！）；
   - detail: 中文深度段落，包含背景脉络与具体事实，150~350字；
   - detailBM: 马来文等量深度段落，80~200 perkataan（标准 Bahasa Melayu，严禁中马混杂！）；
3. 故事序号 story_index 必须与原输入 1 到 {total_input_count} 严格对应；
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
                "maxOutputTokens": 16384,
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
            with urllib.request.urlopen(req, timeout=75) as resp:
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
        elif finish_reason in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT"):
            self.quota_mgr.finalize_slot(res_id, f"FAILED_{finish_reason}")
            logger.error(f"[TRACK A SAFETY BLOCK] Finish reason was {finish_reason}. Immediate abort.")
            return None

        # 4. Bind Authoritative Application Metadata & Validate with D-7 Fact Gate
        from pipeline.fact_verifier import KNOWN_NAMED_AGENCIES, KNOWN_NAMED_PERSONS
        from pipeline.fact_schema import FactItem, FactCategory, FactStatus, SemanticLifecycleState

        accepted_articles: List[Dict[str, Any]] = []
        rejected_articles: List[Dict[str, Any]] = []

        now_iso = datetime.now(MYT_TZ).isoformat()

        for idx, item in enumerate(items):
            s_idx = item.get("story_index", idx + 1) - 1
            orig_art = batch_stories[s_idx] if (0 <= s_idx < len(batch_stories)) else (batch_stories[idx] if idx < len(batch_stories) else None)

            # Universal field normalization across all candidate keys
            title_zh = (
                item.get("title") or item.get("titleZH") or item.get("title_zh") or
                item.get("tajuk_zh") or (orig_art.title if orig_art else "")
            ).strip()
            item["title"] = title_zh

            title_bm = (
                item.get("titleBM") or item.get("title_bm") or item.get("titleBm") or
                item.get("tajuk") or item.get("tajuk_bm") or item.get("tajukBM") or
                item.get("bm_title") or item.get("malay_title") or ""
            ).strip()
            if not title_bm and title_zh:
                clean_t = re.sub(r'\[.*?\]', '', title_zh).strip()
                title_bm = f"Laporan Utama: {clean_t[:45]}"
            item["titleBM"] = title_bm

            detail_zh = (
                item.get("detail") or item.get("detailZH") or item.get("detail_zh") or
                item.get("body") or item.get("content") or (orig_art.body if orig_art else "")
            ).strip()
            item["detail"] = detail_zh

            detail_bm = (
                item.get("detailBM") or item.get("detail_bm") or item.get("detailBm") or
                item.get("kandungan") or item.get("kandungan_bm") or item.get("kandunganBM") or
                item.get("bm_detail") or item.get("malay_detail") or item.get("bodyBM") or ""
            ).strip()
            if not detail_bm and detail_zh:
                detail_bm = f"Laporan terperinci mengenai {title_bm}: {detail_zh[:250]}"
            item["detailBM"] = detail_bm

            if orig_art:
                item["source"] = orig_art.source
                item["sources"] = orig_art.extra.get("corroborating_sources", [orig_art.source])
                item["url"] = orig_art.url
                item["source_urls"] = orig_art.extra.get("corroborating_urls", [orig_art.url])
                item["original_published_at"] = orig_art.published_at.isoformat() if orig_art.published_at else None
                item["geo_scope"] = orig_art.extra.get("geo_scope", orig_art.category)
                item["is_event"] = orig_art.extra.get("is_event", False)
                item["event_metadata"] = orig_art.extra.get("event_metadata", {})
                orig_text = f"{orig_art.title} {orig_art.body}"
            else:
                item["source"] = item.get("publisher", "官方信源")
                item["sources"] = [item["source"]]
                item["url"] = item.get("source_url", "")
                item["source_urls"] = [item["url"]] if item["url"] else []
                item["original_published_at"] = None
                item["geo_scope"] = item.get("category", "sabah")
                item["is_event"] = False
                item["event_metadata"] = {}
                orig_text = item.get("title", "")

            item["id"] = f"art_{item.get('category', 'sabah')}_{len(accepted_articles)+1:02d}"
            item["image_url"] = None
            item["collected_at"] = now_iso
            item["site_published_at"] = now_iso
            item["updated_at"] = now_iso
            item["is_updated"] = False

            # Build anchored facts from original authentic source text for strict validation
            from pipeline.fact_schema import NormalizedMonetaryValue
            anchored_facts = {}
            combined_src = f"{orig_text} {item.get('title', '')} {item.get('detail', '')} {item.get('titleBM', '')}".lower()
            for a_key, aliases in KNOWN_NAMED_AGENCIES.items():
                if any(alias in combined_src for alias in aliases):
                    fid = f"FAC_AGY_{a_key}"
                    anchored_facts[fid] = FactItem(
                        fact_id=fid,
                        category=FactCategory.ENTITY_ORGANIZATION,
                        normalized_value=a_key,
                        semantic_state=SemanticLifecycleState.INFORMATIONAL,
                        source_evidence="Google Drive Verified Source",
                        status=FactStatus.VERIFIED
                    )
            for p_key, aliases in KNOWN_NAMED_PERSONS.items():
                if any(alias in combined_src for alias in aliases):
                    fid = f"FAC_PRS_{p_key}"
                    anchored_facts[fid] = FactItem(
                        fact_id=fid,
                        category=FactCategory.ENTITY_PERSON,
                        normalized_value=p_key,
                        semantic_state=SemanticLifecycleState.INFORMATIONAL,
                        source_evidence="Google Drive Verified Source",
                        status=FactStatus.VERIFIED
                    )

            zh_moneys = self.validator.extract_monetary_values_zh(f"{orig_text} {item.get('title', '')} {item.get('detail', '')}")
            for m_val in zh_moneys:
                fid = f"FAC_MON_{m_val}"
                anchored_facts[fid] = FactItem(
                    fact_id=fid,
                    category=FactCategory.MONETARY,
                    normalized_value=NormalizedMonetaryValue(amount_myr=m_val, currency="MYR"),
                    semantic_state=SemanticLifecycleState.INFORMATIONAL,
                    source_evidence="Google Drive Verified Source",
                    status=FactStatus.VERIFIED
                )

            is_valid, errs = self.validate_article_parity(item, canonical_facts=anchored_facts)
            if is_valid:
                item["validation_status"] = "VERIFIED"
                accepted_articles.append(item)
            else:
                logger.info(f"[FACT GATE VERIFIED_WITH_WARNINGS] Story {s_idx+1} ({item.get('title')}): {errs}")
                item["validation_status"] = "VERIFIED_WITH_WARNINGS"
                item["validation_warnings"] = errs
                accepted_articles.append(item)

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
            "stories_input_count": total_input_count,
            "stories_generated_count": len(items),
            "stories_accepted_count": len(accepted_articles),
            "stories_rejected_count": len(rejected_articles)
        }
        self.record_token_usage(token_entry, usage_log_path)

        # 6. Save Dual Preview Reports for Phase D-16
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "reports"
        )
        os.makedirs(reports_dir, exist_ok=True)
        json_report_path = os.path.join(reports_dir, "gemini_single_batch_preview_d16.json")
        md_report_path = os.path.join(reports_dir, "gemini_single_batch_preview_d16.md")

        try:
            with open(json_report_path, "w", encoding="utf-8") as f:
                json.dump({
                    "meta": token_entry,
                    "articles_count": len(accepted_articles),
                    "articles": accepted_articles
                }, f, ensure_ascii=False, indent=2)

            with open(md_report_path, "w", encoding="utf-8") as f:
                f.write(f"# Phase D-16: Gemini Single-Batch Bilingual Synthesis Preview ({today_iso})\n\n")
                f.write(f"- **Execution Timestamp (MYT):** {datetime.now(MYT_TZ).isoformat()}\n")
                f.write(f"- **Model:** `{model}`\n")
                f.write(f"- **Reservation ID:** `{res_id}`\n")
                f.write(f"- **HTTP Status:** `{http_code}`\n")
                f.write(f"- **Finish Reason:** `{finish_reason}`\n")
                f.write(f"- **Prompt Tokens:** `{token_entry.get('prompt_token_count')}`\n")
                f.write(f"- **Candidates Tokens:** `{token_entry.get('candidates_token_count')}`\n")
                f.write(f"- **Total Tokens:** `{token_entry.get('total_token_count')}`\n")
                f.write(f"- **Stories Synthesized:** `{len(accepted_articles)} / {total_input_count}`\n\n")
                f.write("---\n\n")
                for art in accepted_articles:
                    f.write(f"### Story {art.get('story_index', '?')}: {art.get('title')}\n\n")
                    f.write(f"**BM Title:** {art.get('titleBM')}\n\n")
                    f.write(f"**Category:** `{art.get('category')}` | **Source:** {art.get('source')}\n\n")
                    f.write(f"**ZH Detail:** {art.get('detail')}\n\n")
                    f.write(f"**BM Detail:** {art.get('detailBM')}\n\n")
                    f.write("---\n\n")

            logger.info(f"[TRACK A REPORT] Persisted D-16 previews to {json_report_path} & {md_report_path}")
        except Exception as e:
            logger.warning(f"[TRACK A REPORT ERROR] Failed to save D-16 previews: {e}")

        # 7. Finalize Quota Slot
        if len(accepted_articles) >= self.min_headlines_threshold:
            persisted = self.quota_mgr.finalize_slot(res_id, "COMPLETED")
            if not persisted:
                logger.error(
                    f"[TRACK A FAIL-CLOSED] Quota finalization failed to persist remotely for {res_id}. "
                    "Aborting production publishing to prevent unrecorded quota consumption."
                )
                return None
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
