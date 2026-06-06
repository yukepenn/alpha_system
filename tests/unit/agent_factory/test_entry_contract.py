from __future__ import annotations

import importlib

from alpha_system.agent_factory.entry_contract import (
    AgentFactoryPreflight,
    AgentFactoryPreflightConfig,
    AgentFactoryPreflightGate,
    AgentFactoryPreflightStatus,
    SESSION_CONTEXT_FEATURES,
)


def test_agent_factory_modules_import() -> None:
    assert importlib.import_module("alpha_system.agent_factory") is not None
    assert importlib.import_module("alpha_system.agent_factory.entry_contract") is not None


def test_all_four_gates_are_represented(tmp_path) -> None:
    config = _satisfied_config(tmp_path)

    result = AgentFactoryPreflight(config).evaluate()

    assert {gate.gate_name for gate in result.gates} == {
        AgentFactoryPreflightGate.SEED_PACKS,
        AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE,
        AgentFactoryPreflightGate.PARQUET_SINK,
        AgentFactoryPreflightGate.SESSION_LABEL_GUARD,
    }
    assert len(result.gates) == 4


def test_explicitly_unsatisfied_runtime_smoke_fails_closed(tmp_path) -> None:
    config = _satisfied_config(tmp_path, real_dataset_version_smoke_ran=False)

    result = AgentFactoryPreflight(config).evaluate()

    assert result.status is AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED
    assert result.blocked
    assert result.next_required_gate is AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE
    assert [gate.gate_name for gate in result.blocking_findings] == [
        AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE
    ]


def test_absent_local_registries_degrade_to_warning(tmp_path, monkeypatch) -> None:
    missing_root = tmp_path / "missing_alpha_data_root"
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(missing_root))
    config = AgentFactoryPreflightConfig(
        real_dataset_version_smoke_ran=True,
        parquet_sink_landed=True,
        session_label_guard_fixed=True,
    )

    result = AgentFactoryPreflight(config).evaluate()

    assert result.status is AgentFactoryPreflightStatus.PREFLIGHT_WARN
    assert result.warned
    seed_gate = result.gate(AgentFactoryPreflightGate.SEED_PACKS)
    assert seed_gate.status is AgentFactoryPreflightStatus.PREFLIGHT_WARN
    assert not seed_gate.blocking
    assert any("degraded to PREFLIGHT_WARN" in limitation for limitation in result.limitations)


def test_all_satisfied_synthetic_config_passes(tmp_path) -> None:
    result = AgentFactoryPreflight(_satisfied_config(tmp_path)).evaluate()

    assert result.status is AgentFactoryPreflightStatus.PREFLIGHT_PASS
    assert result.passed
    assert result.blocking_findings == ()
    assert result.limitations == ()
    assert result.next_required_gate is None


def test_result_is_structured_and_value_free(tmp_path) -> None:
    config = _satisfied_config(tmp_path)

    result = AgentFactoryPreflight(config).evaluate()
    payload = result.to_dict()
    payload_text = repr(payload)

    assert set(payload) == {
        "status",
        "gates",
        "blocking_findings",
        "limitations",
        "next_required_gate",
    }
    assert isinstance(payload["gates"], list)
    assert "raw_payload" not in payload_text
    assert "provider_payload" not in payload_text
    assert "db_rows" not in payload_text
    assert str(tmp_path) not in payload_text


def test_parquet_sink_blocks_large_scale_value_consuming_scope(tmp_path) -> None:
    config = _satisfied_config(
        tmp_path,
        parquet_sink_landed=False,
        large_scale_value_consuming_study_requested=True,
    )

    result = AgentFactoryPreflight(config).evaluate()

    parquet_gate = result.gate(AgentFactoryPreflightGate.PARQUET_SINK)
    assert result.status is AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED
    assert parquet_gate.blocking
    assert parquet_gate.blocked_scope == "large-scale value-consuming studies"
    assert parquet_gate.gate_name in {gate.gate_name for gate in result.blocking_findings}


def test_session_label_guard_blocks_session_context_features(tmp_path) -> None:
    config = _satisfied_config(
        tmp_path,
        session_label_guard_fixed=False,
        session_context_features_requested=("rth_flag",),
    )

    result = AgentFactoryPreflight(config).evaluate()

    session_gate = result.gate(AgentFactoryPreflightGate.SESSION_LABEL_GUARD)
    assert result.status is AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED
    assert session_gate.blocking
    assert "session-context features" in (session_gate.blocked_scope or "")
    assert {"rth_flag", "eth_flag", "session_minute"} == set(SESSION_CONTEXT_FEATURES)


def test_runtime_marker_source_with_raw_heavy_suffix_fails_closed_without_reading(
    tmp_path,
) -> None:
    config = _satisfied_config(
        tmp_path,
        real_dataset_version_smoke_ran=None,
        runtime_real_smoke_status_path=tmp_path / "status.parquet",
    )

    result = AgentFactoryPreflight(config).evaluate()

    runtime_gate = result.gate(AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE)
    assert result.status is AgentFactoryPreflightStatus.PREFLIGHT_BLOCKED
    assert runtime_gate.blocking
    assert runtime_gate.limitation is not None
    assert "path was not read" in runtime_gate.limitation


def test_default_config_file_loads_without_real_registries(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(tmp_path / "clean_checkout"))

    result = AgentFactoryPreflight().evaluate()

    assert result.status is AgentFactoryPreflightStatus.PREFLIGHT_WARN
    assert result.gate(AgentFactoryPreflightGate.RUNTIME_REAL_SMOKE).status is (
        AgentFactoryPreflightStatus.PREFLIGHT_PASS
    )


def _satisfied_config(
    tmp_path,
    *,
    real_dataset_version_smoke_ran: bool | None = True,
    runtime_real_smoke_status_path=None,
    parquet_sink_landed: bool = True,
    session_label_guard_fixed: bool = True,
    large_scale_value_consuming_study_requested: bool = False,
    session_context_features_requested: tuple[str, ...] = (),
) -> AgentFactoryPreflightConfig:
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "features.sqlite").touch()
    (registry / "labels.sqlite").touch()
    return AgentFactoryPreflightConfig(
        alpha_data_root=tmp_path,
        real_dataset_version_smoke_ran=real_dataset_version_smoke_ran,
        runtime_real_smoke_status_path=runtime_real_smoke_status_path,
        parquet_sink_landed=parquet_sink_landed,
        session_label_guard_fixed=session_label_guard_fixed,
        large_scale_value_consuming_study_requested=(
            large_scale_value_consuming_study_requested
        ),
        session_context_features_requested=session_context_features_requested,
    )
