"""Symbol batch planning for historical data ingestion.

DATA-P10 owns the ES/NQ/RTY mini main-batch plan and its hard separation from
the MES/MNQ/M2K micro batch. The records in this module are planning records
only: they perform no provider calls, authorize no pull, and write no data.
DATA-P19 owns the separate MES/MNQ/M2K ``MicroBatchPolicy`` secondary path.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from alpha_system.data.foundation.sources import DataFoundationValidationError

REQUIRED_SYMBOL_BATCH_PLAN_FIELDS: tuple[str, ...] = (
    "plan_id",
    "mini_main",
    "micro_secondary",
    "max_concurrent_roots",
    "do_not_mix_mini_and_micro_batches",
)

REQUIRED_MICRO_BATCH_POLICY_FIELDS: tuple[str, ...] = (
    "batch_id",
    "symbols",
    "start_date",
    "separate_batch",
    "parity_check_targets",
)

CANONICAL_MINI_MAIN_ROOTS: tuple[str, ...] = ("ES", "NQ", "RTY")
CANONICAL_MICRO_SECONDARY_ROOTS: tuple[str, ...] = ("MES", "MNQ", "M2K")
CANONICAL_MAX_CONCURRENT_ROOTS = 3
CANONICAL_SYMBOL_BATCH_PLAN_ID = "sbp_mini_main_es_nq_rty_v1"
CANONICAL_MICRO_BATCH_POLICY_ID = "mbp_micro_secondary_mes_mnq_m2k_v1"
CANONICAL_MICRO_BATCH_START_DATE = "2020-01-01"
EARLIEST_CLEAN_AVAILABLE_MARKER = "earliest_clean_available_to_be_verified"
MICRO_BATCH_START_DATE_STATUS = "planning_default_to_be_verified_not_data_claim"
INSTRUMENT_MASTER_RECORD_CONTRACT = "InstrumentMasterRecord"
DATA_P05_INSTRUMENT_ECONOMICS_REFERENCE = "DATA-P05 InstrumentMasterRecord"
DATA_P10_SEPARATION_CONTRACT_REFERENCE = "DATA-P10 SymbolBatchPlan"
HISTORICAL_REQUEST_MANIFEST_CONTRACT = "HistoricalRequestManifest"
REQUEST_PACING_POLICY_CONTRACT = "RequestPacingPolicy"
CANONICAL_REQUEST_PACING_POLICY_ID = "rpp_ibkr_historical_conservative_tobeverified_v1"
CANONICAL_MINI_MICRO_PARITY_TARGETS: tuple[tuple[str, str], ...] = (
    ("ES", "MES"),
    ("NQ", "MNQ"),
    ("RTY", "M2K"),
)

_CANONICAL_MINI_MAIN_ROOT_SET = frozenset(CANONICAL_MINI_MAIN_ROOTS)
_CANONICAL_MICRO_SECONDARY_ROOT_SET = frozenset(CANONICAL_MICRO_SECONDARY_ROOTS)
_CANONICAL_BATCH_ROOT_SET = (
    _CANONICAL_MINI_MAIN_ROOT_SET | _CANONICAL_MICRO_SECONDARY_ROOT_SET
)
_CANONICAL_PARITY_TARGET_SET = frozenset(CANONICAL_MINI_MICRO_PARITY_TARGETS)
_PRESENT_AS_OF_RUN = "present_as_of_run"
_ROLLING_AVAILABLE_EXPIRED_WINDOW = "rolling_available_expired_window"
_ALLOWED_NON_DATE_WINDOW_MARKERS = frozenset(
    {
        _PRESENT_AS_OF_RUN,
        _ROLLING_AVAILABLE_EXPIRED_WINDOW,
        "availability_discovered_not_assumed",
    }
)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not token.replace("_", "").replace("-", "").isalnum():
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


def _require_exact_concurrency(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = "max_concurrent_roots must be the integer 3"
        raise DataFoundationValidationError(msg)
    if value != CANONICAL_MAX_CONCURRENT_ROOTS:
        msg = "max_concurrent_roots must equal 3 and cannot exceed 3"
        raise DataFoundationValidationError(msg)
    return value


def _normalize_root(value: object, field_name: str = "symbol_root") -> str:
    root = _require_text(value, field_name).upper()
    if not root.isalnum():
        msg = f"{field_name} must be alphanumeric"
        raise DataFoundationValidationError(msg)
    if root not in _CANONICAL_BATCH_ROOT_SET:
        allowed = ", ".join(sorted(_CANONICAL_BATCH_ROOT_SET))
        msg = f"{field_name} {root!r} is not in the DATA-P10 mini/micro universe: {allowed}"
        raise DataFoundationValidationError(msg)
    return root


def _normalize_roots(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be a non-empty iterable of symbol roots"
        raise DataFoundationValidationError(msg)

    roots = tuple(_normalize_root(item, field_name) for item in value)
    if not roots:
        msg = f"{field_name} must not be empty"
        raise DataFoundationValidationError(msg)

    duplicate_roots = sorted({root for root in roots if roots.count(root) > 1})
    if duplicate_roots:
        msg = f"{field_name} contains duplicate roots: " + ", ".join(duplicate_roots)
        raise DataFoundationValidationError(msg)

    return roots


def _canonicalize_expected_roots(
    roots: tuple[str, ...],
    *,
    expected_roots: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    expected_set = frozenset(expected_roots)
    root_set = frozenset(roots)
    if root_set != expected_set:
        msg = f"{field_name} must equal " + "/".join(expected_roots)
        raise DataFoundationValidationError(msg)
    return expected_roots


def _require_date_or_window_marker(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if token in _ALLOWED_NON_DATE_WINDOW_MARKERS:
        return token

    parts = token.split("-")
    if (
        len(parts) == 3
        and len(parts[0]) == 4
        and len(parts[1]) == 2
        and len(parts[2]) == 2
        and all(part.isdigit() for part in parts)
    ):
        return token

    msg = (
        f"{field_name} must be an ISO date or an explicit discovered-availability marker"
    )
    raise DataFoundationValidationError(msg)


def _require_micro_start_date(value: object) -> str:
    token = _require_text(value, "start_date")
    if token in {CANONICAL_MICRO_BATCH_START_DATE, EARLIEST_CLEAN_AVAILABLE_MARKER}:
        return token

    msg = (
        "start_date must be 2020-01-01 or "
        "earliest_clean_available_to_be_verified"
    )
    raise DataFoundationValidationError(msg)


def _normalize_session_views(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "session_views must be a non-empty iterable of labels"
        raise DataFoundationValidationError(msg)
    views = tuple(_require_text(item, "session_views") for item in value)
    if not views:
        msg = "session_views must not be empty"
        raise DataFoundationValidationError(msg)
    return views


def _normalize_parity_target_pair(value: object) -> tuple[str, str]:
    if isinstance(value, Mapping):
        allowed_keys = {"mini_root", "micro_root"}
        provided_keys = set(value)
        if provided_keys != allowed_keys:
            msg = (
                "parity_check_targets are declarations only and must contain "
                "only mini_root and micro_root"
            )
            raise DataFoundationValidationError(msg)
        mini_root = _normalize_root(value["mini_root"], "parity_check_targets.mini_root")
        micro_root = _normalize_root(
            value["micro_root"],
            "parity_check_targets.micro_root",
        )
    else:
        if isinstance(value, str) or not isinstance(value, Iterable):
            msg = "parity_check_targets entries must be mini/micro root pairs"
            raise DataFoundationValidationError(msg)
        parts = tuple(value)
        if len(parts) != 2:
            msg = "parity_check_targets entries must contain exactly two roots"
            raise DataFoundationValidationError(msg)
        mini_root = _normalize_root(parts[0], "parity_check_targets.mini_root")
        micro_root = _normalize_root(parts[1], "parity_check_targets.micro_root")

    if mini_root not in _CANONICAL_MINI_MAIN_ROOT_SET:
        msg = "parity_check_targets mini_root must be one of ES/NQ/RTY"
        raise DataFoundationValidationError(msg)
    if micro_root not in _CANONICAL_MICRO_SECONDARY_ROOT_SET:
        msg = "parity_check_targets micro_root must be one of MES/MNQ/M2K"
        raise DataFoundationValidationError(msg)
    if (mini_root, micro_root) not in _CANONICAL_PARITY_TARGET_SET:
        msg = "parity_check_targets must use canonical ES-MES, NQ-MNQ, RTY-M2K pairs"
        raise DataFoundationValidationError(msg)
    return mini_root, micro_root


def _normalize_parity_check_targets(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, Mapping):
        raw_targets = tuple(value.items())
    else:
        if isinstance(value, str) or not isinstance(value, Iterable):
            msg = "parity_check_targets must be a non-empty iterable of root pairs"
            raise DataFoundationValidationError(msg)
        raw_targets = tuple(value)

    if not raw_targets:
        msg = "parity_check_targets must not be empty"
        raise DataFoundationValidationError(msg)

    targets = tuple(_normalize_parity_target_pair(target) for target in raw_targets)
    duplicate_targets = sorted({target for target in targets if targets.count(target) > 1})
    if duplicate_targets:
        formatted = ", ".join(f"{mini}-{micro}" for mini, micro in duplicate_targets)
        msg = "parity_check_targets contains duplicate pairs: " + formatted
        raise DataFoundationValidationError(msg)

    if frozenset(targets) != _CANONICAL_PARITY_TARGET_SET:
        msg = "parity_check_targets must equal ES<->MES, NQ<->MNQ, RTY<->M2K"
        raise DataFoundationValidationError(msg)

    return CANONICAL_MINI_MICRO_PARITY_TARGETS


@dataclass(frozen=True, slots=True)
class SymbolBatchPlan:
    """Fail-closed mini/micro root batch plan.

    The campaign plan is intentionally exact: mini roots are ES/NQ/RTY, micro
    roots are MES/MNQ/M2K, concurrency is capped at and set to three roots, and
    any batch that combines mini and micro roots is rejected.
    """

    plan_id: str
    mini_main: tuple[str, ...]
    micro_secondary: tuple[str, ...]
    max_concurrent_roots: int
    do_not_mix_mini_and_micro_batches: bool

    def __post_init__(self) -> None:
        plan_id = _normalize_id(self.plan_id, "plan_id")
        mini_main = _normalize_roots(self.mini_main, "mini_main")
        micro_secondary = _normalize_roots(self.micro_secondary, "micro_secondary")
        shared_roots = sorted(frozenset(mini_main) & frozenset(micro_secondary))
        if shared_roots:
            msg = "mini_main and micro_secondary must be disjoint: " + ", ".join(shared_roots)
            raise DataFoundationValidationError(msg)

        mini_main = _canonicalize_expected_roots(
            mini_main,
            expected_roots=CANONICAL_MINI_MAIN_ROOTS,
            field_name="mini_main",
        )
        micro_secondary = _canonicalize_expected_roots(
            micro_secondary,
            expected_roots=CANONICAL_MICRO_SECONDARY_ROOTS,
            field_name="micro_secondary",
        )
        max_concurrent_roots = _require_exact_concurrency(self.max_concurrent_roots)
        do_not_mix = _require_bool(
            self.do_not_mix_mini_and_micro_batches,
            "do_not_mix_mini_and_micro_batches",
        )
        if not do_not_mix:
            msg = "do_not_mix_mini_and_micro_batches must be true"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "mini_main", mini_main)
        object.__setattr__(self, "micro_secondary", micro_secondary)
        object.__setattr__(self, "max_concurrent_roots", max_concurrent_roots)
        object.__setattr__(
            self,
            "do_not_mix_mini_and_micro_batches",
            do_not_mix,
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> SymbolBatchPlan:
        """Build a batch plan from persisted/configured values and fail closed."""

        missing = tuple(field for field in REQUIRED_SYMBOL_BATCH_PLAN_FIELDS if field not in values)
        if missing:
            msg = "SymbolBatchPlan missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            plan_id=_require_text(values["plan_id"], "plan_id"),
            mini_main=_normalize_roots(values["mini_main"], "mini_main"),
            micro_secondary=_normalize_roots(
                values["micro_secondary"],
                "micro_secondary",
            ),
            max_concurrent_roots=_require_exact_concurrency(
                values["max_concurrent_roots"],
            ),
            do_not_mix_mini_and_micro_batches=_require_bool(
                values["do_not_mix_mini_and_micro_batches"],
                "do_not_mix_mini_and_micro_batches",
            ),
        )

    @property
    def implies_pull_authorization(self) -> bool:
        """Return false: this planning record never authorizes a pull."""

        return False

    @property
    def mini_root_set(self) -> frozenset[str]:
        """Return the immutable mini-root set."""

        return frozenset(self.mini_main)

    @property
    def micro_root_set(self) -> frozenset[str]:
        """Return the immutable micro-root set."""

        return frozenset(self.micro_secondary)

    def validate_batch_roots(
        self,
        roots: Iterable[object],
        *,
        batch_name: str = "batch",
    ) -> tuple[str, ...]:
        """Validate one batch/root group without permitting mini/micro mixing."""

        normalized_roots = _normalize_roots(roots, batch_name)
        root_set = frozenset(normalized_roots)
        contains_mini = bool(root_set & self.mini_root_set)
        contains_micro = bool(root_set & self.micro_root_set)
        if contains_mini and contains_micro:
            msg = f"{batch_name} mixes mini and micro roots"
            raise DataFoundationValidationError(msg)
        if len(normalized_roots) > self.max_concurrent_roots:
            msg = (
                f"{batch_name} cannot exceed max_concurrent_roots="
                f"{self.max_concurrent_roots}"
            )
            raise DataFoundationValidationError(msg)

        return normalized_roots

    def validate_manifest_roots(
        self,
        manifest: Mapping[str, object] | object,
        *,
        batch_name: str = "manifest request_specs",
    ) -> tuple[str, ...]:
        """Validate roots embedded in a HistoricalRequestManifest-like object."""

        if isinstance(manifest, Mapping):
            request_specs = manifest.get("request_specs")
        else:
            request_specs = getattr(manifest, "request_specs", None)

        if isinstance(request_specs, str) or not isinstance(request_specs, Iterable):
            msg = "manifest request_specs must be an iterable of request spec records"
            raise DataFoundationValidationError(msg)

        roots: list[object] = []
        for request_spec in request_specs:
            if isinstance(request_spec, Mapping):
                if "symbol_root" not in request_spec:
                    msg = "manifest request_specs entries must include symbol_root"
                    raise DataFoundationValidationError(msg)
                roots.append(request_spec["symbol_root"])
            elif hasattr(request_spec, "symbol_root"):
                roots.append(getattr(request_spec, "symbol_root"))
            else:
                msg = "manifest request_specs entries must expose symbol_root"
                raise DataFoundationValidationError(msg)

        unique_roots = tuple(dict.fromkeys(_normalize_root(root) for root in roots))
        return self.validate_batch_roots(unique_roots, batch_name=batch_name)

    def to_mapping(self) -> Mapping[str, object]:
        """Return the JSON-stable required fields without authorization state."""

        return MappingProxyType(
            {
                "plan_id": self.plan_id,
                "mini_main": self.mini_main,
                "micro_secondary": self.micro_secondary,
                "max_concurrent_roots": self.max_concurrent_roots,
                "do_not_mix_mini_and_micro_batches": (
                    self.do_not_mix_mini_and_micro_batches
                ),
            }
        )


@dataclass(frozen=True, slots=True)
class MicroBatchPolicy:
    """Fail-closed MES/MNQ/M2K micro secondary-batch policy.

    The policy is declarative. It references DATA-P05 instrument economics and
    DATA-P10 mini/micro separation contracts, but does not duplicate economics,
    authorize provider pulls, or contain parity results.
    """

    batch_id: str
    symbols: tuple[str, ...]
    start_date: str
    separate_batch: bool
    parity_check_targets: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        batch_id = _normalize_id(self.batch_id, "batch_id")
        symbols = _normalize_roots(self.symbols, "symbols")
        shared_roots = sorted(frozenset(symbols) & _CANONICAL_MINI_MAIN_ROOT_SET)
        if shared_roots:
            msg = "symbols must be disjoint from mini roots: " + ", ".join(shared_roots)
            raise DataFoundationValidationError(msg)
        symbols = _canonicalize_expected_roots(
            symbols,
            expected_roots=CANONICAL_MICRO_SECONDARY_ROOTS,
            field_name="symbols",
        )

        start_date = _require_micro_start_date(self.start_date)
        separate_batch = _require_bool(self.separate_batch, "separate_batch")
        if not separate_batch:
            msg = "separate_batch must be true"
            raise DataFoundationValidationError(msg)

        parity_check_targets = _normalize_parity_check_targets(
            self.parity_check_targets,
        )

        object.__setattr__(self, "batch_id", batch_id)
        object.__setattr__(self, "symbols", symbols)
        object.__setattr__(self, "start_date", start_date)
        object.__setattr__(self, "separate_batch", separate_batch)
        object.__setattr__(self, "parity_check_targets", parity_check_targets)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> MicroBatchPolicy:
        """Build a micro-batch policy from configured values and fail closed."""

        missing = tuple(
            field for field in REQUIRED_MICRO_BATCH_POLICY_FIELDS if field not in values
        )
        if missing:
            msg = "MicroBatchPolicy missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            batch_id=_require_text(values["batch_id"], "batch_id"),
            symbols=_normalize_roots(values["symbols"], "symbols"),
            start_date=_require_micro_start_date(values["start_date"]),
            separate_batch=_require_bool(values["separate_batch"], "separate_batch"),
            parity_check_targets=_normalize_parity_check_targets(
                values["parity_check_targets"],
            ),
        )

    @property
    def implies_pull_authorization(self) -> bool:
        """Return false: this planning record never authorizes a pull."""

        return False

    @property
    def secondary_path(self) -> bool:
        """Return true: micros are a separate secondary path in V1."""

        return True

    @property
    def micro_root_set(self) -> frozenset[str]:
        """Return the immutable micro-root set."""

        return frozenset(self.symbols)

    @property
    def instrument_economics_contract(self) -> str:
        """Reference, without duplicating, the DATA-P05 economics record type."""

        return INSTRUMENT_MASTER_RECORD_CONTRACT

    @property
    def instrument_economics_roots(self) -> tuple[str, ...]:
        """Return roots whose economics are owned by DATA-P05 records."""

        return self.symbols

    @property
    def separation_contract(self) -> Mapping[str, object]:
        """Reference the DATA-P10 mini/micro separation contract."""

        return MappingProxyType(
            {
                "contract_reference": DATA_P10_SEPARATION_CONTRACT_REFERENCE,
                "symbol_batch_plan_id": MINI_MAIN_SYMBOL_BATCH_PLAN.plan_id,
                "do_not_mix_mini_and_micro_batches": (
                    MINI_MAIN_SYMBOL_BATCH_PLAN.do_not_mix_mini_and_micro_batches
                ),
                "max_concurrent_roots": MINI_MAIN_SYMBOL_BATCH_PLAN.max_concurrent_roots,
            }
        )

    def validate_batch_roots(
        self,
        roots: Iterable[object],
        *,
        batch_name: str = "micro batch",
    ) -> tuple[str, ...]:
        """Validate a micro batch without permitting mini roots or partial sets."""

        normalized_roots = _normalize_roots(roots, batch_name)
        mini_roots = sorted(frozenset(normalized_roots) & _CANONICAL_MINI_MAIN_ROOT_SET)
        if mini_roots:
            msg = f"{batch_name} must not include mini roots: " + ", ".join(mini_roots)
            raise DataFoundationValidationError(msg)
        return _canonicalize_expected_roots(
            normalized_roots,
            expected_roots=CANONICAL_MICRO_SECONDARY_ROOTS,
            field_name=batch_name,
        )

    def validate_manifest_roots(
        self,
        manifest: Mapping[str, object] | object,
        *,
        batch_name: str = "micro manifest request_specs",
    ) -> tuple[str, ...]:
        """Validate roots embedded in a HistoricalRequestManifest-like object."""

        if isinstance(manifest, Mapping):
            request_specs = manifest.get("request_specs")
        else:
            request_specs = getattr(manifest, "request_specs", None)

        if isinstance(request_specs, str) or not isinstance(request_specs, Iterable):
            msg = "micro manifest request_specs must be an iterable of request spec records"
            raise DataFoundationValidationError(msg)

        roots: list[object] = []
        for request_spec in request_specs:
            if isinstance(request_spec, Mapping):
                if "symbol_root" not in request_spec:
                    msg = "micro manifest request_specs entries must include symbol_root"
                    raise DataFoundationValidationError(msg)
                roots.append(request_spec["symbol_root"])
            elif hasattr(request_spec, "symbol_root"):
                roots.append(getattr(request_spec, "symbol_root"))
            else:
                msg = "micro manifest request_specs entries must expose symbol_root"
                raise DataFoundationValidationError(msg)

        unique_roots = tuple(dict.fromkeys(_normalize_root(root) for root in roots))
        return self.validate_batch_roots(unique_roots, batch_name=batch_name)

    def to_mapping(self) -> Mapping[str, object]:
        """Return the JSON-stable required fields without authorization state."""

        return MappingProxyType(
            {
                "batch_id": self.batch_id,
                "symbols": self.symbols,
                "start_date": self.start_date,
                "separate_batch": self.separate_batch,
                "parity_check_targets": self.parity_check_targets,
            }
        )


@dataclass(frozen=True, slots=True)
class MiniBatchPanelWindow:
    """Immutable panel-window definition for the ES/NQ/RTY mini plan."""

    panel_id: str
    roots: tuple[str, ...]
    start_date: str
    end_date: str
    bar_size: str
    what_to_show: str
    session_views: tuple[str, ...]
    panel_role: str
    qa_or_diagnostic_label: str | None
    manifest_contract: str
    pacing_policy_id: str
    merge_into_primary_common_panel: bool
    availability_policy: str

    def __post_init__(self) -> None:
        panel_id = _normalize_id(self.panel_id, "panel_id")
        roots = _normalize_roots(self.roots, "panel roots")
        root_set = frozenset(roots)
        if root_set & _CANONICAL_MICRO_SECONDARY_ROOT_SET:
            msg = "mini batch panel roots must not include micro roots"
            raise DataFoundationValidationError(msg)
        if not root_set <= _CANONICAL_MINI_MAIN_ROOT_SET:
            msg = "mini batch panel roots must be a subset of ES/NQ/RTY"
            raise DataFoundationValidationError(msg)

        start_date = _require_date_or_window_marker(self.start_date, "start_date")
        end_date = _require_date_or_window_marker(self.end_date, "end_date")
        bar_size = _require_text(self.bar_size, "bar_size")
        if bar_size != "1 min":
            msg = "mini batch panel bar_size must be 1 min"
            raise DataFoundationValidationError(msg)
        what_to_show = _require_text(self.what_to_show, "what_to_show").upper()
        if what_to_show != "TRADES":
            msg = "mini batch panel what_to_show must be TRADES"
            raise DataFoundationValidationError(msg)

        session_views = _normalize_session_views(self.session_views)
        panel_role = _require_text(self.panel_role, "panel_role")
        is_optional = panel_role.startswith("optional_secondary")
        qa_or_diagnostic_label = self.qa_or_diagnostic_label
        if qa_or_diagnostic_label is not None:
            qa_or_diagnostic_label = _require_text(
                qa_or_diagnostic_label,
                "qa_or_diagnostic_label",
            )
        if is_optional and qa_or_diagnostic_label is None:
            msg = "optional secondary panels require a QA or diagnostic label"
            raise DataFoundationValidationError(msg)

        manifest_contract = _require_text(self.manifest_contract, "manifest_contract")
        if manifest_contract != HISTORICAL_REQUEST_MANIFEST_CONTRACT:
            msg = "manifest_contract must reference HistoricalRequestManifest"
            raise DataFoundationValidationError(msg)
        pacing_policy_id = _normalize_id(self.pacing_policy_id, "pacing_policy_id")
        if pacing_policy_id != CANONICAL_REQUEST_PACING_POLICY_ID:
            msg = "pacing_policy_id must reference the DATA-P08 RequestPacingPolicy"
            raise DataFoundationValidationError(msg)
        merge_into_primary = _require_bool(
            self.merge_into_primary_common_panel,
            "merge_into_primary_common_panel",
        )
        if is_optional and merge_into_primary:
            msg = "optional secondary panels must not be merged into the primary common panel"
            raise DataFoundationValidationError(msg)
        availability_policy = _require_text(self.availability_policy, "availability_policy")

        object.__setattr__(self, "panel_id", panel_id)
        object.__setattr__(self, "roots", roots)
        object.__setattr__(self, "start_date", start_date)
        object.__setattr__(self, "end_date", end_date)
        object.__setattr__(self, "bar_size", bar_size)
        object.__setattr__(self, "what_to_show", what_to_show)
        object.__setattr__(self, "session_views", session_views)
        object.__setattr__(self, "panel_role", panel_role)
        object.__setattr__(self, "qa_or_diagnostic_label", qa_or_diagnostic_label)
        object.__setattr__(self, "manifest_contract", manifest_contract)
        object.__setattr__(self, "pacing_policy_id", pacing_policy_id)
        object.__setattr__(self, "merge_into_primary_common_panel", merge_into_primary)
        object.__setattr__(self, "availability_policy", availability_policy)

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable panel-window planning record."""

        return MappingProxyType(
            {
                "panel_id": self.panel_id,
                "roots": self.roots,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "bar_size": self.bar_size,
                "what_to_show": self.what_to_show,
                "session_views": self.session_views,
                "panel_role": self.panel_role,
                "qa_or_diagnostic_label": self.qa_or_diagnostic_label,
                "manifest_contract": self.manifest_contract,
                "pacing_policy_id": self.pacing_policy_id,
                "merge_into_primary_common_panel": (
                    self.merge_into_primary_common_panel
                ),
                "availability_policy": self.availability_policy,
            }
        )


