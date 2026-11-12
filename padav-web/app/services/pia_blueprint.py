"""PIA v1.0 blueprint: the locked constants from the master specification, in one place.

Changing any of these is a formal revision of the specification (section "Document control"),
so they are deliberately *not* configuration.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

BLUEPRINT_VERSION = "1.0"
CONSENT_VERSION = "pia-consent-1.0"
SCORING_MODEL_VERSION = "raw-v1"
MIN_AGE = 13
ADULT_AGE = 18
LANGUAGES = ("en", "hi")
DIFFICULTIES = ("easy", "medium", "hard", "expert")
ITEM_STATUSES = ("draft", "reviewed", "pilot", "operational")
FORM_STATUSES = ("draft", "pilot", "operational")


@dataclass(frozen=True)
class Subtest:
    domain: str  # stable code stored in the database
    label: str
    construct: str
    questions: int
    minutes: int

    @property
    def seconds(self) -> int:
        return self.minutes * 60


SUBTESTS: tuple[Subtest, ...] = (
    Subtest("gf", "Fluid reasoning (Gf)", "Novel problem-solving and pattern reasoning", 10, 8),
    Subtest("gc", "Verbal comprehension (Gc)", "Understanding and reasoning with language", 7, 6),
    Subtest("gv", "Visual-spatial processing (Gv)", "Mental visualization and spatial relationships", 8, 7),
    Subtest("gwm", "Working memory (Gwm)", "Holding and manipulating information", 7, 6),
    Subtest("gs", "Processing speed (Gs)", "Rapid and accurate visual processing", 7, 5),
    Subtest("gq", "Quantitative reasoning (Gf/Gq)", "Numerical relationships and quantitative logic", 7, 6),
    Subtest("glr", "Long-term retrieval (Glr)", "Learning and retrieving previously presented information", 4, 8),
)
DOMAINS = tuple(s.domain for s in SUBTESTS)
SUBTEST_BY_DOMAIN = {s.domain: s for s in SUBTESTS}
TOTAL_QUESTIONS = 50
TOTAL_MINUTES = 46
DIFFICULTY_TARGET = {"easy": 12, "medium": 18, "hard": 13, "expert": 7}
POOL_TARGET = {"gf": 45, "gc": 40, "gv": 40, "gwm": 35, "gs": 35, "gq": 30, "glr": 15}  # 240 research items

# Events a client may report; everything else is written by the server only.
CLIENT_EVENTS = ("encoding_start", "encoding_end", "retrieval_start", "interruption", "resume")

assert sum(s.questions for s in SUBTESTS) == TOTAL_QUESTIONS
assert sum(s.minutes for s in SUBTESTS) == TOTAL_MINUTES
assert sum(DIFFICULTY_TARGET.values()) == TOTAL_QUESTIONS
assert sum(POOL_TARGET.values()) == 240


def validate_form_shape(entries: Iterable[tuple[str, str]]) -> list[str]:
    """``entries`` = (domain, difficulty) for every item of a form. Returns human-readable problems."""
    entries = list(entries)
    problems: list[str] = []
    if len(entries) != TOTAL_QUESTIONS:
        problems.append(f"a form needs exactly {TOTAL_QUESTIONS} scored items, got {len(entries)}")
    per_domain = Counter(domain for domain, _ in entries)
    for unknown in sorted(set(per_domain) - set(DOMAINS)):
        problems.append(f"unknown domain '{unknown}'")
    for subtest in SUBTESTS:
        if per_domain.get(subtest.domain, 0) != subtest.questions:
            problems.append(f"{subtest.domain}: needs {subtest.questions} items, got {per_domain.get(subtest.domain, 0)}")
    per_difficulty = Counter(difficulty for _, difficulty in entries)
    for level, target in DIFFICULTY_TARGET.items():
        if per_difficulty.get(level, 0) != target:
            problems.append(f"difficulty '{level}': needs {target} items, got {per_difficulty.get(level, 0)}")
    return problems


def blueprint_summary() -> dict:
    return {
        "version": BLUEPRINT_VERSION,
        "total_questions": TOTAL_QUESTIONS,
        "total_minutes": TOTAL_MINUTES,
        "min_age": MIN_AGE,
        "languages": list(LANGUAGES),
        "subtests": [
            {"domain": s.domain, "label": s.label, "construct": s.construct, "questions": s.questions, "minutes": s.minutes}
            for s in SUBTESTS
        ],
    }
