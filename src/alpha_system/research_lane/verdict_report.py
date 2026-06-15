"""Human-readable verdict report renderer for precomputed idea readouts."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from alpha_system.governance.idea_draft import (
    CONTEXT_NOT_EQUAL_TRIGGER,
    MAIN_EFFECT,
    IdeaDraft,
    validate_idea_draft,
)
from alpha_system.governance.validation import GovernanceValidationError, ValidationIssue
from alpha_system.governance.verdict_reason_code import (
    VerdictReasonCode,
    validate_verdict_reason_code,
)
from alpha_system.research.conditional_probe import (
    NET_EXCURSION_OUTCOME,
    NET_EXCURSION_TRIVIAL_LIFT_EPS,
)
from alpha_system.research_lane.testability_gate import CHECK_ORDER, TestabilityGateResult

ALLOWED_REPORT_VERDICTS = frozenset(
    {"REJECT", "DATA_GAP", "INCONCLUSIVE", "WATCH", "CANDIDATE"}
)


class VerdictReportError(ValueError):
    """Raised when a verdict report input is malformed."""


def render_verdict_report(
    idea_draft: IdeaDraft | Mapping[str, Any],
    testability_result: TestabilityGateResult | Mapping[str, Any],
    fast_readout: Mapping[str, Any],
) -> str:
    """Render a deterministic governed ``REPORT.md`` from precomputed summaries.

    The renderer performs no I/O, resolves no packs, loads no values, and computes
    no metric. It only formats ids, counts, gate outcomes, and diagnostic summary
    fields already present in the supplied inputs.
    """

    idea = _idea_mapping(idea_draft)
    gate = _mapping_from_object(testability_result, object_name="testability_result")
    readout = _mapping_from_object(fast_readout, object_name="fast_readout")
    slice_spec = _mapping(readout.get("slice_spec"), default={})
    mechanism = _mapping(readout.get("mechanism_card"), default={})
    dedup = _mapping(mechanism.get("duplicate_exposure"), default={})
    class_summary = _class_summary(gate, readout)
    n_eff, mde = _n_eff_mde(gate, readout)
    surrogate = _surrogate_summary(readout, gate)
    verdict = _derive_report_verdict(
        gate=gate,
        readout=readout,
        class_summary=class_summary,
        n_eff=n_eff,
        surrogate_state=surrogate["state"],
    )

    lines: list[str] = [
        "# Idea Verdict Report",
        "",
        "## Idea Summary",
        f"- alpha_spec_id: {_display(idea.get('alpha_spec_id'))}",
        f"- mechanism_id: {_display(idea.get('mechanism_id'))}",
        f"- setup_spec_id: {_display(idea.get('setup_spec_id'))}",
        f"- hypothesis_id: {_display(idea.get('hypothesis_id'))}",
        f"- source: {_display(idea.get('source'))}",
        "",
        "## Study Kind",
        f"- study_kind: {_display(idea.get('study_kind') or readout.get('study_kind'))}",
        "",
        "## Slice",
        f"- slice_id: {_display(slice_spec.get('slice_id') or gate.get('slice_id'))}",
        f"- instrument: {_display(slice_spec.get('instrument_id'))}",
        f"- session: {_display(slice_spec.get('session_id'))}",
        f"- window: {_window(slice_spec)}",
        f"- dataset_version_id: {_display(slice_spec.get('dataset_version_id'))}",
        f"- partition_id: {_display(slice_spec.get('partition_id'))}",
        f"- feature_pack_refs: {_join_or_none(_pack_refs(slice_spec, 'feature'))}",
        f"- label_pack_refs: {_join_or_none(_pack_refs(slice_spec, 'label'))}",
        "",
        "## Data / Features / Labels Used",
        f"- data_version: {_display(slice_spec.get('data_version'))}",
        "- features:",
    ]
    lines.extend(_input_lines(slice_spec, "feature_inputs", "features", empty_label="none"))
    lines.append("- labels:")
    lines.extend(_input_lines(slice_spec, "label_inputs", "labels", empty_label="none"))
    lines.extend(
        [
            "",
            "## Dedup Outcome",
        ]
    )
    lines.extend(_mapping_lines(dedup, empty_label="none"))
    lines.extend(
        [
            "",
            "## Testability Gates",
        ]
    )
    lines.extend(_gate_lines(gate))
    lines.extend(
        [
            "",
            "## Fast Readout",
            f"- status: {_display(readout.get('status'))}",
            f"- issue_code: {_display(readout.get('issue_code'))}",
            f"- engine: {_display(readout.get('engine'))}",
            f"- class_count: {_display(class_summary.get('class_count'))}",
            f"- minority_count: {_display(class_summary.get('minority_count'))}",
            f"- row_access: {_row_access(readout)}",
            "",
            "## N_eff / MDE",
            f"- n_eff: {_display(n_eff)}",
            f"- mde: {_display(mde)}",
            "",
            "## Surrogate State",
            f"- state: {surrogate['state']}",
            f"- threshold_verdict: {_display(surrogate.get('threshold_verdict'))}",
            f"- gate_status: {_display(surrogate.get('gate_status'))}",
            "",
        ]
    )
    lift = _continuous_lift_summary(readout)
    if lift is not None:
        lines.extend(
            [
                "## Path Outcome Diagnostics",
                f"- outcome_label_type: {_display(lift.get('outcome_label_type'))}",
                f"- conditioned_mean: {_display(lift.get('conditioned_mean'))}",
                f"- base_mean: {_display(lift.get('base_mean'))}",
                f"- mean_lift: {_display(lift.get('mean_lift'))}",
                f"- conditioned_n: {_display(lift.get('conditioned_n'))}",
                f"- base_n: {_display(lift.get('base_n'))}",
                "",
            ]
        )
    lines.extend(
        [
            "## Final Verdict",
            f"- verdict: {verdict['verdict']}",
            f"- reason_code: {verdict['reason_code']}",
            f"- why: {verdict['why']}",
            f"- next_action: {verdict['next_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def _continuous_lift_summary(readout: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Surface the continuous-outcome conditioned-mean-lift diagnostic if present.

    Display-only: the value is already computed by evaluate_setup_conditional_probe;
    the renderer just locates and formats it (it is nested under the readout's
    diagnostics). Returns None for binary/main_effect readouts that have no
    continuous outcome lift.
    """

    return _find_mapping_with_keys(readout, ("mean_lift", "conditioned_mean", "base_mean"))