MINI_MAIN_SYMBOL_BATCH_PLAN = SymbolBatchPlan(
    plan_id=CANONICAL_SYMBOL_BATCH_PLAN_ID,
    mini_main=CANONICAL_MINI_MAIN_ROOTS,
    micro_secondary=CANONICAL_MICRO_SECONDARY_ROOTS,
    max_concurrent_roots=CANONICAL_MAX_CONCURRENT_ROOTS,
    do_not_mix_mini_and_micro_batches=True,
)

MINI_PRIMARY_COMMON_PANEL = MiniBatchPanelWindow(
    panel_id="mini_primary_common_panel",
    roots=CANONICAL_MINI_MAIN_ROOTS,
    start_date="2018-01-01",
    end_date=_PRESENT_AS_OF_RUN,
    bar_size="1 min",
    what_to_show="TRADES",
    session_views=("ETH_canonical", "RTH_derived"),
    panel_role="primary_common_panel",
    qa_or_diagnostic_label=None,
    manifest_contract=HISTORICAL_REQUEST_MANIFEST_CONTRACT,
    pacing_policy_id=CANONICAL_REQUEST_PACING_POLICY_ID,
    merge_into_primary_common_panel=False,
    availability_policy="modern_common_panel_planning_only_no_data_exists_claim",
)

