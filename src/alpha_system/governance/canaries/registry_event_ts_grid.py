"""Registry canary for bar-grid feature and label event timestamps."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_EVENT_TS_GRID_FIXTURE_PATH = Path(
    "evals/canaries/registry_event_ts_grid/synthetic_fixture.json"
)


class RegistryEventTsGridCanaryError(ValueError):
    """Raised when the registry event_ts grid canary cannot parse its inputs."""


@dataclass(frozen=True, slots=True)
class EventTsGridAllowlistEntry:
    """A visible grandfather entry for known off-grid registry debt."""

    registration_kind: str
    family: str
    id_prefix: str
    reason_code: str
    rationale: str

    def matches(self, issue: RegistryEventTsGridIssue) -> bool:
        if issue.registration_kind != self.registration_kind:
            return False
        if issue.family != self.family:
            return False
        return (
            not self.id_prefix
            or issue.registration_id.startswith(self.id_prefix)
            or issue.pack_id.startswith(self.id_prefix)
        )


@dataclass(frozen=True, slots=True)
class RegistrationEventRange:
    """First/last event timestamp metadata for one registry row."""

    registration_kind: str
    family: str
    pack_id: str
    registration_id: str
    version_id: str
    first_event_ts: datetime
    last_event_ts: datetime


@dataclass(frozen=True, slots=True)
class RegistryEventTsGridIssue:
    """One off-grid timestamp found in registered metadata."""

    registration_kind: str
    family: str
    pack_id: str
    registration_id: str
    version_id: str
    timestamp_field: str
    timestamp: datetime
    allowlist_reason_code: str = ""

    def to_line(self, prefix: str) -> str:
        reason = f" reason={self.allowlist_reason_code}" if self.allowlist_reason_code else ""
        return (
            f"{prefix} kind={self.registration_kind} family={self.family} "
            f"pack={self.pack_id} id={self.registration_id} version={self.version_id} "
            f"field={self.timestamp_field} ts={self.timestamp.isoformat()}{reason}"
        )


@dataclass(frozen=True, slots=True)
class RegistryEventTsGridResult:
    """Value-free result summary for the registry event_ts grid canary."""

    scanned_count: int
    allowed_debt: tuple[RegistryEventTsGridIssue, ...] = ()
    violations: tuple[RegistryEventTsGridIssue, ...] = ()
    skipped: bool = False
    skip_reason: str = ""

    @property
    def passed(self) -> bool:
        return self.skipped or not self.violations

    @property
    def off_grid_count(self) -> int:
        return len(self.allowed_debt) + len(self.violations)

    def summary_line(self) -> str:
        if self.skipped:
            return f"SKIP registry_event_ts_grid {self.skip_reason}"
        status = "PASS" if self.passed else "FAIL"
        return (
            f"{status} registry_event_ts_grid scanned={self.scanned_count} "
            f"off_grid={self.off_grid_count} allowed_debt={len(self.allowed_debt)} "
            f"violations={len(self.violations)}"
        )

    def detail_lines(self) -> tuple[str, ...]:
        lines = [self.summary_line()]
        lines.extend(issue.to_line("ALLOW") for issue in self.allowed_debt)
        lines.extend(issue.to_line("VIOLATION") for issue in self.violations)
        return tuple(lines)


# Removing repaired debt is intentionally a one-line deletion from this tuple.
REGISTRY_EVENT_TS_GRID_ALLOWLIST: tuple[EventTsGridAllowlistEntry, ...] = (
    EventTsGridAllowlistEntry(
        registration_kind="feature",
        family="bbo_tradability",
        id_prefix="bbo_tradability_",
        reason_code="BBO_PENDING_RE_MATERIALIZATION",
        rationale=(
            "Existing BBO feature packs were registered before family emission "
            "normalized event_ts to bar_end_ts."
        ),
    ),
    EventTsGridAllowlistEntry(
        registration_kind="label",
        family="cost_adjusted",
        id_prefix="",
        reason_code="COST_SPREAD_LABEL_MIRROR_DEFECT",
        rationale=(
            "Existing cost/spread-adjusted label packs mirror BBO quote-time "
            "event_ts debt until their documented repair and re-lock."
        ),
    ),
)


def load_default_registry_event_ts_grid_fixture() -> Mapping[str, Any]:
    """Load the tiny synthetic fixture used by CI canary_runner."""

    path = _repo_root() / DEFAULT_REGISTRY_EVENT_TS_GRID_FIXTURE_PATH
    return load_registry_event_ts_grid_fixture(path)


def load_registry_event_ts_grid_fixture(path: str | Path) -> Mapping[str, Any]:
    """Load one registry event_ts grid canary fixture."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise RegistryEventTsGridCanaryError("registry grid canary fixture must be a mapping")
    return payload


