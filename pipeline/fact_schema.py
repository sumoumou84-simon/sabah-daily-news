#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline/fact_schema.py — Canonical Fact Schema & Data Contracts
Phase D-5: Universal Fact-Locking Specification
- Strongly-typed fact categories and non-linear evidence states.
- Canonical fact items and temporal precision classes.
- Structured claim contracts for headlines, core claims, and narrative claims.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union


class FactCategory(str, Enum):
    MONETARY = "MONETARY"
    TEMPORAL_DATE = "TEMPORAL_DATE"
    TEMPORAL_YEAR = "TEMPORAL_YEAR"
    TEMPORAL_RANGE = "TEMPORAL_RANGE"
    HEADCOUNT = "HEADCOUNT"
    EDITION = "EDITION"
    QUANTITY_ENTITY = "QUANTITY_ENTITY"
    DURATION = "DURATION"
    ENTITY_PERSON = "ENTITY_PERSON"
    ENTITY_ORGANIZATION = "ENTITY_ORGANIZATION"
    LOCATION = "LOCATION"


class FactStatus(str, Enum):
    EXTRACTED = "EXTRACTED"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTED = "CONFLICTED"


class SemanticLifecycleState(str, Enum):
    # Financial Track
    APPROVED_ALLOCATION = "APPROVED_ALLOCATION"
    FUNDS_DISBURSED = "FUNDS_DISBURSED"
    FUNDS_SPENT = "FUNDS_SPENT"
    # Physical Project Track
    PROJECT_PLANNED = "PROJECT_PLANNED"
    PROJECT_ONGOING = "PROJECT_ONGOING"
    PROJECT_COMPLETED = "PROJECT_COMPLETED"
    # Policy / Governance Track
    POLICY_PROPOSED = "POLICY_PROPOSED"
    POLICY_APPROVED = "POLICY_APPROVED"
    POLICY_ENFORCED = "POLICY_ENFORCED"
    # Event Track
    EVENT_SCHEDULED = "EVENT_SCHEDULED"
    EVENT_ONGOING = "EVENT_ONGOING"
    CEREMONY_CONCLUDED = "CEREMONY_CONCLUDED"
    # General / Informational
    INFORMATIONAL = "INFORMATIONAL"


class TemporalPrecision(str, Enum):
    YEAR_ONLY = "YEAR_ONLY"
    MONTH_ONLY = "MONTH_ONLY"
    EXACT_DATE = "EXACT_DATE"
    DATE_RANGE = "DATE_RANGE"


@dataclass
class NormalizedMonetaryValue:
    amount_myr: int
    currency: str = "MYR"


@dataclass
class NormalizedDateValue:
    year: int
    month: int
    day: int
    weekday: int  # 0 = Monday, ..., 6 = Sunday


@dataclass
class NormalizedDateRangeValue:
    start_year: int
    start_month: int
    start_day: int
    start_weekday: int
    end_year: int
    end_month: int
    end_day: int
    end_weekday: int


@dataclass
class NormalizedQuantityValue:
    count: int
    unit: str


@dataclass
class NormalizedHeadcountValue:
    count: int
    is_approximate: bool = False


@dataclass
class NormalizedEditionValue:
    edition: int


@dataclass
class NormalizedDurationValue:
    value: int
    unit: str  # e.g. "hours", "days"


@dataclass
class SourceEvidence:
    exact_quote: str
    source_url: str
    publisher: str
    retrieved_at: str
    paragraph_index: int = 1


@dataclass
class FactItem:
    fact_id: str
    category: FactCategory
    normalized_value: Any
    semantic_state: SemanticLifecycleState
    source_evidence: SourceEvidence
    status: FactStatus = FactStatus.EXTRACTED
    required_language_coverage: List[str] = field(default_factory=lambda: ["zh", "bm"])
    expected_representations: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class CanonicalFactRecord:
    article_id: str
    facts: Dict[str, FactItem]
    publication_timestamp: str
    geographic_scope: str = "sabah"


@dataclass
class ClaimRecord:
    claim_id: str
    fact_ids: List[str]
    semantic_state: SemanticLifecycleState
    zh_text: str
    bm_text: str


@dataclass
class HeadlineRecord:
    zh_text: str
    bm_text: str
    fact_ids: List[str] = field(default_factory=list)


@dataclass
class NarrativeClaimRecord:
    claim_id: str
    fact_ids: List[str]
    semantic_state: SemanticLifecycleState
    zh_text: str
    bm_text: str


@dataclass
class StylisticTransitions:
    zh_connector: str = ""
    bm_connector: str = ""


@dataclass
class StructuredArticle:
    article_id: str
    category: str
    headline: HeadlineRecord
    core_claims: List[ClaimRecord]
    narrative_claims: List[NarrativeClaimRecord] = field(default_factory=list)
    transitions: StylisticTransitions = field(default_factory=StylisticTransitions)
    source_url: str = ""
    publisher: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    status: str  # "VERIFIED", "REVIEW_REQUIRED", "REJECTED"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    audited_claims_count: int = 0