MINI_OPTIONAL_SECONDARY_PANELS: tuple[MiniBatchPanelWindow, ...] = (
    MiniBatchPanelWindow(
        panel_id="mini_optional_es_nq_long_qa_panel",
        roots=("ES", "NQ"),
        start_date="2015-01-01",
        end_date=_PRESENT_AS_OF_RUN,
        bar_size="1 min",
        what_to_show="TRADES",
        session_views=("ETH_canonical", "RTH_derived"),
        panel_role="optional_secondary_qa",
        qa_or_diagnostic_label=(
            "ES/NQ long-panel data-QA and regime baseline; provider-continuous if needed"
        ),
        manifest_contract=HISTORICAL_REQUEST_MANIFEST_CONTRACT,
        pacing_policy_id=CANONICAL_REQUEST_PACING_POLICY_ID,
        merge_into_primary_common_panel=False,
        availability_policy="not_primary_common_panel_missing_rty_era_differences_labeled",
    ),
    MiniBatchPanelWindow(
        panel_id="mini_optional_rty_transition_qa_panel",
        roots=("RTY",),
        start_date="2017-07-10",
        end_date="2017-12-31",
        bar_size="1 min",
        what_to_show="TRADES",
        session_views=("ETH_canonical", "RTH_derived"),
        panel_role="optional_secondary_qa",
        qa_or_diagnostic_label="RTY CME transition QA only",
        manifest_contract=HISTORICAL_REQUEST_MANIFEST_CONTRACT,
        pacing_policy_id=CANONICAL_REQUEST_PACING_POLICY_ID,
        merge_into_primary_common_panel=False,
        availability_policy="qa_only_not_primary_panel",
    ),
    MiniBatchPanelWindow(
        panel_id="mini_optional_contract_truth_diagnostic_panel",
        roots=CANONICAL_MINI_MAIN_ROOTS,
        start_date=_ROLLING_AVAILABLE_EXPIRED_WINDOW,
        end_date="availability_discovered_not_assumed",
        bar_size="1 min",
        what_to_show="TRADES",
        session_views=("ETH_canonical", "RTH_derived"),
        panel_role="optional_secondary_diagnostic",
        qa_or_diagnostic_label=(
            "Contract-truth diagnostic for discovered dated FUT availability only"
        ),
        manifest_contract=HISTORICAL_REQUEST_MANIFEST_CONTRACT,
        pacing_policy_id=CANONICAL_REQUEST_PACING_POLICY_ID,
        merge_into_primary_common_panel=False,
        availability_policy="dated_fut_availability_discovered_not_assumed",
    ),
)

