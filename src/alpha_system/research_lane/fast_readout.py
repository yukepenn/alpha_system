"""Typed contract for the fast-probe ``readout`` glue seam (Stage A, additive).

``fast_probe`` (``research_lane/fast_probe.py``) returns an untyped ``dict``
"readout" that wires together otherwise-typed islands (``ConditionalProbeReadout``,
``SignalPendingReviewerRecord``, ``FactorDiagnosticsRunResult``, ``SliceSpec``).
Every downstream consumer (``verdict_report.py``, ``memory_router.py``,
``reviewer.py``) re-discovers that dict's shape by string keys and recursive
searches, so any rename / relocation / new lane drifts silently and is absorbed
by multi-spelling fallbacks and mirror parsers.

This module pins the *current* producer shape into a typed, lane-discriminated
family so drift fails loudly at the boundary instead of silently downstream. It
is the Stage-A regression baseline of ``FAST_READOUT_CONTRACT_V1``:

- ADDITIVE and ZERO-BREAK. It does NOT modify the producer's output shape and it
  does NOT migrate any consumer. ``verdict_report`` / ``memory_router`` /
  ``reviewer`` are untouched in Stage A. Stage B migrates them onto these types.
- Canonical field names only. ``from_dict`` reads the single canonical spelling
  the producer writes today and *raises* (``FastReadoutContractError``) on a
  missing required field for the resolved lane/status or on an unknown
  ``study_kind``. There are deliberately NO multi-spelling fallbacks here -- the
  drift those fallbacks mask is exactly what this contract is meant to surface.
- Round-trip preserving. ``FastReadout.from_dict(producer_output).to_dict()``
  preserves every field the current consumers read, so Stage B can migrate
  safely. Large opaque sub-dicts that do not drift (``mechanism_card``,
  ``setup_spec``, ``slice_spec``, ``resolved_handles``, ``row_access``,
  ``variant_ledger_binding``, and the nested ``readout`` payload) are carried as
  passthrough ``dict`` fields; only the fields that DRIFT (``n_eff``, the
  continuous-lift summary, the surrogate gate, the IC quality summary, the
  verdict/status/issue_code, ``study_kind``) are typed field-by-field.

This is research-only diagnostic plumbing. It defines no PnL/value truth and
makes no profitability, tradability, or alpha claim.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.signal_pending_reviewer import (
    STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER,
    STUDY_KIND_MAIN_EFFECT,
)

# Producer status / issue codes (canonical spellings the producer writes today).
FAST_READOUT_STATUS_RECORDED = "RECORDED"
FAST_READOUT_STATUS_INCONCLUSIVE = "INCONCLUSIVE"
FAST_READOUT_ISSUE_DATA_GAP = "DATA_GAP"

# The two lanes the producer discriminates on. Imported from the governance
# constants so this contract never invents a fourth spelling.
FAST_READOUT_STUDY_KINDS = (STUDY_KIND_MAIN_EFFECT, STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER)


class FastReadoutContractError(ValueError):
    """Raised when a producer readout does not match the typed contract.

    A raise here is the loud-at-the-boundary signal that the producer shape and
    this contract have drifted -- the failure Stage A exists to surface instead
    of a silent downstream ``.get()`` returning ``None``.
    """


def _require_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FastReadoutContractError(
            f"fast readout field {field_name!r} must be a mapping; got {type(value).__name__}"
        )
    return value


def _require(mapping: Mapping[str, Any], key: str, *, context: str) -> Any:
    if key not in mapping:
        raise FastReadoutContractError(f"fast readout {context} is missing required field {key!r}")
    return mapping[key]


def _opt_dict(value: Any) -> dict[str, JsonValue] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise FastReadoutContractError(f"expected a mapping or None; got {type(value).__name__}")
    return dict(value)


@dataclass(frozen=True, slots=True)
class ContinuousLiftSummary:
    """Typed view of the setup-lane continuous-outcome conditioned-mean lift.

    Produced by ``continuous_outcome_mean_lift`` and carried on a setup
    ZERO_PASS_MET readout under ``readout.diagnostics.continuous_outcome_mean_lift``.
    Present only for the ``context_not_equal_trigger`` lane's RECORDED path.
    """

    outcome_label_type: str
    mean_lift: float | None
    conditioned_mean: float | None
    base_mean: float | None
    conditioned_n: int
    base_n: int

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "outcome_label_type": self.outcome_label_type,
            "conditioned_mean": self.conditioned_mean,
            "base_mean": self.base_mean,
            "mean_lift": self.mean_lift,
            "conditioned_n": self.conditioned_n,
            "base_n": self.base_n,
        }

    @classmethod
    def from_dict(cls, mapping: Mapping[str, Any]) -> ContinuousLiftSummary:
        active = _require_mapping(mapping, field_name="continuous_outcome_mean_lift")
        context = "continuous_outcome_mean_lift"
        return cls(
            outcome_label_type=str(_require(active, "outcome_label_type", context=context)),
            mean_lift=_as_optional_float(active.get("mean_lift")),
            conditioned_mean=_as_optional_float(active.get("conditioned_mean")),
            base_mean=_as_optional_float(active.get("base_mean")),
            conditioned_n=int(_require(active, "conditioned_n", context=context)),
            base_n=int(_require(active, "base_n", context=context)),
        )


@dataclass(frozen=True, slots=True)
class SurrogateFdrGate:
    """Typed view of the surrogate-FDR zero-pass gate.

    ``build_surrogate_zero_pass_gate`` writes ``gate_status`` / ``threshold_verdict``
    / ``run_count`` / ``gate_pass_count`` / ``error_count`` / ``promotion_evidence``.
    ``run_label_shuffle_surrogate`` additionally attaches ``conditioned_n_eff`` and
    ``observed_effect`` (present on the setup lane; absent on a bare DATA_GAP gate).

    The PARTIAL gate the ``alpha idea run`` pre-probe path emits
    (``cli/idea.py:_pre_probe_exploratory_readout``) carries ONLY ``gate_status`` +
    ``threshold_verdict`` -- a not-yet-run gate. ``run_count`` / ``gate_pass_count``
    / ``error_count`` are therefore OPTIONAL and default to 0 (a gate that never ran
    has 0 runs -- faithful). ``_present_count_keys`` records which of the three count
    keys the source actually carried so ``to_dict`` re-emits EXACTLY what came in
    (a partial gate stays partial; a full gate stays full) -- zero-break round-trip.
    """

    gate_status: str
    threshold_verdict: str
    run_count: int = 0
    gate_pass_count: int = 0
    error_count: int = 0
    promotion_evidence: bool = False
    conditioned_n_eff: int | None = None
    observed_effect: float | None = None
    # Which count keys the source mapping carried (for exact round-trip of a partial
    # vs full gate). ``None`` means the gate was built via the bare constructor (no
    # presence tracking) -> emit the full count set. An explicit frozenset (even the
    # empty one) means the gate was parsed -> emit only the keys that were present.
    # Internal bookkeeping; never emitted as its own key.
    _present_count_keys: frozenset[str] | None = None
    # Whether the source carried promotion_evidence explicitly (a partial gate omits it).
    _had_promotion_evidence: bool | None = None

    _COUNT_KEYS = ("run_count", "gate_pass_count", "error_count")

    def to_dict(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "gate_status": self.gate_status,
            "threshold_verdict": self.threshold_verdict,
        }
        # Re-emit each count key only if the source carried it (preserve partial vs
        # full exactly). A gate built via the bare constructor (presence is None)
        # emits all three counts, matching the full-gate house shape.
        present = (
            frozenset(self._COUNT_KEYS)
            if self._present_count_keys is None
            else self._present_count_keys
        )
        if "run_count" in present:
            payload["run_count"] = self.run_count
        if "gate_pass_count" in present:
            payload["gate_pass_count"] = self.gate_pass_count
        if "error_count" in present:
            payload["error_count"] = self.error_count
        emit_promotion = (
            self._present_count_keys is None
            if self._had_promotion_evidence is None
            else self._had_promotion_evidence
        )
        if emit_promotion:
            payload["promotion_evidence"] = self.promotion_evidence
        # conditioned_n_eff / observed_effect are present only when the surrogate
        # actually ran (setup lane); preserve their presence/absence exactly.
        if self.conditioned_n_eff is not None:
            payload["conditioned_n_eff"] = self.conditioned_n_eff
        if self.observed_effect is not None:
            payload["observed_effect"] = self.observed_effect
        return payload

    @classmethod
    def from_dict(cls, mapping: Mapping[str, Any]) -> SurrogateFdrGate:
        active = _require_mapping(mapping, field_name="surrogate_fdr_gate")
        context = "surrogate_fdr_gate"
        present = frozenset(key for key in cls._COUNT_KEYS if key in active)
        return cls(
            gate_status=str(_require(active, "gate_status", context=context)),
            threshold_verdict=str(_require(active, "threshold_verdict", context=context)),
            run_count=int(active.get("run_count", 0)),
            gate_pass_count=int(active.get("gate_pass_count", 0)),
            error_count=int(active.get("error_count", 0)),
            promotion_evidence=bool(active.get("promotion_evidence", False)),
            conditioned_n_eff=_as_optional_int(active.get("conditioned_n_eff")),
            observed_effect=_as_optional_float(active.get("observed_effect")),
            _present_count_keys=present,
            _had_promotion_evidence="promotion_evidence" in active,
        )


@dataclass(frozen=True, slots=True)
class IcQualitySummary:
    """Typed view of the main_effect IC quality summary that consumers read.

    Lives at ``readout.factor_diagnostics_report.quality_summary`` on a
    main_effect RECORDED readout (the full summary carries more keys; only the
    fields the current consumers read are typed here, the rest is passthrough).
    """

    diagnostic_pass: bool | None
    failing_gate_count: int | None
    pearson_ic: float | None
    rank_ic: float | None
    bucket_rank_correlation: float | None
    ic_power_mde_abs_ic: float | None
    ic_power_n_eff: int | None
    # The full quality_summary as written by the producer, so to_dict() round-trips
    # the untyped tail (decay/bucket/etc.) that downstream may later read.
    extra: dict[str, JsonValue] = field(default_factory=dict)

    _TYPED_KEYS = (
        "diagnostic_pass",
        "failing_gate_count",
        "pearson_ic",
        "rank_ic",
        "bucket_rank_correlation",
        "ic_power_mde_abs_ic",
        "ic_power_n_eff",
    )

    def to_dict(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = dict(self.extra)
        payload["diagnostic_pass"] = self.diagnostic_pass
        payload["failing_gate_count"] = self.failing_gate_count
        payload["pearson_ic"] = self.pearson_ic
        payload["rank_ic"] = self.rank_ic
        payload["bucket_rank_correlation"] = self.bucket_rank_correlation
        payload["ic_power_mde_abs_ic"] = self.ic_power_mde_abs_ic
        payload["ic_power_n_eff"] = self.ic_power_n_eff
        return payload

    @classmethod
    def from_dict(cls, mapping: Mapping[str, Any]) -> IcQualitySummary:
        active = _require_mapping(mapping, field_name="quality_summary")
        extra = {key: value for key, value in active.items() if key not in cls._TYPED_KEYS}
        return cls(
            diagnostic_pass=_as_optional_bool(active.get("diagnostic_pass")),
            failing_gate_count=_as_optional_int(active.get("failing_gate_count")),
            pearson_ic=_as_optional_float(active.get("pearson_ic")),
            rank_ic=_as_optional_float(active.get("rank_ic")),
            bucket_rank_correlation=_as_optional_float(active.get("bucket_rank_correlation")),
            ic_power_mde_abs_ic=_as_optional_float(active.get("ic_power_mde_abs_ic")),
            ic_power_n_eff=_as_optional_int(active.get("ic_power_n_eff")),
            extra=dict(extra),
        )


@dataclass(frozen=True, slots=True)
class PowerStatement:
    """Typed canonical view of the top-level IC-power statement's MDE.

    ``build_ic_power_statement`` (``runtime/diagnostics/power.py``) is the single
    sanctioned power builder; it writes the detectable floor under the CANONICAL
    key ``mde_abs_ic``. The contract reads ONLY that canonical spelling -- the
    historical ``minimum_detectable_abs_ic`` / ``minimum_detectable_effect``
    spellings are exactly the drift this contract eliminates (see A2.6/A2.7 which
    canonicalize the two producers that still wrote the legacy key at source).
    """

    n_eff: int | None
    mde_abs_ic: float | None

    @classmethod
    def from_dict(cls, mapping: Mapping[str, Any]) -> PowerStatement:
        active = _require_mapping(mapping, field_name="power")
        return cls(
            n_eff=_as_optional_int(active.get("n_eff")),
            mde_abs_ic=_as_optional_float(active.get("mde_abs_ic")),
        )


@dataclass(frozen=True, slots=True)
class FastReadout:
    """Lane-discriminated typed contract for one fast-probe readout.

    The lane is ``study_kind`` (main_effect vs context_not_equal_trigger) and the
    status/issue distinguishes RECORDED vs INCONCLUSIVE (DATA_GAP or
    surrogate-blocked). The single canonical accessor ``n_eff`` resolves the one
    cross-lane field that drifts today:

    - setup ZERO_PASS_MET: top-level ``power.n_eff``,
    - main_effect RECORDED: ``quality_summary.ic_power_n_eff``,
    - surrogate-blocked / DATA_GAP: top-level ``power.n_eff`` (the producer writes
      the conditioned overlap-aware n_eff -- or 0 for DATA_GAP -- into the power
      statement on these paths).

    Consumers read ``readout.n_eff`` instead of a broad recursive search, so they
    can never grab the wrong nested ``n_eff`` again.
    """

    schema: str
    status: str
    study_kind: str
    stamp: str
    promotion_eligible: bool
    readout_id: str
    issue_code: str | None
    # Typed drift-prone sub-objects (presence is lane/status dependent).
    power: dict[str, JsonValue] | None
    surrogate_fdr_gate: SurrogateFdrGate | None
    ic_quality_summary: IcQualitySummary | None
    continuous_lift_summary: ContinuousLiftSummary | None
    # Passthrough opaque sub-dicts (typed elsewhere or non-drifting). Preserved
    # verbatim for round-trip so Stage B can migrate consumers safely.
    passthrough: dict[str, JsonValue] = field(default_factory=dict)

    # Keys lifted into typed fields; everything else stays in ``passthrough``.
    _TYPED_TOP_KEYS = (
        "schema",
        "status",
        "study_kind",
        "stamp",
        "promotion_eligible",
        "readout_id",
        "issue_code",
        "power",
        "surrogate_fdr_gate",
    )

    @property
    def n_eff(self) -> int:
        """The single canonical effective-sample count for this readout's lane.

        One resolution order (no depth-varying duplicate, no recursive search),
        reproducing today's prefer-power-fallback-gate behavior
        (``memory_router._setup_conditioned_n_eff`` + ``verdict_report._n_eff_mde``):

        - main_effect with an IC quality summary: ``ic_quality_summary.ic_power_n_eff``;
        - otherwise top-level ``power.n_eff`` when present and not None;
        - else ``surrogate_fdr_gate.conditioned_n_eff`` when present;
        - else 0 (a DATA_GAP / not-yet-run gate carries n_eff 0 by construction).
        """

        if self.study_kind == STUDY_KIND_MAIN_EFFECT and self.ic_quality_summary is not None:
            value = self.ic_quality_summary.ic_power_n_eff
            return int(value) if value is not None else 0
        if self.power is not None:
            value = self.power.get("n_eff")
            if value is not None:
                return int(value)
        gate = self.surrogate_fdr_gate
        if gate is not None and gate.conditioned_n_eff is not None:
            return int(gate.conditioned_n_eff)
        return 0

    @property
    def mde_abs_ic(self) -> float | None:
        """The canonical detectable-floor MDE for this readout (single spelling).

        main_effect reads the IC quality summary's ``ic_power_mde_abs_ic``; every
        other lane reads the top-level power statement's canonical ``mde_abs_ic``.
        Reads ONLY the canonical key -- no ``minimum_detectable_*`` fallback.
        """

        if self.study_kind == STUDY_KIND_MAIN_EFFECT and self.ic_quality_summary is not None:
            return self.ic_quality_summary.ic_power_mde_abs_ic
        if self.power is not None:
            return _as_optional_float(self.power.get("mde_abs_ic"))
        return None

    def to_dict(self) -> dict[str, JsonValue]:
        """Round-trip the producer output: typed fields + verbatim passthrough."""

        payload: dict[str, JsonValue] = dict(self.passthrough)
        payload["schema"] = self.schema
        payload["status"] = self.status
        payload["study_kind"] = self.study_kind
        payload["stamp"] = self.stamp
        payload["promotion_eligible"] = self.promotion_eligible
        payload["readout_id"] = self.readout_id
        if self.issue_code is not None:
            payload["issue_code"] = self.issue_code
        if self.power is not None:
            payload["power"] = dict(self.power)
        if self.surrogate_fdr_gate is not None:
            payload["surrogate_fdr_gate"] = self.surrogate_fdr_gate.to_dict()
        return payload

    @classmethod
    def from_dict(cls, mapping: Mapping[str, Any]) -> FastReadout:
        """Parse a producer readout into the typed contract or raise on drift.

        Lane-discriminates on ``study_kind`` and validates the required fields for
        the resolved (lane, status) shape. Reads canonical field names only.
        """

        active = _require_mapping(mapping, field_name="<readout>")
        study_kind = str(_require(active, "study_kind", context="readout"))
        if study_kind not in FAST_READOUT_STUDY_KINDS:
            raise FastReadoutContractError(
                f"unknown study_kind {study_kind!r}; expected one of "
                f"{', '.join(FAST_READOUT_STUDY_KINDS)}"
            )
        status = str(_require(active, "status", context="readout"))
        issue_code_raw = active.get("issue_code")
        issue_code = None if issue_code_raw is None else str(issue_code_raw)

        power = _opt_dict(active.get("power"))
        surrogate_raw = active.get("surrogate_fdr_gate")
        surrogate = None if surrogate_raw is None else SurrogateFdrGate.from_dict(surrogate_raw)

        ic_quality = None
        continuous_lift = None

        if study_kind == STUDY_KIND_MAIN_EFFECT:
            # main_effect RECORDED carries the nested IC quality summary downstream
            # reads. A main_effect INCONCLUSIVE (the `alpha idea run` pre-probe
            # gate-FAIL / DATA_GAP path emits study_kind=main_effect with an empty
            # `readout: {}`) carries NO IC summary -- ic_quality_summary is None there
            # (A2.2). Require the summary ONLY when status == RECORDED.
            if status == FAST_READOUT_STATUS_RECORDED:
                ic_quality = cls._extract_main_effect_quality(active)
        else:
            # context_not_equal_trigger: RECORDED (ZERO_PASS_MET) carries the nested
            # conditional-probe readout with the continuous lift + surrogate gate.
            # INCONCLUSIVE (surrogate-blocked / DATA_GAP / pre-probe gate-FAIL) carries
            # the gate and/or power but no nested readout/lift.
            if status == FAST_READOUT_STATUS_RECORDED:
                # A2.3: require the surrogate gate + continuous lift; do NOT hard-require
                # a top-level power statement (the ZERO_PASS_MET signal-routing path
                # resolves n_eff via power-then-gate, so a missing power falls back to
                # the gate's conditioned_n_eff -- see the n_eff accessor).
                continuous_lift = cls._extract_setup_lift(active)
                if surrogate is None:
                    raise FastReadoutContractError(
                        "context_not_equal_trigger RECORDED readout requires surrogate_fdr_gate"
                    )
            elif issue_code == FAST_READOUT_ISSUE_DATA_GAP:
                # A bare fast_probe DATA_GAP carries a power statement; the pre-probe
                # DATA_GAP path also carries a (zero) power statement. Require neither
                # the gate nor lift here -- a DATA_GAP is honestly empty of diagnostics.
                pass
            elif surrogate is None:
                # surrogate-blocked INCONCLUSIVE (a real not-met gate): carries the
                # real surrogate gate. A pre-probe PRE_TEST_FAIL carries a partial
                # gate (gate_status/threshold only) which still parses via A2.1.
                raise FastReadoutContractError(
                    "surrogate-blocked readout requires surrogate_fdr_gate"
                )

        passthrough = {
            key: value for key, value in active.items() if key not in cls._TYPED_TOP_KEYS
        }
        return cls(
            schema=str(_require(active, "schema", context="readout")),
            status=status,
            study_kind=study_kind,
            stamp=str(_require(active, "stamp", context="readout")),
            promotion_eligible=bool(_require(active, "promotion_eligible", context="readout")),
            readout_id=str(_require(active, "readout_id", context="readout")),
            issue_code=issue_code,
            power=power,
            surrogate_fdr_gate=surrogate,
            ic_quality_summary=ic_quality,
            continuous_lift_summary=continuous_lift,
            passthrough=dict(passthrough),
        )

    @staticmethod
    def _extract_main_effect_quality(active: Mapping[str, Any]) -> IcQualitySummary:
        inner = _require_mapping(
            _require(active, "readout", context="main_effect readout"),
            field_name="readout",
        )
        report = _require_mapping(
            _require(inner, "factor_diagnostics_report", context="main_effect readout.readout"),
            field_name="factor_diagnostics_report",
        )
        quality = _require(
            report, "quality_summary", context="main_effect factor_diagnostics_report"
        )
        return IcQualitySummary.from_dict(quality)

    @staticmethod
    def _extract_setup_lift(active: Mapping[str, Any]) -> ContinuousLiftSummary:
        inner = _require_mapping(
            _require(active, "readout", context="setup readout"),
            field_name="readout",
        )
        diagnostics = _require_mapping(
            _require(inner, "diagnostics", context="setup readout.readout"),
            field_name="diagnostics",
        )
        lift = _require(
            diagnostics, "continuous_outcome_mean_lift", context="setup readout.diagnostics"
        )
        return ContinuousLiftSummary.from_dict(lift)


def _as_optional_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    raise FastReadoutContractError(f"expected a float or None; got {type(value).__name__}")


def _as_optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    raise FastReadoutContractError(f"expected an int or None; got {type(value).__name__}")


def _as_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise FastReadoutContractError(f"expected a bool or None; got {type(value).__name__}")


def validate_fast_readout(mapping: Mapping[str, Any]) -> FastReadout:
    """Module-level validator mirroring the governance ``validate_*`` house style."""

    return FastReadout.from_dict(mapping)


__all__ = [
    "FAST_READOUT_ISSUE_DATA_GAP",
    "FAST_READOUT_STATUS_INCONCLUSIVE",
    "FAST_READOUT_STATUS_RECORDED",
    "FAST_READOUT_STUDY_KINDS",
    "ContinuousLiftSummary",
    "FastReadout",
    "FastReadoutContractError",
    "IcQualitySummary",
    "PowerStatement",
    "SurrogateFdrGate",
    "validate_fast_readout",
]