def _idea_mapping(value: IdeaDraft | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, IdeaDraft):
        return value.to_dict()
    if isinstance(value, Mapping):
        return validate_idea_draft(value).to_dict()
    raise VerdictReportError("idea_draft must be an IdeaDraft or mapping")


def _mapping_from_object(value: Any, *, object_name: str) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise VerdictReportError(f"{object_name} must be a mapping or expose to_dict()")
    return dict(value)


def _mapping(value: Any, *, default: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return dict(default or {})


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return tuple(value)
    return ()


def _display(value: Any) -> str:
    if value is None or value == "":
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def _join_or_none(values: Iterable[Any]) -> str:
    rendered = [_display(value) for value in values if value not in (None, "")]
    return ", ".join(rendered) if rendered else "none"


def _window(slice_spec: Mapping[str, Any]) -> str:
    parts: list[str] = []
    if slice_spec.get("horizon_seconds") is not None:
        parts.append(f"horizon_seconds={_display(slice_spec.get('horizon_seconds'))}")
    if slice_spec.get("required_future_bars") is not None:
        parts.append(f"required_future_bars={_display(slice_spec.get('required_future_bars'))}")
    if slice_spec.get("created_at") is not None:
        parts.append(f"created_at={_display(slice_spec.get('created_at'))}")
    return "; ".join(parts) if parts else "n/a"


def _pack_refs(slice_spec: Mapping[str, Any], kind: str) -> tuple[str, ...]:
    direct_key = f"{kind}_pack_refs"
    if direct_key in slice_spec:
        return tuple(str(item) for item in _sequence(slice_spec.get(direct_key)) if item)
    input_key = "feature_inputs" if kind == "feature" else "label_inputs"
    legacy_key = "features" if kind == "feature" else "labels"
    refs: list[str] = []
    for item in _sequence(slice_spec.get(input_key) or slice_spec.get(legacy_key)):
        if isinstance(item, Mapping):
            ref = item.get("pack_ref") or item.get(f"{kind}_pack_ref")
            if ref:
                refs.append(str(ref))
    return tuple(refs)


def _input_lines(
    slice_spec: Mapping[str, Any],
    primary_key: str,
    fallback_key: str,
    *,
    empty_label: str,
) -> list[str]:
    rows = _sequence(slice_spec.get(primary_key) or slice_spec.get(fallback_key))
    if not rows:
        return [f"  - {empty_label}"]
    lines: list[str] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        if primary_key == "feature_inputs":
            lines.append(
                "  - "
                f"role={_display(item.get('role'))}; "
                f"factor_id={_display(item.get('factor_id'))}; "
                f"factor_version={_display(item.get('factor_version'))}; "
                f"pack_ref={_display(item.get('pack_ref'))}; "
                f"feature_request_id={_display(item.get('feature_request_id'))}"
            )
        else:
            lines.append(
                "  - "
                f"role={_display(item.get('role'))}; "
                f"label_id={_display(item.get('label_id'))}; "
                f"pack_ref={_display(item.get('pack_ref'))}; "
                f"label_spec_id={_display(item.get('label_spec_id'))}"
            )
    return lines or [f"  - {empty_label}"]


def _mapping_lines(mapping: Mapping[str, Any], *, empty_label: str) -> list[str]:
    if not mapping:
        return [f"- {empty_label}"]
    return [f"- {key}: {_display_jsonish(value)}" for key, value in sorted(mapping.items())]


def _display_jsonish(value: Any) -> str:
    if isinstance(value, Mapping):
        items = ", ".join(
            f"{key}={_display_jsonish(item)}" for key, item in sorted(value.items())
        )
        return "{" + items + "}"
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return "[" + ", ".join(_display_jsonish(item) for item in value) + "]"
    return _display(value)


def _gate_lines(gate: Mapping[str, Any]) -> list[str]:
    checks = _checks_by_id(gate)
    lines: list[str] = []
    for check_id in CHECK_ORDER:
        check = checks.get(check_id)
        if check is None:
            lines.append(f"- {check_id}: DATA_GAP - missing from testability_result")
            continue
        detail = _mapping(check.get("detail"), default={})
        message = detail.get("message") or detail.get("reason") or "no detail"
        lines.append(
            f"- {check_id}: {_display(check.get('status'))} - {_display(message)}"
        )
    return lines


def _checks_by_id(gate: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}
    for item in _sequence(gate.get("checks")):
        if not isinstance(item, Mapping):
            continue
        check_id = item.get("check_id")
        if check_id:
            checks[str(check_id)] = dict(item)
    return checks


def _class_summary(gate: Mapping[str, Any], readout: Mapping[str, Any]) -> dict[str, Any]:
    for check in _checks_by_id(gate).values():
        detail = _mapping(check.get("detail"), default={})
        candidate = _mapping(detail.get("class_balance"), default={})
        if "class_count" in candidate:
            return {
                "class_count": candidate.get("class_count"),
                "minority_count": candidate.get("minority_class_count")
                if candidate.get("minority_class_count") is not None
                else candidate.get("minority_count"),
            }
    found = _find_mapping_with_keys(readout, ("class_count",))
    if found:
        return {
            "class_count": found.get("class_count"),
            "minority_count": found.get("minority_class_count")
            if found.get("minority_class_count") is not None
            else found.get("minority_count"),
        }
    return {"class_count": None, "minority_count": None}


def _n_eff_mde(gate: Mapping[str, Any], readout: Mapping[str, Any]) -> tuple[Any, Any]:
    power = _mapping(readout.get("power"), default={})
    if not power:
        power = _mapping(_find_mapping_with_keys(readout, ("n_eff",)), default={})
    if power:
        n_eff = power.get("n_eff")
        mde = (
            power.get("minimum_detectable_effect")
            if power.get("minimum_detectable_effect") is not None
            else power.get("minimum_detectable_abs_ic")
        )
        if mde is None:
            mde = power.get("mde_abs_ic")
        return n_eff, mde
    for check in _checks_by_id(gate).values():
        detail = _mapping(check.get("detail"), default={})
        if "n_eff" in detail or "minimum_detectable_effect" in detail:
            return detail.get("n_eff"), detail.get("minimum_detectable_effect")
    return None, None


def _surrogate_summary(
    readout: Mapping[str, Any],
    gate: Mapping[str, Any],
) -> dict[str, Any]:
    surrogate = _mapping(readout.get("surrogate_fdr_gate"), default={})
    threshold = surrogate.get("threshold_verdict")
    gate_status = surrogate.get("gate_status")
    if _is_blocked(gate_status) or _is_blocked(threshold):
        state = "BLOCKED"
    elif _is_zero_pass(threshold):
        state = "ZERO_PASS_MET"
    else:
        state = "UNKNOWN"
    if state == "UNKNOWN":
        for check in _checks_by_id(gate).values():
            detail = _mapping(check.get("detail"), default={})
            requirement = detail.get("surrogate_fdr_requirement") or detail.get("expected")
            if _is_zero_pass(requirement):
                state = "ZERO_PASS_MET"
                threshold = requirement
                break
    return {
        "state": state,
        "threshold_verdict": threshold,
        "gate_status": gate_status,
    }


def _derive_report_verdict(
    *,
    gate: Mapping[str, Any],
    readout: Mapping[str, Any],
    class_summary: Mapping[str, Any],
    n_eff: Any,
    surrogate_state: Any,
) -> dict[str, str]:
    class_count = _int_or_none(class_summary.get("class_count"))
    if class_count is not None and class_count < 2:
        return _verdict(
            "DATA_GAP",
            VerdictReasonCode.DATA_QUALITY,
            "Path-label slice has fewer than two distinct classes.",
            "Choose or repair a bounded slice with at least two observed classes.",
        )

    overall = str(gate.get("overall_status") or gate.get("verdict") or "").upper()
    if overall == "FAIL":
        check = _first_check_with_status(gate, "FAIL")
        return _verdict(
            "REJECT",
            _reason_for_check(check),
            f"Pre-test gate failed at {check or 'unknown_check'}.",
            "Do not spend a probe shot until the blocking gate is corrected.",
        )
    if overall == "DATA_GAP":
        check = _first_check_with_status(gate, "DATA_GAP")
        return _verdict(
            "DATA_GAP",
            _reason_for_check(check),
            f"Pre-test gate reports DATA_GAP at {check or 'unknown_check'}.",
            "Resolve the missing substrate or metadata before interpretation.",
        )

    issue_code = str(readout.get("issue_code") or "").upper()
    status = str(readout.get("status") or "").upper()
    study_kind = str(readout.get("study_kind") or "").strip().lower()
    # A context!=trigger setup readout owns its own surrogate-gate / power
    # classification (a not-met surrogate gate is a WELL_POWERED_NULL REJECT when
    # power is adequate, an UNDERPOWERED INCONCLUSIVE otherwise) rather than being
    # swept into the generic substrate-gap DATA_GAP. Genuine substrate gaps (an
    # explicit DATA_GAP issue/status or an unresolved row access) still short-circuit
    # here; only the surrogate-BLOCKED / zero-n_eff sub-conditions defer to
    # _derive_setup_verdict.
    generic_gap = (
        issue_code == "DATA_GAP"
        or status == "DATA_GAP"
        or _row_access_unresolved(readout)
    )
    if study_kind != CONTEXT_NOT_EQUAL_TRIGGER:
        generic_gap = generic_gap or _int_or_none(n_eff) == 0 or surrogate_state == "BLOCKED"
    if generic_gap:
        return _verdict(
            "DATA_GAP",
            VerdictReasonCode.SUBSTRATE_GAP,
            "Fast readout reports an unresolved data or calibration gap.",
            "Resolve the blocked slice inputs before rerendering the report.",
        )

    explicit = _explicit_verdict(readout)
    if explicit is not None:
        return explicit

    if study_kind == MAIN_EFFECT:
        return _derive_main_effect_verdict(readout, n_eff)
    if study_kind == CONTEXT_NOT_EQUAL_TRIGGER:
        return _derive_setup_verdict(readout, n_eff)

    return _verdict(
        "INCONCLUSIVE",
        VerdictReasonCode.DATA_QUALITY,
        "No upstream governed final verdict was supplied with the readout.",
        "Keep the readout in research review until a governed verdict is attached.",
    )


def _derive_main_effect_verdict(
    readout: Mapping[str, Any],
    n_eff: Any,
) -> dict[str, str]:
    """Map a main_effect factor-diagnostics readout to a non-promoting verdict.

    Generic for any factor-shaped continuous-label IC probe (no factor is
    special-cased). Thresholds use only report-provided values: the detectable
    floor ``ic_power_mde_abs_ic`` already folds in z=1.96 (mde = z * se), so
    ``|ic| >= mde`` is exactly ``|ic|/se >= 1.96``. No magic constants.

    - invalid diagnostics / missing IC -> INCONCLUSIVE + DATA_QUALITY
    - cannot establish a detectable floor -> INCONCLUSIVE + UNDERPOWERED
    - well-powered and both |IC| below floor -> REJECT + WELL_POWERED_NULL
    - well-powered, both |IC| above floor, same sign -> INCONCLUSIVE +
      SIGNAL_PENDING_REVIEWER (routed to the non-promoting reviewer shelf)
    - mixed (one above one below) or sign-conflicting -> INCONCLUSIVE +
      REVIEW_NEEDED

    The machine may classify evidence autonomously; it may never autonomously
    promote. A resolved signal stays INCONCLUSIVE (a non-promoting verdict);
    only the reason_code and the signal-shelf sidecar distinguish it.
    """

    summary = _mapping(_mapping(readout.get("readout"), default={}).get(
        "factor_diagnostics_report"
    ), default={})
    quality = _mapping(summary.get("quality_summary"), default={})

    diagnostic_pass = quality.get("diagnostic_pass")
    failing = _int_or_none(quality.get("failing_gate_count"))
    if diagnostic_pass is False or (failing is not None and failing > 0):
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.DATA_QUALITY,
            "Main-effect diagnostics did not pass their quality gates.",
            "Resolve the failing diagnostic gates before interpretation.",
        )

    pearson = _float_or_none(quality.get("pearson_ic"))
    rank = _float_or_none(quality.get("rank_ic"))
    if pearson is None or rank is None:
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.DATA_QUALITY,
            "Main-effect readout did not expose both pearson and rank IC.",
            "Keep the readout in research review until complete IC diagnostics exist.",
        )

    mde = _float_or_none(quality.get("ic_power_mde_abs_ic"))
    n_eff_value = _int_or_none(quality.get("ic_power_n_eff")) or _int_or_none(n_eff)
    well_powered = (
        mde is not None
        and math.isfinite(mde)
        and mde > 0
        and n_eff_value is not None
        and n_eff_value >= 2
    )
    if not well_powered:
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.UNDERPOWERED,
            "Main-effect probe could not establish a detectable IC floor at adequate power.",
            "Requeue for evidence accrual; revisit when power improves.",
        )

    pearson_above = abs(pearson) >= mde
    rank_above = abs(rank) >= mde
    if not pearson_above and not rank_above:
        return _verdict(
            "REJECT",
            VerdictReasonCode.WELL_POWERED_NULL,
            (
                f"Well-powered main-effect probe found no IC above the detectable floor "
                f"(|pearson|={abs(pearson):.6f}, |rank|={abs(rank):.6f}, mde={mde:.6f})."
            ),
            "Route to graveyard; no detectable factor information at adequate power.",
        )
    if pearson_above != rank_above:
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.REVIEW_NEEDED,
            "Main-effect pearson and rank IC disagree on detectability across the floor.",
            "Reviewer must adjudicate the mixed IC evidence; no autonomous promotion.",
        )
    if math.copysign(1.0, pearson) != math.copysign(1.0, rank):
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.REVIEW_NEEDED,
            "Main-effect pearson and rank IC are both resolved but disagree in sign.",
            "Reviewer must adjudicate the sign-conflicting IC evidence; no autonomous promotion.",
        )
    return _verdict(
        "INCONCLUSIVE",
        VerdictReasonCode.SIGNAL_PENDING_REVIEWER,
        (
            f"Well-powered main-effect probe resolved an IC above the detectable floor "
            f"(pearson={pearson:.6f}, rank={rank:.6f}, mde={mde:.6f}); recorded as a "
            "non-promoting signal."
        ),
        "Route to the reviewer-pending signal shelf; only the reviewer gate may promote.",
    )


