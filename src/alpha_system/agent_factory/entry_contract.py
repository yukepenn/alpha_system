"""Agent Factory entry contract and local preflight gates.

This module is a contracts-only front door. It reads declarative status flags
and checks for local registry marker files; it does not open registries, read
provider files, call external services, instantiate agents, or start runners.
"""

from __future__ import annotations

import json
import os
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[3] / "configs" / "agent_factory" / "preflight.toml"
)
DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH = "registry/features.sqlite"
DEFAULT_LABEL_REGISTRY_RELATIVE_PATH = "registry/labels.sqlite"
FORBIDDEN_MARKER_SOURCE_SUFFIXES: frozenset[str] = frozenset(
    {".dbn", ".zst", ".parquet", ".arrow", ".feather"}
)
SESSION_CONTEXT_FEATURES: frozenset[str] = frozenset(
    {"rth_flag", "eth_flag", "session_minute"}
)


class AgentFactoryPreflightStatus(StrEnum):
    """Top-level and per-gate preflight status."""

    PREFLIGHT_PASS = "PREFLIGHT_PASS"
    PREFLIGHT_WARN = "PREFLIGHT_WARN"
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"


PreflightStatus = AgentFactoryPreflightStatus


class AgentFactoryPreflightGate(StrEnum):
    """The four Agent Factory preflight gates."""

    SEED_PACKS = "SEED_PACKS"
    RUNTIME_REAL_SMOKE = "RUNTIME_REAL_SMOKE"
    PARQUET_SINK = "FEATURE_LABEL_PARQUET_SINK_V1"
    SESSION_LABEL_GUARD = "SESSION_LABEL_GUARD_FIX_V1"


PreflightGate = AgentFactoryPreflightGate


@dataclass(frozen=True, slots=True)
class GateResult:
    """Structured, value-free result for one preflight gate."""

    gate_name: AgentFactoryPreflightGate
    status: AgentFactoryPreflightStatus
    detail: str
    blocking: bool
    limitation: str | None = None
    blocked_scope: str | None = None
    required_follow_up: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible gate payload."""

        return {
            "gate_name": self.gate_name.value,
            "status": self.status.value,
            "detail": self.detail,
            "blocking": self.blocking,
            "limitation": self.limitation,
            "blocked_scope": self.blocked_scope,
            "required_follow_up": self.required_follow_up,
        }


@dataclass(frozen=True, slots=True)
class AgentFactoryPreflightResult:
    """Structured result for Agent Factory entry preflight."""

    status: AgentFactoryPreflightStatus
    gates: tuple[GateResult, ...]
    blocking_findings: tuple[GateResult, ...]
    limitations: tuple[str, ...]
    next_required_gate: AgentFactoryPreflightGate | None

    @property
    def passed(self) -> bool:
        """Return true only when every gate is satisfied."""

        return self.status is AgentFactoryPreflightStatus.PREFLIGHT_PASS

    @property
    def warned(self) -> bool:
        """Return true when at least one non-blocking gate warns."""

        return self.status is AgentFactoryPreflightStatus.PREFLIGHT_WARN

    @property
    def blocked(self) -> bool:
        """Return true when one or more gates fail closed."""

        return self.status is AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED

    def gate(self, gate_name: AgentFactoryPreflightGate) -> GateResult:
        """Return one gate result by identifier."""

        for gate_result in self.gates:
            if gate_result.gate_name is gate_name:
                return gate_result
        raise KeyError(gate_name.value)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible result payload."""

        return {
            "status": self.status.value,
            "gates": [gate.to_dict() for gate in self.gates],
            "blocking_findings": [gate.to_dict() for gate in self.blocking_findings],
            "limitations": list(self.limitations),
            "next_required_gate": (
                None if self.next_required_gate is None else self.next_required_gate.value
            ),
        }


