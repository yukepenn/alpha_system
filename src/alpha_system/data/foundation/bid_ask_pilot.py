"""Optional BID_ASK pilot plan and spread-proxy diagnostics.

DATA-P20 owns a planning-only BID_ASK pilot and a deterministic spread-proxy
scaffold. This module performs no provider calls, authorizes no pull, opens no
sockets, writes no market data, and does not feed the canonical TRADES panel.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType

from alpha_system.data.foundation.datasets import CoverageReport, DataQualityReport
from alpha_system.data.foundation.requests import (
    HistoricalPullLedger,
    HistoricalRequestManifest,
    RequestPacingPolicy,
    require_pacing_policy_for_provider_pull,
    require_validated_manifest_for_provider_pull,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

REQUIRED_BID_ASK_PILOT_PLAN_FIELDS: tuple[str, ...] = (
    "plan_id",
    "optional",
    "pilot_only",
    "research_diagnostics_only",
    "secondary_to_primary_trades_panel",
    "what_to_show",
    "symbols",
    "contract_refs",
    "start_date",
    "end_date",
    "max_symbols",
    "max_contracts",
    "max_date_window_days",
    "max_chunk_count",
    "planned_chunk_count",
    "max_local_storage_bytes",
    "estimated_local_storage_bytes",
    "pacing_policy_id",
    "request_spec_contract",
    "manifest_contract",
    "resume_ledger_contract",
    "provider_error_contract",
    "quality_report_contract",
    "coverage_report_contract",
    "merge_into_primary_trades_panel",
    "implies_pull_authorization",
    "external_provider_call",
    "real_data_pull",
    "storage_scope",
)

REQUIRED_SPREAD_PROXY_INPUT_FIELDS: tuple[str, ...] = (
    "observation_id",
    "instrument_id",
    "contract_ref",
    "bar_start_ts",
    "bid",
    "ask",
    "source_request_id",
    "pilot_plan_id",
)

BID_ASK_PILOT_PLAN_ID = "bap_bid_ask_spread_proxy_pilot_v1"
BID_ASK_PILOT_WHAT_TO_SHOW = "BID_ASK"
BID_ASK_PRIMARY_TRADES_PANEL_REFERENCE = (
    "DATA-P10 mini primary common TRADES panel ES/NQ/RTY 2018-01-01 to present"
)
BID_ASK_PACING_POLICY_ID = "rpp_ibkr_historical_conservative_tobeverified_v1"
BID_ASK_STORAGE_SCOPE = "local_only_under_alpha_data_root_never_repo_data"

HISTORICAL_REQUEST_SPEC_CONTRACT = "HistoricalRequestSpec"
HISTORICAL_REQUEST_MANIFEST_CONTRACT = "HistoricalRequestManifest"
HISTORICAL_PULL_LEDGER_CONTRACT = "HistoricalPullLedger"
PROVIDER_ERROR_RECORD_CONTRACT = "ProviderErrorRecord"
DATA_QUALITY_REPORT_CONTRACT = "DataQualityReport"
COVERAGE_REPORT_CONTRACT = "CoverageReport"

BID_ASK_PILOT_ALLOWED_SYMBOLS: tuple[str, ...] = ("ES", "NQ", "RTY")
BID_ASK_PILOT_DEFAULT_SYMBOLS: tuple[str, ...] = ("ES",)
BID_ASK_PILOT_DEFAULT_CONTRACT_REFS: tuple[str, ...] = ("fcr_synthetic_es_h5",)
BID_ASK_PILOT_DEFAULT_START_DATE = "2025-01-02"
BID_ASK_PILOT_DEFAULT_END_DATE = "2025-01-03"
BID_ASK_PILOT_DEFAULT_MAX_SYMBOLS = 1
BID_ASK_PILOT_DEFAULT_MAX_CONTRACTS = 1
BID_ASK_PILOT_DEFAULT_MAX_DATE_WINDOW_DAYS = 3
BID_ASK_PILOT_DEFAULT_MAX_CHUNK_COUNT = 4
BID_ASK_PILOT_DEFAULT_PLANNED_CHUNK_COUNT = 2
BID_ASK_PILOT_DEFAULT_MAX_LOCAL_STORAGE_BYTES = 5 * 1024 * 1024
BID_ASK_PILOT_DEFAULT_ESTIMATED_LOCAL_STORAGE_BYTES = 128 * 1024

BID_ASK_PILOT_HARD_MAX_SYMBOLS = 2
BID_ASK_PILOT_HARD_MAX_CONTRACTS = 4
BID_ASK_PILOT_HARD_MAX_DATE_WINDOW_DAYS = 10
BID_ASK_PILOT_HARD_MAX_CHUNK_COUNT = 24
BID_ASK_PILOT_HARD_MAX_LOCAL_STORAGE_BYTES = 25 * 1024 * 1024


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    if "\n" in normalized or "\r" in normalized:
        msg = f"{field_name} must be a single-line string"
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


def _require_positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a positive integer"
        raise DataFoundationValidationError(msg)
    if value <= 0:
        msg = f"{field_name} must be positive"
        raise DataFoundationValidationError(msg)
    return value


def _parse_date(value: object, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = _require_text(value, field_name)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        msg = f"{field_name} must be an ISO date"
        raise DataFoundationValidationError(msg) from exc


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, field_name)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def _normalize_symbol(value: object, field_name: str = "symbols") -> str:
    symbol = _require_text(value, field_name).upper()
    if symbol not in BID_ASK_PILOT_ALLOWED_SYMBOLS:
        allowed = ", ".join(BID_ASK_PILOT_ALLOWED_SYMBOLS)
        msg = f"{field_name} must use primary mini roots only: {allowed}"
        raise DataFoundationValidationError(msg)
    return symbol


def _normalize_symbols(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "symbols must be a non-empty iterable of primary mini roots"
        raise DataFoundationValidationError(msg)
    symbols = tuple(_normalize_symbol(item) for item in value)
    if not symbols:
        msg = "symbols must not be empty"
        raise DataFoundationValidationError(msg)
    duplicates = sorted({symbol for symbol in symbols if symbols.count(symbol) > 1})
    if duplicates:
        msg = "symbols contains duplicates: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    return symbols


def _normalize_contract_refs(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "contract_refs must be a non-empty iterable of contract references"
        raise DataFoundationValidationError(msg)
    contract_refs = tuple(_require_text(item, "contract_refs") for item in value)
    if not contract_refs:
        msg = "contract_refs must not be empty"
        raise DataFoundationValidationError(msg)
    duplicates = sorted(
        {contract_ref for contract_ref in contract_refs if contract_refs.count(contract_ref) > 1}
    )
    if duplicates:
        msg = "contract_refs contains duplicates: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    return contract_refs


def _parse_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be a finite decimal price"
        raise DataFoundationValidationError(msg)
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be a finite decimal price"
        raise DataFoundationValidationError(msg) from exc
    if not parsed.is_finite():
        msg = f"{field_name} must be a finite decimal price"
        raise DataFoundationValidationError(msg)
    return parsed


def _require_positive_decimal(value: object, field_name: str) -> Decimal:
    parsed = _parse_decimal(value, field_name)
    if parsed <= 0:
        msg = f"{field_name} must be positive"
        raise DataFoundationValidationError(msg)
    return parsed


def _coerce_manifest(
    manifest: HistoricalRequestManifest | Mapping[str, object] | None,
) -> HistoricalRequestManifest:
    return require_validated_manifest_for_provider_pull(manifest)


def _coerce_ledger(
    pull_ledger: HistoricalPullLedger | Mapping[str, object] | None,
) -> HistoricalPullLedger:
    if pull_ledger is None:
        msg = "missing HistoricalPullLedger blocks BID_ASK pilot provider-pull preflight"
        raise DataFoundationValidationError(msg)
    if isinstance(pull_ledger, HistoricalPullLedger):
        return pull_ledger
    if isinstance(pull_ledger, Mapping):
        return HistoricalPullLedger.from_mapping(pull_ledger)
    msg = "HistoricalPullLedger is required for BID_ASK pilot provider-pull preflight"
    raise DataFoundationValidationError(msg)


def _coerce_quality_report(
    quality_report: DataQualityReport | Mapping[str, object] | None,
) -> DataQualityReport:
    if quality_report is None:
        msg = "missing DataQualityReport blocks BID_ASK pilot quality linkage"
        raise DataFoundationValidationError(msg)
    if isinstance(quality_report, DataQualityReport):
        return quality_report
    if isinstance(quality_report, Mapping):
        return DataQualityReport.from_mapping(quality_report)
    msg = "DataQualityReport is required for BID_ASK pilot quality linkage"
    raise DataFoundationValidationError(msg)


def _coerce_coverage_report(
    coverage_report: CoverageReport | Mapping[str, object] | None,
) -> CoverageReport:
    if coverage_report is None:
        msg = "missing CoverageReport blocks BID_ASK pilot coverage linkage"
        raise DataFoundationValidationError(msg)
    if isinstance(coverage_report, CoverageReport):
        return coverage_report
    if isinstance(coverage_report, Mapping):
        return CoverageReport.from_mapping(coverage_report)
    msg = "CoverageReport is required for BID_ASK pilot coverage linkage"
    raise DataFoundationValidationError(msg)


@dataclass(frozen=True, slots=True)
class BidAskPilotPlan:
    """Declarative optional BID_ASK pilot plan with fail-closed bounds."""

    plan_id: str
    optional: bool
    pilot_only: bool
    research_diagnostics_only: bool
    secondary_to_primary_trades_panel: bool
    what_to_show: str
    symbols: tuple[str, ...]
    contract_refs: tuple[str, ...]
    start_date: date
    end_date: date
    max_symbols: int
    max_contracts: int
    max_date_window_days: int
    max_chunk_count: int
    planned_chunk_count: int
    max_local_storage_bytes: int
    estimated_local_storage_bytes: int
    pacing_policy_id: str
    request_spec_contract: str
    manifest_contract: str
    resume_ledger_contract: str
    provider_error_contract: str
    quality_report_contract: str
    coverage_report_contract: str
    merge_into_primary_trades_panel: bool
    implies_pull_authorization: bool
    external_provider_call: bool
    real_data_pull: bool
    storage_scope: str

    def __post_init__(self) -> None:
        plan_id = _normalize_id(self.plan_id, "plan_id")
        optional = _require_bool(self.optional, "optional")
        pilot_only = _require_bool(self.pilot_only, "pilot_only")
        research_diagnostics_only = _require_bool(
            self.research_diagnostics_only,
            "research_diagnostics_only",
        )
        secondary_to_primary = _require_bool(
            self.secondary_to_primary_trades_panel,
            "secondary_to_primary_trades_panel",
        )
        what_to_show = _require_text(self.what_to_show, "what_to_show").upper()
        symbols = _normalize_symbols(self.symbols)
        contract_refs = _normalize_contract_refs(self.contract_refs)
        start_date = _parse_date(self.start_date, "start_date")
        end_date = _parse_date(self.end_date, "end_date")
        max_symbols = _require_positive_int(self.max_symbols, "max_symbols")
        max_contracts = _require_positive_int(self.max_contracts, "max_contracts")
        max_date_window_days = _require_positive_int(
            self.max_date_window_days,
            "max_date_window_days",
        )
        max_chunk_count = _require_positive_int(self.max_chunk_count, "max_chunk_count")
        planned_chunk_count = _require_positive_int(
            self.planned_chunk_count,
            "planned_chunk_count",
        )
        max_local_storage_bytes = _require_positive_int(
            self.max_local_storage_bytes,
            "max_local_storage_bytes",
        )
        estimated_local_storage_bytes = _require_positive_int(
            self.estimated_local_storage_bytes,
            "estimated_local_storage_bytes",
        )
        pacing_policy_id = _normalize_id(self.pacing_policy_id, "pacing_policy_id")
        request_spec_contract = _require_text(
            self.request_spec_contract,
            "request_spec_contract",
        )
        manifest_contract = _require_text(self.manifest_contract, "manifest_contract")
        resume_ledger_contract = _require_text(
            self.resume_ledger_contract,
            "resume_ledger_contract",
        )
        provider_error_contract = _require_text(
            self.provider_error_contract,
            "provider_error_contract",
        )
        quality_report_contract = _require_text(
            self.quality_report_contract,
            "quality_report_contract",
        )
        coverage_report_contract = _require_text(
            self.coverage_report_contract,
            "coverage_report_contract",
        )
        merge_into_primary = _require_bool(
            self.merge_into_primary_trades_panel,
            "merge_into_primary_trades_panel",
        )
        implies_pull_authorization = _require_bool(
            self.implies_pull_authorization,
            "implies_pull_authorization",
        )
        external_provider_call = _require_bool(
            self.external_provider_call,
            "external_provider_call",
        )
        real_data_pull = _require_bool(self.real_data_pull, "real_data_pull")
        storage_scope = _require_text(self.storage_scope, "storage_scope")

        if not optional:
            msg = "BID_ASK pilot plan must be optional"
            raise DataFoundationValidationError(msg)
        if not pilot_only or not research_diagnostics_only:
            msg = "BID_ASK pilot plan must be pilot-only and research-diagnostics-only"
            raise DataFoundationValidationError(msg)
        if not secondary_to_primary:
            msg = "BID_ASK pilot plan must be secondary to the primary TRADES panel"
            raise DataFoundationValidationError(msg)
        if what_to_show != BID_ASK_PILOT_WHAT_TO_SHOW:
            msg = "BID_ASK pilot plan what_to_show must be BID_ASK"
            raise DataFoundationValidationError(msg)
        if end_date < start_date:
            msg = "end_date must not be earlier than start_date"
            raise DataFoundationValidationError(msg)

        date_window_days = (end_date - start_date).days + 1
        if len(symbols) > max_symbols:
            msg = "symbols exceed max_symbols cap"
            raise DataFoundationValidationError(msg)
        if len(contract_refs) > max_contracts:
            msg = "contract_refs exceed max_contracts cap"
            raise DataFoundationValidationError(msg)
        if date_window_days > max_date_window_days:
            msg = "date window exceeds max_date_window_days cap"
            raise DataFoundationValidationError(msg)
        if planned_chunk_count > max_chunk_count:
            msg = "planned_chunk_count exceeds max_chunk_count cap"
            raise DataFoundationValidationError(msg)
        if estimated_local_storage_bytes > max_local_storage_bytes:
            msg = "estimated_local_storage_bytes exceeds max_local_storage_bytes cap"
            raise DataFoundationValidationError(msg)

        if max_symbols > BID_ASK_PILOT_HARD_MAX_SYMBOLS:
            msg = "max_symbols must not exceed the BID_ASK pilot hard cap"
            raise DataFoundationValidationError(msg)
        if max_contracts > BID_ASK_PILOT_HARD_MAX_CONTRACTS:
            msg = "max_contracts must not exceed the BID_ASK pilot hard cap"
            raise DataFoundationValidationError(msg)
        if max_date_window_days > BID_ASK_PILOT_HARD_MAX_DATE_WINDOW_DAYS:
            msg = "max_date_window_days must not exceed the BID_ASK pilot hard cap"
            raise DataFoundationValidationError(msg)
        if max_chunk_count > BID_ASK_PILOT_HARD_MAX_CHUNK_COUNT:
            msg = "max_chunk_count must not exceed the BID_ASK pilot hard cap"
            raise DataFoundationValidationError(msg)
        if max_local_storage_bytes > BID_ASK_PILOT_HARD_MAX_LOCAL_STORAGE_BYTES:
            msg = "max_local_storage_bytes must not exceed the BID_ASK pilot hard cap"
            raise DataFoundationValidationError(msg)

        if pacing_policy_id != BID_ASK_PACING_POLICY_ID:
            msg = "pacing_policy_id must reference the DATA-P08 RequestPacingPolicy"
            raise DataFoundationValidationError(msg)
        expected_contracts = {
            "request_spec_contract": HISTORICAL_REQUEST_SPEC_CONTRACT,
            "manifest_contract": HISTORICAL_REQUEST_MANIFEST_CONTRACT,
            "resume_ledger_contract": HISTORICAL_PULL_LEDGER_CONTRACT,
            "provider_error_contract": PROVIDER_ERROR_RECORD_CONTRACT,
            "quality_report_contract": DATA_QUALITY_REPORT_CONTRACT,
            "coverage_report_contract": COVERAGE_REPORT_CONTRACT,
        }
        observed_contracts = {
            "request_spec_contract": request_spec_contract,
            "manifest_contract": manifest_contract,
            "resume_ledger_contract": resume_ledger_contract,
            "provider_error_contract": provider_error_contract,
            "quality_report_contract": quality_report_contract,
            "coverage_report_contract": coverage_report_contract,
        }
        for field_name, expected in expected_contracts.items():
            if observed_contracts[field_name] != expected:
                msg = f"{field_name} must reference {expected}"
                raise DataFoundationValidationError(msg)

        if merge_into_primary:
            msg = "BID_ASK pilot must not merge into the primary TRADES panel"
            raise DataFoundationValidationError(msg)
        if implies_pull_authorization or external_provider_call or real_data_pull:
            msg = "BID_ASK pilot plan must not authorize provider calls or real data pulls"
            raise DataFoundationValidationError(msg)
        if storage_scope != BID_ASK_STORAGE_SCOPE:
            msg = "storage_scope must remain local-only and outside repo data paths"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "optional", optional)
        object.__setattr__(self, "pilot_only", pilot_only)
        object.__setattr__(self, "research_diagnostics_only", research_diagnostics_only)
        object.__setattr__(self, "secondary_to_primary_trades_panel", secondary_to_primary)
        object.__setattr__(self, "what_to_show", what_to_show)
        object.__setattr__(self, "symbols", symbols)
        object.__setattr__(self, "contract_refs", contract_refs)
        object.__setattr__(self, "start_date", start_date)
        object.__setattr__(self, "end_date", end_date)
        object.__setattr__(self, "max_symbols", max_symbols)
        object.__setattr__(self, "max_contracts", max_contracts)
        object.__setattr__(self, "max_date_window_days", max_date_window_days)
        object.__setattr__(self, "max_chunk_count", max_chunk_count)
        object.__setattr__(self, "planned_chunk_count", planned_chunk_count)
        object.__setattr__(self, "max_local_storage_bytes", max_local_storage_bytes)
        object.__setattr__(
            self,
            "estimated_local_storage_bytes",
            estimated_local_storage_bytes,
        )
        object.__setattr__(self, "pacing_policy_id", pacing_policy_id)
        object.__setattr__(self, "request_spec_contract", request_spec_contract)
        object.__setattr__(self, "manifest_contract", manifest_contract)
        object.__setattr__(self, "resume_ledger_contract", resume_ledger_contract)
        object.__setattr__(self, "provider_error_contract", provider_error_contract)
        object.__setattr__(self, "quality_report_contract", quality_report_contract)
        object.__setattr__(self, "coverage_report_contract", coverage_report_contract)
        object.__setattr__(self, "merge_into_primary_trades_panel", merge_into_primary)
        object.__setattr__(
            self,
            "implies_pull_authorization",
            implies_pull_authorization,
        )
        object.__setattr__(self, "external_provider_call", external_provider_call)
        object.__setattr__(self, "real_data_pull", real_data_pull)
        object.__setattr__(self, "storage_scope", storage_scope)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> BidAskPilotPlan:
        """Build a pilot plan from declarative config and reject loose fields."""

        missing = tuple(
            field for field in REQUIRED_BID_ASK_PILOT_PLAN_FIELDS if field not in values
        )
        if missing:
            msg = "BidAskPilotPlan missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        extra = tuple(field for field in values if field not in REQUIRED_BID_ASK_PILOT_PLAN_FIELDS)
        if extra:
            msg = "BidAskPilotPlan includes unsupported fields: " + ", ".join(extra)
            raise DataFoundationValidationError(msg)
        return cls(
            plan_id=_require_text(values["plan_id"], "plan_id"),
            optional=_require_bool(values["optional"], "optional"),
            pilot_only=_require_bool(values["pilot_only"], "pilot_only"),
            research_diagnostics_only=_require_bool(
                values["research_diagnostics_only"],
                "research_diagnostics_only",
            ),
            secondary_to_primary_trades_panel=_require_bool(
                values["secondary_to_primary_trades_panel"],
                "secondary_to_primary_trades_panel",
            ),
            what_to_show=_require_text(values["what_to_show"], "what_to_show"),
            symbols=_normalize_symbols(values["symbols"]),
            contract_refs=_normalize_contract_refs(values["contract_refs"]),
            start_date=_parse_date(values["start_date"], "start_date"),
            end_date=_parse_date(values["end_date"], "end_date"),
            max_symbols=_require_positive_int(values["max_symbols"], "max_symbols"),
            max_contracts=_require_positive_int(values["max_contracts"], "max_contracts"),
            max_date_window_days=_require_positive_int(
                values["max_date_window_days"],
                "max_date_window_days",
            ),
            max_chunk_count=_require_positive_int(
                values["max_chunk_count"],
                "max_chunk_count",
            ),
            planned_chunk_count=_require_positive_int(
                values["planned_chunk_count"],
                "planned_chunk_count",
            ),
            max_local_storage_bytes=_require_positive_int(
                values["max_local_storage_bytes"],
                "max_local_storage_bytes",
            ),
            estimated_local_storage_bytes=_require_positive_int(
                values["estimated_local_storage_bytes"],
                "estimated_local_storage_bytes",
            ),
            pacing_policy_id=_require_text(values["pacing_policy_id"], "pacing_policy_id"),
            request_spec_contract=_require_text(
                values["request_spec_contract"],
                "request_spec_contract",
            ),
            manifest_contract=_require_text(values["manifest_contract"], "manifest_contract"),
            resume_ledger_contract=_require_text(
                values["resume_ledger_contract"],
                "resume_ledger_contract",
            ),
            provider_error_contract=_require_text(
                values["provider_error_contract"],
                "provider_error_contract",
            ),
            quality_report_contract=_require_text(
                values["quality_report_contract"],
                "quality_report_contract",
            ),
            coverage_report_contract=_require_text(
                values["coverage_report_contract"],
                "coverage_report_contract",
            ),
            merge_into_primary_trades_panel=_require_bool(
                values["merge_into_primary_trades_panel"],
                "merge_into_primary_trades_panel",
            ),
            implies_pull_authorization=_require_bool(
                values["implies_pull_authorization"],
                "implies_pull_authorization",
            ),
            external_provider_call=_require_bool(
                values["external_provider_call"],
                "external_provider_call",
            ),
            real_data_pull=_require_bool(values["real_data_pull"], "real_data_pull"),
            storage_scope=_require_text(values["storage_scope"], "storage_scope"),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable plan with no provider authorization claim."""

        return MappingProxyType(
            {
                "plan_id": self.plan_id,
                "optional": self.optional,
                "pilot_only": self.pilot_only,
                "research_diagnostics_only": self.research_diagnostics_only,
                "secondary_to_primary_trades_panel": (self.secondary_to_primary_trades_panel),
                "what_to_show": self.what_to_show,
                "symbols": self.symbols,
                "contract_refs": self.contract_refs,
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
                "max_symbols": self.max_symbols,
                "max_contracts": self.max_contracts,
                "max_date_window_days": self.max_date_window_days,
                "max_chunk_count": self.max_chunk_count,
                "planned_chunk_count": self.planned_chunk_count,
                "max_local_storage_bytes": self.max_local_storage_bytes,
                "estimated_local_storage_bytes": self.estimated_local_storage_bytes,
                "pacing_policy_id": self.pacing_policy_id,
                "request_spec_contract": self.request_spec_contract,
                "manifest_contract": self.manifest_contract,
                "resume_ledger_contract": self.resume_ledger_contract,
                "provider_error_contract": self.provider_error_contract,
                "quality_report_contract": self.quality_report_contract,
                "coverage_report_contract": self.coverage_report_contract,
                "merge_into_primary_trades_panel": self.merge_into_primary_trades_panel,
                "implies_pull_authorization": self.implies_pull_authorization,
                "external_provider_call": self.external_provider_call,
                "real_data_pull": self.real_data_pull,
                "storage_scope": self.storage_scope,
            }
        )

    def validate_pacing_policy(
        self,
        pacing_policy: RequestPacingPolicy | Mapping[str, object] | None,
    ) -> RequestPacingPolicy:
        """Require DATA-P08 pacing and BID_ASK heavier accounting."""

        policy = require_pacing_policy_for_provider_pull(pacing_policy)
        if policy.pacing_policy_id != self.pacing_policy_id:
            msg = "RequestPacingPolicy id does not match the BID_ASK pilot plan"
            raise DataFoundationValidationError(msg)
        trades_weight = policy.accounting_weight("TRADES")
        bid_ask_weight = policy.accounting_weight(BID_ASK_PILOT_WHAT_TO_SHOW)
        if not policy.bid_ask_counts_double or bid_ask_weight <= trades_weight:
            msg = "BID_ASK must count heavier than TRADES through bid_ask_counts_double"
            raise DataFoundationValidationError(msg)
        return policy

    def validate_manifest_scope(
        self,
        manifest: HistoricalRequestManifest | Mapping[str, object] | None,
    ) -> HistoricalRequestManifest:
        """Require a validated BID_ASK manifest inside the pilot bounds."""

        manifest_record = _coerce_manifest(manifest)
        if manifest_record.pacing_policy_id != self.pacing_policy_id:
            msg = "manifest pacing_policy_id must match the BID_ASK pilot pacing policy"
            raise DataFoundationValidationError(msg)
        if manifest_record.chunk_count > self.max_chunk_count:
            msg = "manifest chunk_count exceeds the BID_ASK pilot cap"
            raise DataFoundationValidationError(msg)

        roots = tuple(
            dict.fromkeys(request.symbol_root for request in manifest_record.request_specs)
        )
        contract_refs = tuple(
            dict.fromkeys(request.contract_ref for request in manifest_record.request_specs)
        )
        if len(roots) > self.max_symbols:
            msg = "manifest symbols exceed the BID_ASK pilot max_symbols cap"
            raise DataFoundationValidationError(msg)
        if len(contract_refs) > self.max_contracts:
            msg = "manifest contract_refs exceed the BID_ASK pilot max_contracts cap"
            raise DataFoundationValidationError(msg)
        for request in manifest_record.request_specs:
            if request.what_to_show != BID_ASK_PILOT_WHAT_TO_SHOW:
                msg = "BID_ASK pilot manifest request_specs must use what_to_show BID_ASK"
                raise DataFoundationValidationError(msg)
            if request.symbol_root not in self.symbols:
                msg = "BID_ASK pilot manifest symbol_root is outside the plan symbols"
                raise DataFoundationValidationError(msg)
            if request.contract_ref not in self.contract_refs:
                msg = "BID_ASK pilot manifest contract_ref is outside the plan contract_refs"
                raise DataFoundationValidationError(msg)
            if request.start_ts.date() < self.start_date or request.end_ts.date() > self.end_date:
                msg = "BID_ASK pilot manifest request window is outside the plan date window"
                raise DataFoundationValidationError(msg)
        return manifest_record

    def validate_provider_pull_contracts(
        self,
        *,
        manifest: HistoricalRequestManifest | Mapping[str, object] | None,
        pacing_policy: RequestPacingPolicy | Mapping[str, object] | None,
        pull_ledger: HistoricalPullLedger | Mapping[str, object] | None,
    ) -> Mapping[str, object]:
        """Validate required contracts without authorizing or performing a pull."""

        manifest_record = self.validate_manifest_scope(manifest)
        policy = self.validate_pacing_policy(pacing_policy)
        ledger = _coerce_ledger(pull_ledger)
        if ledger.manifest_id != manifest_record.manifest_id:
            msg = "HistoricalPullLedger manifest_id must match the BID_ASK manifest"
            raise DataFoundationValidationError(msg)
        return MappingProxyType(
            {
                "plan_id": self.plan_id,
                "manifest_id": manifest_record.manifest_id,
                "pacing_policy_id": policy.pacing_policy_id,
                "pull_id": ledger.pull_id,
                "provider_pull_authorized": False,
                "external_provider_call": False,
            }
        )

    def require_quality_coverage_contract(
        self,
        *,
        quality_report: DataQualityReport | Mapping[str, object] | None,
        coverage_report: CoverageReport | Mapping[str, object] | None,
    ) -> tuple[DataQualityReport, CoverageReport]:
        """Require DATA-P16 quality and coverage linkage for pilot outputs."""

        quality = _coerce_quality_report(quality_report)
        coverage = _coerce_coverage_report(coverage_report)
        coverage.require_linked_quality_report(quality)
        return quality, coverage