def _derive_setup_verdict(
    readout: Mapping[str, Any],
    n_eff: Any,
) -> dict[str, str]:
    """Map a context!=trigger setup-lane readout to a non-promoting verdict.

    Mirrors the main_effect verdict's discipline and reason codes; the machine may
    classify evidence autonomously but never autonomously promotes (a resolved
    signal stays INCONCLUSIVE, distinguished only by reason_code + signal shelf).

    - missing/invalid continuous_outcome_mean_lift -> INCONCLUSIVE + DATA_QUALITY
    - surrogate gate NOT ZERO_PASS_MET -> REJECT + WELL_POWERED_NULL when power is
      adequate (n_eff >= 2), else INCONCLUSIVE + UNDERPOWERED. The surrogate gate is
      the FDR significance test; not met = no distinguishable conditioned effect.
    - surrogate ZERO_PASS_MET on the SIGNED net_excursion outcome with a non-trivial
      |mean_lift| -> INCONCLUSIVE + SIGNAL_PENDING_REVIEWER (a resolved, surrogate-
      gated signed directional asymmetry; routed to the reviewer shelf).
    - surrogate ZERO_PASS_MET on a SINGLE-excursion outcome (mfe/mae alone) ->
      INCONCLUSIVE + REVIEW_NEEDED (single-excursion significance is volatility-
      confounded; a signed net_excursion run is required to decide directional edge).
    """

    surrogate_state = _surrogate_summary(readout, {})["state"]
    gate = _mapping(readout.get("surrogate_fdr_gate"), default={})
    error_count = _int_or_none(gate.get("error_count")) or 0
    n_eff_value = _int_or_none(n_eff)
    if n_eff_value is None:
        n_eff_value = _int_or_none(gate.get("conditioned_n_eff"))
    adequately_powered = n_eff_value is not None and n_eff_value >= 2
    if surrogate_state != "ZERO_PASS_MET":
        # Surrogate-FDR gate NOT met: no conditioned effect is distinguishable from
        # the block-shuffle null. This branch does NOT require a lift (the lane early
        # returns a surrogate-blocked readout without one). A genuine calibration
        # error is DATA_QUALITY; a well-powered "not distinguishable" is a
        # WELL_POWERED_NULL REJECT (prune it); an underpowered one requeues.
        if error_count > 0:
            return _verdict(
                "INCONCLUSIVE",
                VerdictReasonCode.DATA_QUALITY,
                "Setup probe surrogate calibration failed (surrogate iterations errored).",
                "Resolve the calibration error before interpretation.",
            )
        if adequately_powered:
            observed = _float_or_none(gate.get("observed_effect"))
            observed_txt = "" if observed is None else f" (observed effect={observed:.6f})"
            return _verdict(
                "REJECT",
                VerdictReasonCode.WELL_POWERED_NULL,
                (
                    "Well-powered setup probe found no conditioned effect distinguishable "
                    f"from the block-shuffle surrogate null{observed_txt}."
                ),
                "Route to graveyard; no distinguishable conditioned effect at adequate power.",
            )
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.UNDERPOWERED,
            "Setup probe surrogate gate was not met and power is inadequate to call a null.",
            "Requeue for evidence accrual; revisit when power improves.",
        )

    # ZERO_PASS_MET: require the conditioned-mean lift to classify a (non-promoting) signal.
    lift = _continuous_lift_summary(readout)
    mean_lift = _float_or_none(lift.get("mean_lift")) if lift is not None else None
    if mean_lift is None:
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.DATA_QUALITY,
            "Setup readout passed the surrogate gate but exposed no continuous-outcome mean_lift.",
            "Keep the readout in research review until a valid mean_lift is attached.",
        )

    outcome_label_type = str(lift.get("outcome_label_type") or "").strip()
    if outcome_label_type == NET_EXCURSION_OUTCOME:
        if abs(mean_lift) <= NET_EXCURSION_TRIVIAL_LIFT_EPS:
            return _verdict(
                "INCONCLUSIVE",
                VerdictReasonCode.DATA_QUALITY,
                (
                    "Surrogate-gated net_excursion mean_lift is trivially zero "
                    f"(|mean_lift|={abs(mean_lift):.6f}); no signed directional asymmetry."
                ),
                "Keep in research review; a near-zero net excursion carries no signed edge.",
            )
        return _verdict(
            "INCONCLUSIVE",
            VerdictReasonCode.SIGNAL_PENDING_REVIEWER,
            (
                "Surrogate-gated net_excursion resolved a signed directional asymmetry "
                f"(mean_lift={mean_lift:.6f}); recorded as a non-promoting signal."
            ),
            "Route to the reviewer-pending signal shelf; only the reviewer gate may promote.",
        )
    return _verdict(
        "INCONCLUSIVE",
        VerdictReasonCode.REVIEW_NEEDED,
        (
            "Surrogate-gated single-excursion outcome "
            f"({outcome_label_type or 'unknown'}) is significant but volatility-confounded; "
            "a signed net_excursion run is required to decide directional edge."
        ),
        "Run the signed net_excursion outcome before any directional interpretation.",
    )