@dataclass(frozen=True, slots=True)
class AgentFactoryPreflightConfig:
    """Injectable, deterministic source for entry preflight inputs."""

    alpha_data_root: Path | None = None
    feature_registry_relative_path: str = DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH
    label_registry_relative_path: str = DEFAULT_LABEL_REGISTRY_RELATIVE_PATH
    real_dataset_version_smoke_ran: bool | None = None
    runtime_real_smoke_status_path: Path | None = None
    runtime_real_smoke_status_source: str = "declarative config"
    parquet_sink_landed: bool = False
    parquet_sink_human_approved: bool = False
    session_label_guard_fixed: bool = False
    session_context_features_explicitly_available: bool = False
    large_scale_value_consuming_study_requested: bool = False
    session_context_features_requested: tuple[str, ...] = ()

    @classmethod
    def from_file(cls, path: str | Path = DEFAULT_CONFIG_PATH) -> AgentFactoryPreflightConfig:
        """Load preflight inputs from a TOML file."""

        config_path = Path(path)
        return cls.from_mapping(tomllib.loads(config_path.read_text(encoding="utf-8")))

    @classmethod
    def from_default_file(cls) -> AgentFactoryPreflightConfig:
        """Load the repo default config when present, otherwise return conservative defaults."""

        if DEFAULT_CONFIG_PATH.exists():
            return cls.from_file(DEFAULT_CONFIG_PATH)
        return cls()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> AgentFactoryPreflightConfig:
        """Build config from a flat or sectioned mapping."""

        return cls(
            alpha_data_root=_optional_path(_lookup(data, "registries", "alpha_data_root")),
            feature_registry_relative_path=str(
                _lookup(
                    data,
                    "registries",
                    "feature_registry_relative_path",
                    DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH,
                )
            ),
            label_registry_relative_path=str(
                _lookup(
                    data,
                    "registries",
                    "label_registry_relative_path",
                    DEFAULT_LABEL_REGISTRY_RELATIVE_PATH,
                )
            ),
            real_dataset_version_smoke_ran=_optional_bool(
                _lookup(data, "runtime_real_smoke", "real_dataset_version_smoke_ran")
            ),
            runtime_real_smoke_status_path=_optional_path(
                _lookup(data, "runtime_real_smoke", "status_path")
            ),
            runtime_real_smoke_status_source=str(
                _lookup(data, "runtime_real_smoke", "status_source", "declarative config")
            ),
            parquet_sink_landed=_bool(
                _lookup(data, "future_blockers", "parquet_sink_landed", False)
            ),
            parquet_sink_human_approved=_bool(
                _lookup(data, "future_blockers", "parquet_sink_human_approved", False)
            ),
            session_label_guard_fixed=_bool(
                _lookup(data, "future_blockers", "session_label_guard_fixed", False)
            ),
            session_context_features_explicitly_available=_bool(
                _lookup(
                    data,
                    "future_blockers",
                    "session_context_features_explicitly_available",
                    False,
                )
            ),
            large_scale_value_consuming_study_requested=_bool(
                _lookup(
                    data,
                    "request_scope",
                    "large_scale_value_consuming_study_requested",
                    False,
                )
            ),
            session_context_features_requested=_string_tuple(
                _lookup(data, "request_scope", "session_context_features_requested", ())
            ),
        )

    def with_request_scope(
        self,
        *,
        large_scale_value_consuming_study_requested: bool | None = None,
        session_context_features_requested: Sequence[str] | None = None,
    ) -> AgentFactoryPreflightConfig:
        """Return a config copy with request-specific scope flags applied."""

        updates: dict[str, object] = {}
        if large_scale_value_consuming_study_requested is not None:
            updates["large_scale_value_consuming_study_requested"] = (
                large_scale_value_consuming_study_requested
            )
        if session_context_features_requested is not None:
            updates["session_context_features_requested"] = _string_tuple(
                session_context_features_requested
            )
        return replace(self, **updates)