def run_registry_event_ts_grid_canary(
    *,
    mode: str = "synthetic",
    fixture: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
    alpha_data_root: str | Path | None = None,
    feature_registry_path: str | Path | None = None,
    label_registry_path: str | Path | None = None,
    allowlist: Sequence[EventTsGridAllowlistEntry] = REGISTRY_EVENT_TS_GRID_ALLOWLIST,
) -> RegistryEventTsGridResult:
    """Run the registry event_ts grid canary in synthetic or live-registry mode."""

    if mode == "synthetic":
        active_fixture = fixture or load_default_registry_event_ts_grid_fixture()
        return scan_registry_event_ts_grid(
            _registrations_from_fixture(active_fixture),
            allowlist=allowlist,
        )
    if mode == "live":
        return scan_live_registry_event_ts_grid(
            env=env,
            alpha_data_root=alpha_data_root,
            feature_registry_path=feature_registry_path,
            label_registry_path=label_registry_path,
            allowlist=allowlist,
        )
    raise RegistryEventTsGridCanaryError("mode must be synthetic or live")


def scan_live_registry_event_ts_grid(
    *,
    env: Mapping[str, str] | None = None,
    alpha_data_root: str | Path | None = None,
    feature_registry_path: str | Path | None = None,
    label_registry_path: str | Path | None = None,
    allowlist: Sequence[EventTsGridAllowlistEntry] = REGISTRY_EVENT_TS_GRID_ALLOWLIST,
) -> RegistryEventTsGridResult:
    """Scan live local registries, skipping loudly when registry files are absent."""

    paths = _live_registry_paths(
        env=env,
        alpha_data_root=alpha_data_root,
        feature_registry_path=feature_registry_path,
        label_registry_path=label_registry_path,
    )
    if isinstance(paths, str):
        return RegistryEventTsGridResult(0, skipped=True, skip_reason=paths)
    feature_path, label_path = paths
    missing = tuple(path.as_posix() for path in (feature_path, label_path) if not path.exists())
    if missing:
        return RegistryEventTsGridResult(
            0,
            skipped=True,
            skip_reason="live registry file absent: " + ", ".join(missing),
        )
    registrations = (
        *_feature_registrations_from_sqlite(feature_path),
        *_label_registrations_from_sqlite(label_path),
    )
    return scan_registry_event_ts_grid(registrations, allowlist=allowlist)