def _explicit_verdict(readout: Mapping[str, Any]) -> dict[str, str] | None:
    raw = (
        readout.get("verdict")
        or readout.get("final_verdict")
        or readout.get("report_verdict")
    )
    if raw is None:
        return None
    verdict = str(raw).strip().upper()
    if verdict not in ALLOWED_REPORT_VERDICTS:
        raise GovernanceValidationError(
            ValidationIssue(
                field="verdict",
                code="invalid_report_verdict",
                message="report verdict must be one of the allowed governed outputs",
                expected=" | ".join(sorted(ALLOWED_REPORT_VERDICTS)),
                actual=str(raw),
            )
        )
    reason_raw = readout.get("reason_code") or readout.get("verdict_reason_code")
    if reason_raw is None and verdict == "INCONCLUSIVE":
        reason = VerdictReasonCode.DATA_QUALITY
    elif reason_raw is None:
        reason = _default_reason_for_verdict(verdict)
    else:
        reason = validate_verdict_reason_code(reason_raw, field="reason_code")
    why = str(readout.get("why") or readout.get("verdict_reason") or _default_why(verdict))
    next_action = str(readout.get("next_action") or _default_next_action(verdict))
    return _verdict(verdict, reason, why, next_action)


def _verdict(
    verdict: str,
    reason_code: VerdictReasonCode,
    why: str,
    next_action: str,
) -> dict[str, str]:
    reason = validate_verdict_reason_code(reason_code)
    return {
        "verdict": verdict,
        "reason_code": reason.value,
        "why": why,
        "next_action": next_action,
    }