class AgentFactoryPreflight:
    """Evaluate the Agent Factory entry gates without touching runtime data."""

    def __init__(
        self,
        config: AgentFactoryPreflightConfig | Mapping[str, Any] | None = None,
        *,
        config_path: str | Path | None = None,
    ) -> None:
        if config is not None and config_path is not None:
            raise ValueError("pass either config or config_path, not both")
        if isinstance(config, AgentFactoryPreflightConfig):
            self.config = config
        elif config is not None:
            self.config = AgentFactoryPreflightConfig.from_mapping(config)
        elif config_path is not None:
            self.config = AgentFactoryPreflightConfig.from_file(config_path)
        else:
            self.config = AgentFactoryPreflightConfig.from_default_file()

    def evaluate(
        self,
        *,
        large_scale_value_consuming_study_requested: bool | None = None,
        session_context_features_requested: Sequence[str] | None = None,
    ) -> AgentFactoryPreflightResult:
        """Evaluate all four preflight gates."""

        config = self.config.with_request_scope(
            large_scale_value_consuming_study_requested=(
                large_scale_value_consuming_study_requested
            ),
            session_context_features_requested=session_context_features_requested,
        )
        gates = (
            self._check_seed_packs(config),
            self._check_runtime_real_smoke(config),
            self._check_parquet_sink(config),
            self._check_session_label_guard(config),
        )
        return _result_from_gates(gates)

    run = evaluate

    def _check_seed_packs(self, config: AgentFactoryPreflightConfig) -> GateResult:
        alpha_data_root = _alpha_data_root(config)
        if alpha_data_root is None:
            limitation = (
                "ALPHA_DATA_ROOT is unset; local seed FeaturePack/LabelPack registry "
                "gate degraded to PREFLIGHT_WARN."
            )
            return GateResult(
                gate_name=AgentFactoryPreflightGate.SEED_PACKS,
                status=AgentFactoryPreflightStatus.PREFLIGHT_WARN,
                detail=(
                    "Local registry marker files were not checked because no data root "
                    "was declared."
                ),
                blocking=False,
                limitation=limitation,
            )

        feature_registry = _registry_path(
            alpha_data_root,
            config.feature_registry_relative_path,
        )
        label_registry = _registry_path(
            alpha_data_root,
            config.label_registry_relative_path,
        )
        if feature_registry.exists() and label_registry.exists():
            return GateResult(
                gate_name=AgentFactoryPreflightGate.SEED_PACKS,
                status=AgentFactoryPreflightStatus.PREFLIGHT_PASS,
                detail=(
                    "FeaturePack and LabelPack registry marker files exist; registry "
                    "contents were not opened."
                ),
                blocking=False,
            )

        limitation = (
            "Local FeaturePack/LabelPack registries are absent or incomplete on this "
            "checkout; seed-pack gate degraded to PREFLIGHT_WARN."
        )
        return GateResult(
            gate_name=AgentFactoryPreflightGate.SEED_PACKS,
            status=AgentFactoryPreflightStatus.PREFLIGHT_WARN,
            detail=(
                "One or both local registry marker files are absent; no registry "
                "contents were opened."
            ),
            blocking=False,
            limitation=limitation,
        )

    def _check_runtime_real_smoke(self, config: AgentFactoryPreflightConfig) -> GateResult:
        status, limitation, parse_failed = _runtime_real_smoke_status(config)
        if status is True:
            return GateResult(
                gate_name=AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE,
                status=AgentFactoryPreflightStatus.PREFLIGHT_PASS,
                detail=(
                    "Recorded runtime real smoke status is real_dataset_version_smoke_ran=true."
                ),
                blocking=False,
            )
        if status is False:
            return GateResult(
                gate_name=AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE,
                status=AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED,
                detail=(
                    "Recorded runtime real smoke status is not satisfied; Agent Factory "
                    "entry fails closed."
                ),
                blocking=True,
                limitation=limitation,
                required_follow_up=config.runtime_real_smoke_status_source,
            )

        if parse_failed:
            return GateResult(
                gate_name=AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE,
                status=AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED,
                detail=(
                    "Runtime real smoke status source is malformed; Agent Factory entry "
                    "fails closed."
                ),
                blocking=True,
                limitation=limitation,
                required_follow_up=config.runtime_real_smoke_status_source,
            )

        limitation = limitation or (
            "Runtime real smoke status is unknown; gate degraded to PREFLIGHT_WARN."
        )
        return GateResult(
            gate_name=AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE,
            status=AgentFactoryPreflightStatus.PREFLIGHT_WARN,
            detail=(
                "No recorded runtime real smoke PASS was provided; the runtime was not re-run."
            ),
            blocking=False,
            limitation=limitation,
            required_follow_up=config.runtime_real_smoke_status_source,
        )

    def _check_parquet_sink(self, config: AgentFactoryPreflightConfig) -> GateResult:
        if config.parquet_sink_landed:
            return GateResult(
                gate_name=AgentFactoryPreflightGate.PARQUET_SINK,
                status=AgentFactoryPreflightStatus.PREFLIGHT_PASS,
                detail="FEATURE_LABEL_PARQUET_SINK_V1 is marked landed.",
                blocking=False,
            )

        blocked_scope = "large-scale value-consuming studies"
        limitation = (
            "Large-scale value-consuming studies are blocked until "
            "FEATURE_LABEL_PARQUET_SINK_V1 lands or explicit human approval is recorded."
        )
        if (
            config.large_scale_value_consuming_study_requested
            and not config.parquet_sink_human_approved
        ):
            return GateResult(
                gate_name=AgentFactoryPreflightGate.PARQUET_SINK,
                status=AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED,
                detail=(
                    "FEATURE_LABEL_PARQUET_SINK_V1 is not marked landed and a "
                    "large-scale value-consuming study was requested."
                ),
                blocking=True,
                limitation=limitation,
                blocked_scope=blocked_scope,
                required_follow_up=AgentFactoryPreflightGate.PARQUET_SINK.value,
            )

        return GateResult(
            gate_name=AgentFactoryPreflightGate.PARQUET_SINK,
            status=AgentFactoryPreflightStatus.PREFLIGHT_WARN,
            detail=(
                "FEATURE_LABEL_PARQUET_SINK_V1 is not marked landed; plain entry may "
                "continue with this scope constraint."
            ),
            blocking=False,
            limitation=limitation,
            blocked_scope=blocked_scope,
            required_follow_up=AgentFactoryPreflightGate.PARQUET_SINK.value,
        )

    def _check_session_label_guard(self, config: AgentFactoryPreflightConfig) -> GateResult:
        if config.session_label_guard_fixed:
            return GateResult(
                gate_name=AgentFactoryPreflightGate.SESSION_LABEL_GUARD,
                status=AgentFactoryPreflightStatus.PREFLIGHT_PASS,
                detail="SESSION_LABEL_GUARD_FIX_V1 is marked fixed.",
                blocking=False,
            )

        requested = tuple(
            feature
            for feature in config.session_context_features_requested
            if feature in SESSION_CONTEXT_FEATURES
        )
        blocked_scope = "session-context features: rth_flag, eth_flag, session_minute"
        limitation = (
            "Session-context features are blocked until SESSION_LABEL_GUARD_FIX_V1 is "
            "fixed or explicitly marked available."
        )
        if requested and not config.session_context_features_explicitly_available:
            return GateResult(
                gate_name=AgentFactoryPreflightGate.SESSION_LABEL_GUARD,
                status=AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED,
                detail=(
                    "SESSION_LABEL_GUARD_FIX_V1 is not fixed and a session-context "
                    "feature was requested."
                ),
                blocking=True,
                limitation=limitation,
                blocked_scope=blocked_scope,
                required_follow_up=AgentFactoryPreflightGate.SESSION_LABEL_GUARD.value,
            )

        return GateResult(
            gate_name=AgentFactoryPreflightGate.SESSION_LABEL_GUARD,
            status=AgentFactoryPreflightStatus.PREFLIGHT_WARN,
            detail=(
                "SESSION_LABEL_GUARD_FIX_V1 is not fixed; plain entry may continue "
                "with this scope constraint."
            ),
            blocking=False,
            limitation=limitation,
            blocked_scope=blocked_scope,
            required_follow_up=AgentFactoryPreflightGate.SESSION_LABEL_GUARD.value,
        )