@dataclass(frozen=True, slots=True)
class SpreadProxyMetric:
    """Pilot-only spread proxy computed from available BID_ASK observations."""

    observation_id: str
    instrument_id: str
    contract_ref: str
    bar_start_ts: datetime
    bid: Decimal
    ask: Decimal
    mid: Decimal
    spread: Decimal
    spread_bps: Decimal
    pilot_plan_id: str
    pilot_only: bool
    research_diagnostics_only: bool
    tradable_cost_claim: bool
    liquidity_truth_claim: bool
    feeds_canonical_trades_panel: bool

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable metric without tradability claims."""

        return MappingProxyType(
            {
                "observation_id": self.observation_id,
                "instrument_id": self.instrument_id,
                "contract_ref": self.contract_ref,
                "bar_start_ts": self.bar_start_ts.isoformat(),
                "bid": str(self.bid),
                "ask": str(self.ask),
                "mid": str(self.mid),
                "spread": str(self.spread),
                "spread_bps": str(self.spread_bps),
                "pilot_plan_id": self.pilot_plan_id,
                "pilot_only": self.pilot_only,
                "research_diagnostics_only": self.research_diagnostics_only,
                "tradable_cost_claim": self.tradable_cost_claim,
                "liquidity_truth_claim": self.liquidity_truth_claim,
                "feeds_canonical_trades_panel": self.feeds_canonical_trades_panel,
            }
        )


def _metric_from_mapping(
    values: Mapping[str, object],
    *,
    plan: BidAskPilotPlan,
) -> SpreadProxyMetric:
    missing = tuple(field for field in REQUIRED_SPREAD_PROXY_INPUT_FIELDS if field not in values)
    if missing:
        msg = "spread-proxy input missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    extra = tuple(field for field in values if field not in REQUIRED_SPREAD_PROXY_INPUT_FIELDS)
    if extra:
        msg = "spread-proxy input includes unsupported fields: " + ", ".join(extra)
        raise DataFoundationValidationError(msg)

    observation_id = _normalize_id(values["observation_id"], "observation_id")
    instrument_id = _normalize_id(values["instrument_id"], "instrument_id")
    contract_ref = _require_text(values["contract_ref"], "contract_ref")
    if contract_ref not in plan.contract_refs:
        msg = "spread-proxy input contract_ref is outside the BID_ASK pilot plan"
        raise DataFoundationValidationError(msg)
    bar_start_ts = _parse_aware_datetime(values["bar_start_ts"], "bar_start_ts")
    if bar_start_ts.date() < plan.start_date or bar_start_ts.date() > plan.end_date:
        msg = "spread-proxy input timestamp is outside the BID_ASK pilot date window"
        raise DataFoundationValidationError(msg)
    bid = _require_positive_decimal(values["bid"], "bid")
    ask = _require_positive_decimal(values["ask"], "ask")
    _normalize_id(values["source_request_id"], "source_request_id")
    pilot_plan_id = _normalize_id(values["pilot_plan_id"], "pilot_plan_id")
    if pilot_plan_id != plan.plan_id:
        msg = "spread-proxy input pilot_plan_id must match the BID_ASK pilot plan"
        raise DataFoundationValidationError(msg)
    if ask < bid:
        msg = "ask must be greater than or equal to bid for BID_ASK spread proxy"
        raise DataFoundationValidationError(msg)

    mid = (bid + ask) / Decimal("2")
    spread = ask - bid
    if spread < 0:
        msg = "spread must be non-negative"
        raise DataFoundationValidationError(msg)
    spread_bps = Decimal("0")
    if mid > 0:
        spread_bps = ((spread / mid) * Decimal("10000")).quantize(Decimal("0.000001"))
    if not spread_bps.is_finite():
        msg = "spread_bps must be finite"
        raise DataFoundationValidationError(msg)

    return SpreadProxyMetric(
        observation_id=observation_id,
        instrument_id=instrument_id,
        contract_ref=contract_ref,
        bar_start_ts=bar_start_ts,
        bid=bid,
        ask=ask,
        mid=mid,
        spread=spread,
        spread_bps=spread_bps,
        pilot_plan_id=plan.plan_id,
        pilot_only=True,
        research_diagnostics_only=True,
        tradable_cost_claim=False,
        liquidity_truth_claim=False,
        feeds_canonical_trades_panel=False,
    )


def compute_spread_proxy_metrics(
    observations: Iterable[Mapping[str, object]],
    *,
    plan: BidAskPilotPlan | None = None,
) -> tuple[SpreadProxyMetric, ...]:
    """Compute deterministic pilot-only spread proxies from synthetic BID_ASK rows."""

    active_plan = BID_ASK_PILOT_PLAN if plan is None else plan
    if isinstance(observations, str) or not isinstance(observations, Iterable):
        msg = "observations must be an iterable of spread-proxy input mappings"
        raise DataFoundationValidationError(msg)
    metrics = tuple(_metric_from_mapping(row, plan=active_plan) for row in observations)
    if not metrics:
        msg = "observations must not be empty"
        raise DataFoundationValidationError(msg)
    return metrics


BID_ASK_PILOT_PLAN = BidAskPilotPlan(
    plan_id=BID_ASK_PILOT_PLAN_ID,
    optional=True,
    pilot_only=True,
    research_diagnostics_only=True,
    secondary_to_primary_trades_panel=True,
    what_to_show=BID_ASK_PILOT_WHAT_TO_SHOW,
    symbols=BID_ASK_PILOT_DEFAULT_SYMBOLS,
    contract_refs=BID_ASK_PILOT_DEFAULT_CONTRACT_REFS,
    start_date=BID_ASK_PILOT_DEFAULT_START_DATE,
    end_date=BID_ASK_PILOT_DEFAULT_END_DATE,
    max_symbols=BID_ASK_PILOT_DEFAULT_MAX_SYMBOLS,
    max_contracts=BID_ASK_PILOT_DEFAULT_MAX_CONTRACTS,
    max_date_window_days=BID_ASK_PILOT_DEFAULT_MAX_DATE_WINDOW_DAYS,
    max_chunk_count=BID_ASK_PILOT_DEFAULT_MAX_CHUNK_COUNT,
    planned_chunk_count=BID_ASK_PILOT_DEFAULT_PLANNED_CHUNK_COUNT,
    max_local_storage_bytes=BID_ASK_PILOT_DEFAULT_MAX_LOCAL_STORAGE_BYTES,
    estimated_local_storage_bytes=BID_ASK_PILOT_DEFAULT_ESTIMATED_LOCAL_STORAGE_BYTES,
    pacing_policy_id=BID_ASK_PACING_POLICY_ID,
    request_spec_contract=HISTORICAL_REQUEST_SPEC_CONTRACT,
    manifest_contract=HISTORICAL_REQUEST_MANIFEST_CONTRACT,
    resume_ledger_contract=HISTORICAL_PULL_LEDGER_CONTRACT,
    provider_error_contract=PROVIDER_ERROR_RECORD_CONTRACT,
    quality_report_contract=DATA_QUALITY_REPORT_CONTRACT,
    coverage_report_contract=COVERAGE_REPORT_CONTRACT,
    merge_into_primary_trades_panel=False,
    implies_pull_authorization=False,
    external_provider_call=False,
    real_data_pull=False,
    storage_scope=BID_ASK_STORAGE_SCOPE,
)


__all__ = [
    "BID_ASK_PILOT_PLAN",
    "BID_ASK_PILOT_PLAN_ID",
    "BID_ASK_PILOT_WHAT_TO_SHOW",
    "BID_ASK_PRIMARY_TRADES_PANEL_REFERENCE",
    "BID_ASK_STORAGE_SCOPE",
    "COVERAGE_REPORT_CONTRACT",
    "DATA_QUALITY_REPORT_CONTRACT",
    "HISTORICAL_PULL_LEDGER_CONTRACT",
    "HISTORICAL_REQUEST_MANIFEST_CONTRACT",
    "HISTORICAL_REQUEST_SPEC_CONTRACT",
    "PROVIDER_ERROR_RECORD_CONTRACT",
    "REQUIRED_BID_ASK_PILOT_PLAN_FIELDS",
    "REQUIRED_SPREAD_PROXY_INPUT_FIELDS",
    "BidAskPilotPlan",
    "SpreadProxyMetric",
    "compute_spread_proxy_metrics",
]