def _first_check_with_status(gate: Mapping[str, Any], status: str) -> str | None:
    for check_id in CHECK_ORDER:
        check = _checks_by_id(gate).get(check_id)
        if check is not None and str(check.get("status")).upper() == status:
            return check_id
    for check_id, check in _checks_by_id(gate).items():
        if str(check.get("status")).upper() == status:
            return check_id
    return None


def _reason_for_check(check_id: str | None) -> VerdictReasonCode:
    if check_id is None:
        return VerdictReasonCode.DATA_QUALITY
    if "feature" in check_id or "label" in check_id:
        return VerdictReasonCode.SUBSTRATE_GAP
    if "dedup" in check_id or "duplicate" in check_id:
        return VerdictReasonCode.DUPLICATE_EXPOSURE
    if "n_eff" in check_id or "mde" in check_id:
        return VerdictReasonCode.UNDERPOWERED
    if "lookahead" in check_id or "available_ts" in check_id:
        return VerdictReasonCode.LEAKAGE_BLOCKED
    return VerdictReasonCode.DATA_QUALITY


def _default_reason_for_verdict(verdict: str) -> VerdictReasonCode:
    if verdict == "REJECT":
        return VerdictReasonCode.DATA_QUALITY
    if verdict == "DATA_GAP":
        return VerdictReasonCode.SUBSTRATE_GAP
    if verdict == "INCONCLUSIVE":
        return VerdictReasonCode.DATA_QUALITY
    if verdict == "WATCH":
        return VerdictReasonCode.REGIME_UNSTABLE
    return VerdictReasonCode.UNDERPOWERED