def evaluate_agent_factory_preflight(
    config: AgentFactoryPreflightConfig | Mapping[str, Any] | None = None,
    *,
    config_path: str | Path | None = None,
    large_scale_value_consuming_study_requested: bool | None = None,
    session_context_features_requested: Sequence[str] | None = None,
) -> AgentFactoryPreflightResult:
    """Convenience function for evaluating the Agent Factory entry contract."""

    return AgentFactoryPreflight(config=config, config_path=config_path).evaluate(
        large_scale_value_consuming_study_requested=large_scale_value_consuming_study_requested,
        session_context_features_requested=session_context_features_requested,
    )


def _result_from_gates(gates: tuple[GateResult, ...]) -> AgentFactoryPreflightResult:
    blocking_findings = tuple(gate for gate in gates if gate.blocking)
    limitations = tuple(gate.limitation for gate in gates if gate.limitation)
    if blocking_findings:
        status = AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED
        next_required_gate = blocking_findings[0].gate_name
    else:
        warning_gates = tuple(
            gate for gate in gates if gate.status is AgentFactoryPreflightStatus.PREFLIGHT_WARN
        )
        if warning_gates:
            status = AgentFactoryPreflightStatus.PREFLIGHT_WARN
            next_required_gate = warning_gates[0].gate_name
        else:
            status = AgentFactoryPreflightStatus.PREFLIGHT_PASS
            next_required_gate = None
    return AgentFactoryPreflightResult(
        status=status,
        gates=gates,
        blocking_findings=blocking_findings,
        limitations=limitations,
        next_required_gate=next_required_gate,
    )