def scan_registry_event_ts_grid(
    registrations: Sequence[RegistrationEventRange],
    *,
    allowlist: Sequence[EventTsGridAllowlistEntry] = REGISTRY_EVENT_TS_GRID_ALLOWLIST,
) -> RegistryEventTsGridResult:
    """Return PASS only when every off-grid registry timestamp is grandfathered."""

    allowed: list[RegistryEventTsGridIssue] = []
    violations: list[RegistryEventTsGridIssue] = []
    for registration in registrations:
        for timestamp_field, timestamp in (
            ("first_event_ts", registration.first_event_ts),
            ("last_event_ts", registration.last_event_ts),
        ):
            if _is_minute_grid_timestamp(timestamp):
                continue
            issue = RegistryEventTsGridIssue(
                registration_kind=registration.registration_kind,
                family=registration.family,
                pack_id=registration.pack_id,
                registration_id=registration.registration_id,
                version_id=registration.version_id,
                timestamp_field=timestamp_field,
                timestamp=timestamp,
            )
            allowlist_entry = _matching_allowlist_entry(issue, allowlist)
            if allowlist_entry is None:
                violations.append(issue)
                continue
            allowed.append(
                RegistryEventTsGridIssue(
                    registration_kind=issue.registration_kind,
                    family=issue.family,
                    pack_id=issue.pack_id,
                    registration_id=issue.registration_id,
                    version_id=issue.version_id,
                    timestamp_field=issue.timestamp_field,
                    timestamp=issue.timestamp,
                    allowlist_reason_code=allowlist_entry.reason_code,
                )
            )
    return RegistryEventTsGridResult(
        scanned_count=len(registrations),
        allowed_debt=tuple(allowed),
        violations=tuple(violations),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for canary_runner and live-registry spot checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("synthetic", "live"), default="synthetic")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--alpha-data-root", type=Path)
    parser.add_argument("--feature-registry", type=Path)
    parser.add_argument("--label-registry", type=Path)
    parser.add_argument(
        "--no-allowlist",
        action="store_true",
        help="Report known off-grid debt as violations instead of grandfathered debt.",
    )
    args = parser.parse_args(argv)

    fixture = load_registry_event_ts_grid_fixture(args.fixture) if args.fixture else None
    result = run_registry_event_ts_grid_canary(
        mode=args.mode,
        fixture=fixture,
        alpha_data_root=args.alpha_data_root,
        feature_registry_path=args.feature_registry,
        label_registry_path=args.label_registry,
        allowlist=() if args.no_allowlist else REGISTRY_EVENT_TS_GRID_ALLOWLIST,
    )
    for line in result.detail_lines():
        print(line)
    return 0 if result.passed else 1


def _registrations_from_fixture(fixture: Mapping[str, Any]) -> tuple[RegistrationEventRange, ...]:
    raw_registrations = fixture.get("registrations")
    if not isinstance(raw_registrations, Sequence) or isinstance(raw_registrations, str):
        raise RegistryEventTsGridCanaryError("fixture.registrations must be a sequence")
    return tuple(
        _registration_from_mapping(_require_mapping(item, "fixture.registrations[]"))
        for item in raw_registrations
    )


def _registration_from_mapping(values: Mapping[str, Any]) -> RegistrationEventRange:
    return RegistrationEventRange(
        registration_kind=_required_text(values.get("registration_kind"), "registration_kind"),
        family=_required_text(values.get("family"), "family"),
        pack_id=_required_text(values.get("pack_id"), "pack_id"),
        registration_id=_required_text(values.get("registration_id"), "registration_id"),
        version_id=_required_text(values.get("version_id"), "version_id"),
        first_event_ts=_timestamp(values.get("first_event_ts"), "first_event_ts"),
        last_event_ts=_timestamp(values.get("last_event_ts"), "last_event_ts"),
    )


def _feature_registrations_from_sqlite(path: Path) -> tuple[RegistrationEventRange, ...]:
    rows = _read_registry_rows(
        path,
        table_name="feature_registry_records",
        columns=(
            "feature_version_id",
            "feature_id",
            "first_event_ts",
            "last_event_ts",
            "metadata_json",
        ),
        lifecycle_state="REGISTERED",
    )
    registrations: list[RegistrationEventRange] = []
    for row in rows:
        payload = _json_mapping(str(row["metadata_json"]), "feature metadata_json")
        spec = _optional_mapping(payload.get("feature_spec"))
        membership = _optional_mapping(payload.get("feature_set_membership"))
        feature_id = _required_text(row["feature_id"], "feature_id")
        registrations.append(
            RegistrationEventRange(
                registration_kind="feature",
                family=_optional_text(spec.get("family"), "unknown_feature_family"),
                pack_id=_optional_text(membership.get("feature_set_id"), feature_id),
                registration_id=feature_id,
                version_id=_required_text(row["feature_version_id"], "feature_version_id"),
                first_event_ts=_timestamp(row["first_event_ts"], "first_event_ts"),
                last_event_ts=_timestamp(row["last_event_ts"], "last_event_ts"),
            )
        )
    return tuple(registrations)