MINI_MAIN_BATCH_PULL_PLAN: Mapping[str, object] = MappingProxyType(
    {
        "plan_id": MINI_MAIN_SYMBOL_BATCH_PLAN.plan_id,
        "symbol_batch_plan": MINI_MAIN_SYMBOL_BATCH_PLAN.to_mapping(),
        "primary_common_panel": MINI_PRIMARY_COMMON_PANEL.to_mapping(),
        "optional_secondary_panels": tuple(
            panel.to_mapping() for panel in MINI_OPTIONAL_SECONDARY_PANELS
        ),
        "manifest_contract": HISTORICAL_REQUEST_MANIFEST_CONTRACT,
        "pacing_policy_contract": REQUEST_PACING_POLICY_CONTRACT,
        "pacing_policy_id": CANONICAL_REQUEST_PACING_POLICY_ID,
        "external_provider_call": False,
        "pull_authorization": False,
        "data_exists_claim": False,
    }
)


MICRO_BATCH_POLICY = MicroBatchPolicy(
    batch_id=CANONICAL_MICRO_BATCH_POLICY_ID,
    symbols=CANONICAL_MICRO_SECONDARY_ROOTS,
    start_date=CANONICAL_MICRO_BATCH_START_DATE,
    separate_batch=True,
    parity_check_targets=CANONICAL_MINI_MICRO_PARITY_TARGETS,
)

