"""Fail-closed unsupported-claim guard for governance text artifacts."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from alpha_system.governance.validation import GovernanceValidationError, ValidationIssue

STANDARD_NO_CLAIMS_LANGUAGE = (
    "This report is not evidence of alpha validity, profitability, tradability, "
    "robustness, production readiness, paper readiness, live readiness, broker "
    "readiness, or readiness for real data."
)

PERMITTED_NON_ASSERTING_LANGUAGE: tuple[str, ...] = (
    "explicit no-claims or no-assertion statements",
    "blocked-language policy, taxonomy, or vocabulary catalogs",
    "guard or detector statements that reject blocked claim vocabulary",
    "governance object identifiers such as AlphaSpec and alpha_spec_id",
)


@dataclass(frozen=True, slots=True)
class ProhibitedClaimPattern:
    """One prohibited-claim regular expression inside a taxonomy category."""

    pattern_id: str
    expression: str


@dataclass(frozen=True, slots=True)
class ProhibitedClaimRule:
    """A prohibited unsupported-claim category."""

    category: str
    description: str
    patterns: tuple[ProhibitedClaimPattern, ...]


@dataclass(frozen=True, slots=True)
class PermittedClaimContext:
    """A documented non-asserting context that may mention blocked vocabulary."""

    name: str
    description: str
    expression: str


@dataclass(frozen=True, slots=True)
class UnsupportedClaimViolation:
    """Structured rejected unsupported-claim match."""

    category: str
    pattern_id: str
    matched_text: str
    line: int
    column: int
    snippet: str

    def to_dict(self) -> dict[str, str | int]:
        """Return a stable representation for handoffs and validators."""

        return asdict(self)


class UnsupportedClaimError(GovernanceValidationError):
    """Raised when governance text is malformed or contains unsupported claims."""

    def __init__(
        self,
        *,
        context: str,
        violations: tuple[UnsupportedClaimViolation, ...] = (),
        input_issues: tuple[ValidationIssue, ...] = (),
    ) -> None:
        self.context = context
        self.violations = violations
        issues = list(input_issues)
        for violation in violations:
            issues.append(
                ValidationIssue(
                    field=context,
                    code=f"unsupported_claim:{violation.category}",
                    message=(
                        f"{context} contains unsupported {violation.category} claim "
                        f"language at line {violation.line}, column {violation.column}"
                    ),
                    expected="governance text without unsupported research claims",
                    actual=violation.matched_text,
                )
            )
        super().__init__(issues)

    def to_dict(self) -> dict[str, Any]:
        """Return validation issues plus structured claim matches."""

        payload = super().to_dict()
        payload["violations"] = [violation.to_dict() for violation in self.violations]
        return payload


PROHIBITED_CLAIM_TAXONOMY: tuple[ProhibitedClaimRule, ...] = (
    ProhibitedClaimRule(
        category="alpha_validity",
        description="Assertions that a research object has, finds, proves, or generates alpha.",
        patterns=(
            ProhibitedClaimPattern(
                "valid_alpha",
                r"\b(?:valid|validated|proven|predictive|durable|real)\s+alpha\b",
            ),
            ProhibitedClaimPattern(
                "alpha_is_confirmed",
                r"\balpha\s+(?:is\s+)?(?:valid|validated|proven|confirmed|found)\b",
            ),
            ProhibitedClaimPattern(
                "alpha_validity_confirmed",
                (
                    r"\balpha\s+validity\s+(?:is\s+)?"
                    r"(?:proven|validated|confirmed|established)\b"
                ),
            ),
            ProhibitedClaimPattern(
                "establishes_alpha_validity",
                r"\b(?:proves|validates|confirms|establishes|shows)\s+alpha\s+validity\b",
            ),
            ProhibitedClaimPattern(
                "generates_alpha",
                (
                    r"\b(?:is|are|has|have|shows|show|proves|prove|demonstrates|"
                    r"demonstrate|generates|generate|captures|capture|delivers|"
                    r"deliver|yields|yield)\s+(?:durable\s+|validated\s+|valid\s+|"
                    r"predictive\s+|real\s+)?alpha\b(?!\s+validity)"
                ),
            ),
        ),
    ),
    ProhibitedClaimRule(
        category="profitability",
        description="Assertions about profit, profitability, or market-beating behavior.",
        patterns=(
            ProhibitedClaimPattern("profitable", r"\bprofitable\b"),
            ProhibitedClaimPattern(
                "profitability_confirmed",
                r"\bprofitability\s+(?:is\s+)?(?:proven|confirmed|established|validated)\b",
            ),
            ProhibitedClaimPattern(
                "generates_profit",
                r"\b(?:generates|delivers|produces|shows|has)\s+(?:positive\s+)?profits?\b",
            ),
            ProhibitedClaimPattern(
                "positive_pnl",
                r"\b(?:positive|reliable|consistent)\s+pnl\b",
            ),
            ProhibitedClaimPattern("market_beating", r"\bmarket[-\s]?beating\b"),
        ),
    ),
    ProhibitedClaimRule(
        category="tradability",
        description="Assertions that a research object is tradable or ready to trade.",
        patterns=(
            ProhibitedClaimPattern("tradable", r"\btradable\b"),
            ProhibitedClaimPattern("tradeable", r"\btradeable\b"),
            ProhibitedClaimPattern(
                "tradability_confirmed",
                r"\btradability\s+(?:is\s+)?(?:proven|validated|confirmed|established)\b",
            ),
            ProhibitedClaimPattern("can_be_traded", r"\bcan\s+be\s+traded\b"),
            ProhibitedClaimPattern("suitable_for_trading", r"\bsuitable\s+for\s+trading\b"),
            ProhibitedClaimPattern("trading_ready", r"\btrading[-\s]?ready\b"),
        ),
    ),
    ProhibitedClaimRule(
        category="robustness",
        description="Assertions that results are robust without a reviewed claim standard.",
        patterns=(
            ProhibitedClaimPattern("robust", r"\brobust\b"),
            ProhibitedClaimPattern(
                "robustness_confirmed",
                r"\brobustness\s+(?:is\s+)?(?:proven|validated|confirmed|established)\b",
            ),
            ProhibitedClaimPattern(
                "stable_across_contexts",
                r"\bstable\s+across\s+(?:markets|regimes|datasets|periods)\b",
            ),
        ),
    ),
    ProhibitedClaimRule(
        category="production_readiness",
        description="Assertions about production readiness or deployability.",
        patterns=(
            ProhibitedClaimPattern("production_ready", r"\bproduction[-\s]?ready\b"),
            ProhibitedClaimPattern(
                "production_readiness_confirmed",
                (
                    r"\bproduction[-\s]+readiness\s+(?:is\s+)?"
                    r"(?:proven|validated|confirmed|established)\b"
                ),
            ),
            ProhibitedClaimPattern("ready_for_production", r"\bready\s+for\s+production\b"),
            ProhibitedClaimPattern(
                "production_execution_ready",
                r"\bproduction\s+(?:deployment|use|execution)\s+ready\b",
            ),
            ProhibitedClaimPattern("deployable", r"\bdeployable\b"),
            ProhibitedClaimPattern("deployment_ready", r"\bdeployment[-\s]?ready\b"),
        ),
    ),
    ProhibitedClaimRule(
        category="paper_readiness",
        description="Assertions about readiness for paper-trading use.",
        patterns=(
            ProhibitedClaimPattern("paper_ready", r"\bpaper[-\s]?ready\b"),
            ProhibitedClaimPattern(
                "paper_readiness_confirmed",
                (
                    r"\bpaper[-\s]+readiness\s+(?:is\s+)?"
                    r"(?:proven|validated|confirmed|established)\b"
                ),
            ),
            ProhibitedClaimPattern(
                "ready_for_paper_trading",
                r"\bready\s+for\s+paper\s+(?:trading|use)\b",
            ),
            ProhibitedClaimPattern(
                "suitable_for_paper_trading",
                r"\bsuitable\s+for\s+paper\s+trading\b",
            ),
            ProhibitedClaimPattern(
                "paper_trading_ready",
                r"\bpaper\s+trading[-\s]?ready\b",
            ),
        ),
    ),
    ProhibitedClaimRule(
        category="live_readiness",
        description="Assertions about readiness for live use or live execution.",
        patterns=(
            ProhibitedClaimPattern("live_ready", r"\blive[-\s]?ready\b"),
            ProhibitedClaimPattern(
                "live_readiness_confirmed",
                (
                    r"\blive[-\s]+readiness\s+(?:is\s+)?"
                    r"(?:proven|validated|confirmed|established)\b"
                ),
            ),
            ProhibitedClaimPattern(
                "ready_for_live",
                r"\bready\s+for\s+live\s+(?:trading|use|execution)\b",
            ),
            ProhibitedClaimPattern("suitable_for_live_use", r"\bsuitable\s+for\s+live\s+use\b"),
            ProhibitedClaimPattern(
                "live_execution_ready",
                r"\blive\s+(?:trading|execution)[-\s]?ready\b",
            ),
        ),
    ),
    ProhibitedClaimRule(
        category="broker_readiness",
        description="Assertions about broker execution, order routing, or broker readiness.",
        patterns=(
            ProhibitedClaimPattern("broker_ready", r"\bbroker[-\s]?ready\b"),
            ProhibitedClaimPattern(
                "broker_readiness_confirmed",
                (
                    r"\bbroker[-\s]+readiness\s+(?:is\s+)?"
                    r"(?:proven|validated|confirmed|established)\b"
                ),
            ),
            ProhibitedClaimPattern(
                "ready_for_broker",
                r"\bready\s+for\s+broker\s+(?:execution|use)\b",
            ),
            ProhibitedClaimPattern(
                "suitable_for_broker_execution",
                r"\bsuitable\s+for\s+broker\s+execution\b",
            ),
            ProhibitedClaimPattern("safe_to_route_orders", r"\bsafe\s+to\s+route\s+orders\b"),
            ProhibitedClaimPattern("order_routing_ready", r"\border[-\s]?routing[-\s]?ready\b"),
        ),
    ),
    ProhibitedClaimRule(
        category="real_data_readiness",
        description="Assertions that a research object is ready for real data.",
        patterns=(
            ProhibitedClaimPattern("real_data_ready", r"\breal[-\s]?data[-\s]?ready\b"),
            ProhibitedClaimPattern("ready_for_real_data", r"\bready\s+for\s+real\s+data\b"),
            ProhibitedClaimPattern(
                "suitable_for_real_data",
                r"\bsuitable\s+for\s+real\s+data\b",
            ),
            ProhibitedClaimPattern(
                "can_run_on_real_data",
                r"\bcan\s+(?:run|operate|be\s+used)\s+on\s+real\s+data\b",
            ),
            ProhibitedClaimPattern(
                "real_data_readiness_confirmed",
                (
                    r"\breal[-\s]?data[-\s]?readiness\s+(?:is\s+)?"
                    r"(?:confirmed|proven|validated|established)\b"
                ),
            ),
        ),
    ),
)

PERMITTED_CLAIM_CONTEXTS: tuple[PermittedClaimContext, ...] = (
    PermittedClaimContext(
        name="explicit_no_claims",
        description="The local sentence explicitly says the blocked term is not a claim.",
        expression=(
            r"\b(?:no|not|never|without|do\s+not|does\s+not|must\s+not)\b"
            r"[^.?!\n]{0,160}"
            r"\b(?:claim|claims|assert|asserts|assertion|assertions|statement|statements)\b"
        ),
    ),
    PermittedClaimContext(
        name="not_evidence",
        description="The local sentence explicitly says the blocked term is not evidence.",
        expression=r"\b(?:no|not|never|without)\b[^.?!\n]{0,160}\bevidence\b",
    ),
    PermittedClaimContext(
        name="blocked_language_catalog",
        description="The local sentence catalogs blocked or unsupported language.",
        expression=(
            r"\b(?:prohibited|blocked|unsupported|forbidden)\b"
            r"[^.?!\n]{0,160}"
            r"\b(?:claim|claims|language|vocabulary|taxonomy|set|phrase|phrases|"
            r"term|terms|form|forms|category|categories)\b"
        ),
    ),
    PermittedClaimContext(
        name="guard_behavior",
        description="The local sentence describes guard or detector blocking vocabulary.",
        expression=(
            r"\b(?:guard|detector)\b"
            r"[^.?!\n]{0,160}"
            r"\b(?:block|blocks|detect|detects|reject|rejects|prevent|prevents)\b"
            r"[^.?!\n]{0,160}"
            r"\b(?:claim|claims|assert|asserts|assertion|assertions|language|"
            r"vocabulary|taxonomy|term|terms|phrase|phrases|category|categories)\b"
        ),
    ),
    PermittedClaimContext(
        name="governance_identifier",
        description="The local sentence mentions a governance identifier, not a result.",
        expression=r"\b(?:AlphaSpec|alpha_spec_id)\b",
    ),
)

_COMPILED_RULES: tuple[
    tuple[ProhibitedClaimRule, ProhibitedClaimPattern, re.Pattern[str]],
    ...,
] = tuple(
    (rule, pattern, re.compile(pattern.expression, re.IGNORECASE))
    for rule in PROHIBITED_CLAIM_TAXONOMY
    for pattern in rule.patterns
)
_COMPILED_PERMITTED_CONTEXTS: tuple[tuple[PermittedClaimContext, re.Pattern[str]], ...] = tuple(
    (context, re.compile(context.expression, re.IGNORECASE)) for context in PERMITTED_CLAIM_CONTEXTS
)


def find_unsupported_claims(
    text: object,
    *,
    context: str = "governance text",
) -> tuple[UnsupportedClaimViolation, ...]:
    """Return unsupported-claim matches, failing closed on malformed input."""

    normalized_text = _require_decidable_text(text, context=context)
    violations: list[UnsupportedClaimViolation] = []
    seen: set[tuple[str, int, int]] = set()

    for rule, pattern, compiled in _COMPILED_RULES:
        for match in compiled.finditer(normalized_text):
            sentence = _sentence_window(normalized_text, match.start(), match.end())
            if _is_permitted_non_asserting_context(sentence):
                continue
            key = (rule.category, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            line, column = _line_column(normalized_text, match.start())
            violations.append(
                UnsupportedClaimViolation(
                    category=rule.category,
                    pattern_id=pattern.pattern_id,
                    matched_text=match.group(0),
                    line=line,
                    column=column,
                    snippet=_compact_snippet(sentence),
                )
            )
    return tuple(violations)


def has_unsupported_claims(text: object, *, context: str = "governance text") -> bool:
    """Return whether text contains unsupported claims, failing closed on malformed input."""

    return bool(find_unsupported_claims(text, context=context))


def validate_no_unsupported_claims(
    text: object,
    *,
    context: str = "governance text",
) -> None:
    """Raise a structured rejection when text is malformed or contains a blocked claim."""

    violations = find_unsupported_claims(text, context=context)
    if violations:
        raise UnsupportedClaimError(context=context, violations=violations)


assert_no_unsupported_claims = validate_no_unsupported_claims


def _require_decidable_text(text: object, *, context: str) -> str:
    issues: list[ValidationIssue] = []
    if not isinstance(text, str):
        issues.append(
            ValidationIssue(
                field=context,
                code="invalid_text_type",
                message=f"{context} must be a string",
                expected="str",
                actual=type(text).__name__,
            )
        )
        raise UnsupportedClaimError(context=context, input_issues=tuple(issues))

    if not text.strip():
        issues.append(
            ValidationIssue(
                field=context,
                code="empty_text",
                message=f"{context} must not be empty",
                expected="non-empty text",
                actual="empty",
            )
        )

    if "\ufffd" in text:
        issues.append(
            ValidationIssue(
                field=context,
                code="undecidable_text_encoding",
                message=f"{context} contains replacement characters",
                expected="decoded text without replacement characters",
                actual="replacement character present",
            )
        )

    bad_control = _first_disallowed_control(text)
    if bad_control is not None:
        issues.append(
            ValidationIssue(
                field=context,
                code="undecidable_control_character",
                message=f"{context} contains a disallowed control character",
                expected="text without NUL or non-whitespace control characters",
                actual=f"U+{ord(bad_control):04X}",
            )
        )

    if issues:
        raise UnsupportedClaimError(context=context, input_issues=tuple(issues))
    return text


def _first_disallowed_control(text: str) -> str | None:
    for character in text:
        if character in "\t\n\r":
            continue
        if ord(character) < 32:
            return character
    return None


def _sentence_window(text: str, start: int, end: int) -> str:
    left_boundaries = [text.rfind(mark, 0, start) for mark in ".?!\n"]
    left = max(left_boundaries) + 1
    right_candidates = [idx for mark in ".?!\n" if (idx := text.find(mark, end)) != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left:right].strip()


def _is_permitted_non_asserting_context(sentence: str) -> bool:
    return any(compiled.search(sentence) for _, compiled in _COMPILED_PERMITTED_CONTEXTS)


def _line_column(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    previous_newline = text.rfind("\n", 0, index)
    column = index + 1 if previous_newline == -1 else index - previous_newline
    return line, column


def _compact_snippet(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