def _label_registrations_from_sqlite(path: Path) -> tuple[RegistrationEventRange, ...]:
    rows = _read_registry_rows(
        path,
        table_name="label_registry_records",
        columns=(
            "label_version_id",
            "label_id",
            "first_event_ts",
            "last_event_ts",
            "metadata_json",
        ),
        lifecycle_state="REGISTERED",
    )
    registrations: list[RegistrationEventRange] = []
    for row in rows:
        payload = _json_mapping(str(row["metadata_json"]), "label metadata_json")
        contract = _optional_mapping(payload.get("label_contract"))
        registry_metadata = _optional_mapping(payload.get("registry_metadata"))
        materialization = _optional_mapping(payload.get("materialization"))
        label_id = _required_text(row["label_id"], "label_id")
        registrations.append(
            RegistrationEventRange(
                registration_kind="label",
                family=_optional_text(contract.get("family"), "unknown_label_family"),
                pack_id=_optional_text(
                    registry_metadata.get("label_pack_id"),
                    _optional_text(materialization.get("plan_id"), label_id),
                ),
                registration_id=label_id,
                version_id=_required_text(row["label_version_id"], "label_version_id"),
                first_event_ts=_timestamp(row["first_event_ts"], "first_event_ts"),
                last_event_ts=_timestamp(row["last_event_ts"], "last_event_ts"),
            )
        )
    return tuple(registrations)


def _read_registry_rows(
    path: Path,
    *,
    table_name: str,
    columns: Sequence[str],
    lifecycle_state: str,
) -> tuple[sqlite3.Row, ...]:
    with _connect_read_only(path) as connection:
        if not _table_exists(connection, table_name):
            return ()
        selected = ", ".join(columns)
        rows = connection.execute(
            f"""
            SELECT {selected}
            FROM {table_name}
            WHERE lifecycle_state = ?
            ORDER BY 1
            """,
            (lifecycle_state,),
        ).fetchall()
    return tuple(rows)


def _connect_read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _live_registry_paths(
    *,
    env: Mapping[str, str] | None,
    alpha_data_root: str | Path | None,
    feature_registry_path: str | Path | None,
    label_registry_path: str | Path | None,
) -> tuple[Path, Path] | str:
    feature_path = (
        Path(feature_registry_path).expanduser().resolve(strict=False)
        if feature_registry_path
        else None
    )
    label_path = (
        Path(label_registry_path).expanduser().resolve(strict=False)
        if label_registry_path
        else None
    )
    if feature_path is not None and label_path is not None:
        return feature_path, label_path
    source = os.environ if env is None else env
    root_value = alpha_data_root or source.get("ALPHA_DATA_ROOT")
    if root_value is None:
        return "ALPHA_DATA_ROOT is unset; live registry mode requires local registry paths"
    root = Path(root_value).expanduser().resolve(strict=False)
    return (
        feature_path or root / "registry" / "features.sqlite",
        label_path or root / "registry" / "labels.sqlite",
    )


def _matching_allowlist_entry(
    issue: RegistryEventTsGridIssue,
    allowlist: Sequence[EventTsGridAllowlistEntry],
) -> EventTsGridAllowlistEntry | None:
    for entry in allowlist:
        if entry.matches(issue):
            return entry
    return None


def _is_minute_grid_timestamp(timestamp: datetime) -> bool:
    return timestamp.second == 0 and timestamp.microsecond == 0


def _timestamp(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            timestamp = datetime.fromisoformat(text)
        except ValueError as exc:
            raise RegistryEventTsGridCanaryError(f"{field_name} must be an ISO timestamp") from exc
    else:
        raise RegistryEventTsGridCanaryError(f"{field_name} must be an ISO timestamp")
    if timestamp.tzinfo is None:
        raise RegistryEventTsGridCanaryError(f"{field_name} must be timezone-aware")
    return timestamp


def _json_mapping(text: str, field_name: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RegistryEventTsGridCanaryError(f"{field_name} must be JSON") from exc
    return _require_mapping(payload, field_name)


def _require_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RegistryEventTsGridCanaryError(f"{field_name} must be a mapping")
    return value


def _optional_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryEventTsGridCanaryError(f"{field_name} must be non-empty text")
    return value.strip()


def _optional_text(value: object, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


if __name__ == "__main__":
    raise SystemExit(main())