MICRO_BATCH_PLAN: Mapping[str, object] = MappingProxyType(
    {
        "batch_id": MICRO_BATCH_POLICY.batch_id,
        "policy": MICRO_BATCH_POLICY.to_mapping(),
        "secondary_path": MICRO_BATCH_POLICY.secondary_path,
        "v1_source_role": "secondary_path_not_primary_alpha_source",
        "start_date_status": MICRO_BATCH_START_DATE_STATUS,
        "instrument_economics_reference": DATA_P05_INSTRUMENT_ECONOMICS_REFERENCE,
        "instrument_economics_contract": MICRO_BATCH_POLICY.instrument_economics_contract,
        "instrument_economics_roots": MICRO_BATCH_POLICY.instrument_economics_roots,
        "separation_contract": MICRO_BATCH_POLICY.separation_contract,
        "parity_check_declaration_only": True,
        "parity_check_targets": MICRO_BATCH_POLICY.parity_check_targets,
        "external_provider_call": False,
        "pull_authorization": False,
        "data_exists_claim": False,
    }
)


__all__ = [
    "CANONICAL_MAX_CONCURRENT_ROOTS",
    "CANONICAL_MICRO_BATCH_POLICY_ID",
    "CANONICAL_MICRO_BATCH_START_DATE",
    "CANONICAL_MICRO_SECONDARY_ROOTS",
    "CANONICAL_MINI_MICRO_PARITY_TARGETS",
    "CANONICAL_MINI_MAIN_ROOTS",
    "CANONICAL_REQUEST_PACING_POLICY_ID",
    "CANONICAL_SYMBOL_BATCH_PLAN_ID",
    "DATA_P05_INSTRUMENT_ECONOMICS_REFERENCE",
    "DATA_P10_SEPARATION_CONTRACT_REFERENCE",
    "EARLIEST_CLEAN_AVAILABLE_MARKER",
    "HISTORICAL_REQUEST_MANIFEST_CONTRACT",
    "INSTRUMENT_MASTER_RECORD_CONTRACT",
    "MICRO_BATCH_PLAN",
    "MICRO_BATCH_POLICY",
    "MICRO_BATCH_START_DATE_STATUS",
    "MINI_MAIN_BATCH_PULL_PLAN",
    "MINI_MAIN_SYMBOL_BATCH_PLAN",
    "MINI_OPTIONAL_SECONDARY_PANELS",
    "MINI_PRIMARY_COMMON_PANEL",
    "MicroBatchPolicy",
    "MiniBatchPanelWindow",
    "REQUEST_PACING_POLICY_CONTRACT",
    "REQUIRED_MICRO_BATCH_POLICY_FIELDS",
    "REQUIRED_SYMBOL_BATCH_PLAN_FIELDS",
    "SymbolBatchPlan",
]
