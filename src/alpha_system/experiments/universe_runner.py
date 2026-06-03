"""Deterministic tiny-fixture universe runner."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.fixture_policy import FixturePolicyError, assert_registry_path_allowed
from alpha_system.data.sessions import expected_bar_starts
from alpha_system.data.universe import MISSING_DATA_FLAG, UniverseSpec
from alpha_system.experiments.registry import RunRecord, insert_run_record


UNIVERSE_RUNNER_ENGINE_VERSION = "universe_fixture_runner_v1"
UNIVERSE_RUN_TABLE = "study_runs"
FORBIDDEN_REPO_OUTPUT_ROOTS: tuple[str, ...] = ("runs", "metadata", "data", "artifacts")
ONE_MINUTE = timedelta(minutes=1)


class UniverseRunnerError(ValueError):
    """Raised when a universe fixture run cannot be assembled safely."""


@dataclass(frozen=True, slots=True, kw_only=True)
class AlignedUniverseSession:
    """Session alignment record for one instrument and local trading date."""

    instrument_id: str
    trading_date: date
    calendar_id: str
    session_id: str
    open_ts: datetime
    close_ts: datetime
    timezone: str
    expected_bar_count: int

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseRunnerSpec:
    """Validated inputs for a tiny deterministic multi-symbol fixture run."""

    run_id: str
    universe: UniverseSpec
    calendars: Mapping[str, TradingCalendar]
    trading_dates: tuple[date, ...]
    bars: tuple[Mapping[str, Any], ...] = ()
    registry_path: str | None = None
    output_dir: str | None = None
    factor_versions: Mapping[str, str] = None
    label_versions: Mapping[str, str] = None
    engine_version: str = UNIVERSE_RUNNER_ENGINE_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _text(self.run_id, "run_id"))
        if not isinstance(self.universe, UniverseSpec):
            raise UniverseRunnerError("universe runner requires a UniverseSpec")
        object.__setattr__(self, "calendars", dict(self.calendars))
        if not self.calendars:
            raise UniverseRunnerError("universe runner requires calendars by instrument_id")
        object.__setattr__(
            self,
            "trading_dates",
            tuple(sorted(_date_value(item, "trading_date") for item in self.trading_dates)),
        )
        if not self.trading_dates:
            raise UniverseRunnerError("universe runner requires at least one trading_date")
        object.__setattr__(self, "bars", tuple(dict(row) for row in self.bars))
        object.__setattr__(self, "factor_versions", dict(self.factor_versions or {}))
        object.__setattr__(self, "label_versions", dict(self.label_versions or {}))
        object.__setattr__(self, "engine_version", _text(self.engine_version, "engine_version"))

    def config_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "universe": self.universe.hash_input(),
            "calendar_ids": {
                instrument_id: calendar.calendar_id
                for instrument_id, calendar in sorted(self.calendars.items())
            },
            "trading_dates": [item.isoformat() for item in self.trading_dates],
            "factor_versions": dict(sorted(self.factor_versions.items())),
            "label_versions": dict(sorted(self.label_versions.items())),
            "engine_version": self.engine_version,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseRunResult:
    """Summary of one deterministic universe fixture run."""

    run_id: str
    universe_id: str
    universe_hash: str
    config_hash: str
    output_dir: str
    manifest_path: str
    missing_data_flags_path: str
    aligned_sessions: tuple[AlignedUniverseSession, ...]
    missing_data_flags: Mapping[str, tuple[str, ...]]
    registry_path: str | None
    registry_written: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "universe_id": self.universe_id,
            "universe_hash": self.universe_hash,
            "config_hash": self.config_hash,
            "output_dir": self.output_dir,
            "manifest_path": self.manifest_path,
            "missing_data_flags_path": self.missing_data_flags_path,
            "aligned_sessions": [session.to_dict() for session in self.aligned_sessions],
            "missing_data_flags": {
                instrument_id: list(flags)
                for instrument_id, flags in sorted(self.missing_data_flags.items())
            },
            "registry_path": self.registry_path,
            "registry_written": self.registry_written,
        }


def run_universe_fixture(
    spec: UniverseRunnerSpec,
    *,
    repo_root: str | Path | None = None,
) -> UniverseRunResult:
    """Run a bounded fixture-only universe alignment pass."""
    root = Path(repo_root).resolve(strict=False) if repo_root is not None else Path.cwd().resolve(strict=False)
    universe_hash = spec.universe.config_hash()
    config_hash = hash_config(spec.config_payload())
    aligned_sessions = align_universe_sessions(spec.universe, spec.calendars, spec.trading_dates)
    missing_flags = per_symbol_missing_data_flags(spec.bars, aligned_sessions)

    output_dir = resolve_universe_output_dir(spec.output_dir, run_id=spec.run_id, repo_root=root)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    missing_flags_path = output_dir / "missing_data_flags.json"
    manifest = {
        "run_id": spec.run_id,
        "engine_version": spec.engine_version,
        "universe_id": spec.universe.universe_id,
        "universe_hash": universe_hash,
        "config_hash": config_hash,
        "data_version": spec.universe.data_version,
        "aligned_sessions": [session.to_dict() for session in aligned_sessions],
        "missing_data_flags": {
            instrument_id: list(flags)
            for instrument_id, flags in sorted(missing_flags.items())
        },
        "status_message": "Tiny deterministic universe fixture only; no trading or alpha claim.",
    }
    manifest_path.write_text(_json_text(manifest), encoding="utf-8")
    missing_flags_path.write_text(_json_text(manifest["missing_data_flags"]), encoding="utf-8")

    registry_written = False
    registry_path = None
    if spec.registry_path:
        registry_path = _record_universe_run(
            spec,
            registry_path=spec.registry_path,
            universe_hash=universe_hash,
            config_hash=config_hash,
            artifact_paths={
                "manifest_path": manifest_path.as_posix(),
                "missing_data_flags_path": missing_flags_path.as_posix(),
            },
            aligned_sessions=aligned_sessions,
            missing_data_flags=missing_flags,
            repo_root=root,
        )
        registry_written = True

    return UniverseRunResult(
        run_id=spec.run_id,
        universe_id=spec.universe.universe_id,
        universe_hash=universe_hash,
        config_hash=config_hash,
        output_dir=output_dir.as_posix(),
        manifest_path=manifest_path.as_posix(),
        missing_data_flags_path=missing_flags_path.as_posix(),
        aligned_sessions=aligned_sessions,
        missing_data_flags=missing_flags,
        registry_path=registry_path,
        registry_written=registry_written,
    )


def align_universe_sessions(
    universe: UniverseSpec,
    calendars: Mapping[str, TradingCalendar],
    trading_dates: Sequence[date | str],
) -> tuple[AlignedUniverseSession, ...]:
    """Align independent instrument calendars without assuming one timezone."""
    sessions: list[AlignedUniverseSession] = []
    for trading_date in sorted(_date_value(item, "trading_date") for item in trading_dates):
        for member in universe.active_members(trading_date):
            calendar = calendars.get(member.instrument_id)
            if calendar is None:
                raise UniverseRunnerError(f"missing calendar for instrument_id {member.instrument_id}")
            if calendar.timezone != member.timezone:
                raise UniverseRunnerError(
                    f"calendar timezone {calendar.timezone!r} does not match "
                    f"member timezone {member.timezone!r} for {member.instrument_id}"
                )
            session = calendar.trading_session_for_date(trading_date)
            if session is None:
                continue
            sessions.append(
                AlignedUniverseSession(
                    instrument_id=member.instrument_id,
                    trading_date=trading_date,
                    calendar_id=session.calendar_id,
                    session_id=session.session_id,
                    open_ts=session.open_ts,
                    close_ts=session.close_ts,
                    timezone=session.timezone,
                    expected_bar_count=len(expected_bar_starts(session)),
                )
            )
    return tuple(sorted(sessions, key=lambda item: (item.trading_date, item.instrument_id)))


def per_symbol_missing_data_flags(
    bars: Sequence[Mapping[str, Any]],
    aligned_sessions: Sequence[AlignedUniverseSession],
) -> dict[str, tuple[str, ...]]:
    """Return deterministic missing-data flags per active instrument."""
    bars_by_key: set[tuple[str, datetime]] = set()
    for row_number, row in enumerate(bars):
        instrument_id = _text(row.get("instrument_id"), f"bar {row_number} instrument_id")
        bar_start_ts = _datetime_value(row.get("bar_start_ts"), f"bar {row_number} bar_start_ts")
        bars_by_key.add((instrument_id, bar_start_ts))

    flags: dict[str, list[str]] = {}
    for session in aligned_sessions:
        expected_starts = _expected_starts_for_aligned_session(session)
        for bar_start_ts in expected_starts:
            if (session.instrument_id, bar_start_ts) not in bars_by_key:
                flags.setdefault(session.instrument_id, []).append(MISSING_DATA_FLAG)
                break
    return {
        instrument_id: tuple(dict.fromkeys(items))
        for instrument_id, items in sorted(flags.items())
    }


def resolve_universe_output_dir(
    output_dir: str | Path | None,
    *,
    run_id: str,
    repo_root: str | Path | None = None,
) -> Path:
    """Resolve a temp/local output directory and reject repository artifact roots."""
    if output_dir is None:
        return Path(tempfile.gettempdir()) / "alpha_system_universe_runs" / run_id
    candidate = Path(output_dir).expanduser().resolve(strict=False)
    root = Path(repo_root).expanduser().resolve(strict=False) if repo_root is not None else Path.cwd().resolve(strict=False)
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return candidate
    if candidate == root:
        raise UniverseRunnerError("universe runner outputs must use a temp/local path outside the repo")
    first = relative.parts[0] if relative.parts else ""
    if first in FORBIDDEN_REPO_OUTPUT_ROOTS or first:
        raise UniverseRunnerError("universe runner outputs must use a temp/local path outside the repo")
    return candidate


def _record_universe_run(
    spec: UniverseRunnerSpec,
    *,
    registry_path: str | Path,
    universe_hash: str,
    config_hash: str,
    artifact_paths: Mapping[str, str],
    aligned_sessions: Sequence[AlignedUniverseSession],
    missing_data_flags: Mapping[str, tuple[str, ...]],
    repo_root: Path,
) -> str:
    try:
        resolved_registry_path = assert_registry_path_allowed(registry_path, repo_root=repo_root)
    except FixturePolicyError as exc:
        raise UniverseRunnerError(str(exc)) from exc
    status = init_registry(resolved_registry_path)
    if not status.valid:
        raise UniverseRunnerError(f"registry is not valid: {status.status_message}")
    git_info = capture_git_info(repo_root)
    record = RunRecord(
        run_id=spec.run_id,
        timestamp=datetime.now(timezone.utc),
        git_commit=git_info.commit,
        git_dirty=git_info.dirty,
        code_hash=hash_config({"module": __name__, "engine_version": spec.engine_version}),
        config_hash=config_hash,
        data_version=spec.universe.data_version,
        factor_versions=dict(spec.factor_versions),
        label_versions=dict(spec.label_versions),
        engine_version=spec.engine_version,
        parameters={
            "universe_id": spec.universe.universe_id,
            "universe_hash": universe_hash,
            "config_hash": config_hash,
            "trading_dates": [item.isoformat() for item in spec.trading_dates],
            "aligned_session_count": len(aligned_sessions),
            "missing_data_flags": {
                instrument_id: list(flags)
                for instrument_id, flags in sorted(missing_data_flags.items())
            },
        },
        artifact_paths=dict(artifact_paths),
        decision_status="universe_fixture_recorded",
        warnings=(),
        status_message="Universe fixture metadata only; review required before broader multi-asset use.",
    )
    with connect_registry(resolved_registry_path) as connection:
        insert_run_record(connection, UNIVERSE_RUN_TABLE, record)
    return resolved_registry_path.as_posix()


def _expected_starts_for_aligned_session(session: AlignedUniverseSession) -> tuple[datetime, ...]:
    starts: list[datetime] = []
    current = session.open_ts
    while current + ONE_MINUTE <= session.close_ts:
        starts.append(current)
        current += ONE_MINUTE
    return tuple(starts)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UniverseRunnerError(f"{field_name} must be a non-empty string")
    return value.strip()


def _date_value(value: date | str, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise UniverseRunnerError(f"{field_name} must be an ISO date") from exc
    raise UniverseRunnerError(f"{field_name} must be a date or ISO date string")


def _datetime_value(value: datetime | str | Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise UniverseRunnerError(f"{field_name} must be an ISO datetime") from exc
    else:
        raise UniverseRunnerError(f"{field_name} must be a datetime or ISO datetime string")
    if active.tzinfo is None or active.utcoffset() is None:
        raise UniverseRunnerError(f"{field_name} must be timezone-aware")
    return active


def _json_text(payload: Any) -> str:
    return json.dumps(_json_ready(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value