def _default_why(verdict: str) -> str:
    if verdict == "WATCH":
        return "Upstream governed readout requested WATCH routing."
    if verdict == "CANDIDATE":
        return "Upstream governed readout requested CANDIDATE routing."
    if verdict == "REJECT":
        return "Upstream governed readout requested REJECT routing."
    if verdict == "DATA_GAP":
        return "Upstream governed readout requested DATA_GAP routing."
    return "Upstream governed readout did not produce a final interpretation."


def _default_next_action(verdict: str) -> str:
    if verdict == "WATCH":
        return "Keep as a research-only watch item for reviewer routing."
    if verdict == "CANDIDATE":
        return "Send to reviewer-gated candidate routing outside this renderer."
    if verdict == "REJECT":
        return "Record the rejection reason through governed follow-up routing."
    if verdict == "DATA_GAP":
        return "Resolve the named gap before rerendering."
    return "Attach a governed reason code before any further routing."


def _row_access(readout: Mapping[str, Any]) -> str:
    row_access = _mapping(readout.get("row_access"), default={})
    if not row_access:
        return "n/a"
    parts = []
    for key in ("status", "fabricated_values", "reason"):
        if key in row_access:
            parts.append(f"{key}={_display(row_access.get(key))}")
    return "; ".join(parts) if parts else "n/a"


def _row_access_unresolved(readout: Mapping[str, Any]) -> bool:
    row_access = _mapping(readout.get("row_access"), default={})
    return str(row_access.get("status") or "").lower() in {"unresolved", "blocked", "missing"}


def _find_mapping_with_keys(value: Any, keys: tuple[str, ...]) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        if all(key in value for key in keys):
            return value
        for item in value.values():
            found = _find_mapping_with_keys(item, keys)
            if found is not None:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            found = _find_mapping_with_keys(item, keys)
            if found is not None:
                return found
    return None


def _is_blocked(value: Any) -> bool:
    return str(value or "").strip().upper() in {"BLOCKED", "CALIBRATION_BLOCKED"}


def _is_zero_pass(value: Any) -> bool:
    normalized = str(value or "").strip().replace("-", "_").upper()
    return normalized == "ZERO_PASS_MET"


def _int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


__all__ = [
    "ALLOWED_REPORT_VERDICTS",
    "VerdictReportError",
    "render_verdict_report",
]