def _runtime_real_smoke_status(
    config: AgentFactoryPreflightConfig,
) -> tuple[bool | None, str | None, bool]:
    if config.real_dataset_version_smoke_ran is not None:
        return config.real_dataset_version_smoke_ran, None, False

    if config.runtime_real_smoke_status_path is None:
        return (
            None,
            "Runtime real smoke status source is not configured; gate degraded to PREFLIGHT_WARN.",
            False,
        )

    if _has_forbidden_marker_suffix(config.runtime_real_smoke_status_path):
        return (
            None,
            "Runtime real smoke status source uses a forbidden raw/heavy file suffix; "
            "the path was not read.",
            True,
        )

    try:
        text = config.runtime_real_smoke_status_path.read_text(encoding="utf-8")
    except OSError:
        return (
            None,
            "Runtime real smoke status source is absent or unreadable; gate degraded to "
            "PREFLIGHT_WARN.",
            False,
        )

    try:
        return _parse_smoke_status(text), None, False
    except ValueError:
        return (
            None,
            "Runtime real smoke status source could not be parsed.",
            True,
        )


def _parse_smoke_status(text: str) -> bool:
    stripped = text.strip()
    lowered = stripped.lower()
    if lowered in {"true", "1", "yes", "pass", "passed"}:
        return True
    if lowered in {"false", "0", "no", "fail", "failed"}:
        return False

    if stripped.startswith("{"):
        payload = json.loads(stripped)
    else:
        payload = tomllib.loads(stripped)

    if not isinstance(payload, Mapping) or "real_dataset_version_smoke_ran" not in payload:
        raise ValueError("missing real_dataset_version_smoke_ran")
    return _bool(payload["real_dataset_version_smoke_ran"])


def _alpha_data_root(config: AgentFactoryPreflightConfig) -> Path | None:
    if config.alpha_data_root is not None:
        return config.alpha_data_root
    env_value = os.environ.get("ALPHA_DATA_ROOT")
    if not env_value:
        return None
    return Path(os.path.expanduser(os.path.expandvars(env_value)))


def _registry_path(alpha_data_root: Path, configured_path: str) -> Path:
    path = Path(os.path.expanduser(os.path.expandvars(configured_path)))
    if path.is_absolute():
        return path
    return alpha_data_root / path


def _has_forbidden_marker_suffix(path: Path) -> bool:
    return any(suffix.lower() in FORBIDDEN_MARKER_SOURCE_SUFFIXES for suffix in path.suffixes)


def _lookup(
    data: Mapping[str, Any],
    section: str,
    key: str,
    default: object = None,
) -> object:
    section_value = data.get(section)
    if isinstance(section_value, Mapping) and key in section_value:
        return section_value[key]
    return data.get(key, default)


def _optional_path(value: object) -> Path | None:
    if value is None or value == "":
        return None
    return Path(os.path.expanduser(os.path.expandvars(str(value))))


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return _bool(value)


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "pass", "passed"}:
            return True
        if lowered in {"false", "0", "no", "n", "fail", "failed"}:
            return False
    raise ValueError(f"expected boolean-compatible value, got {value!r}")


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value)
    raise ValueError(f"expected sequence of strings, got {value!r}")
