from __future__ import annotations

import hashlib
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.data.databento import cost_check
from alpha_system.data.databento.cost_check import run_cost_check
from alpha_system.data.databento.download_batch import run_download_batch
from alpha_system.data.databento.manifest_files import run_manifest_files
from alpha_system.data.databento.request_spec import (
    DATABENTO_ALLOWED_SCHEMAS,
    DatabentoRequestSpec,
    build_default_continuous_request_spec,
    request_spec_hash,
    write_json_mapping,
)
from alpha_system.data.databento.submit_batch import (
    JobsManifest,
    SubmittedDatabentoJob,
    run_submit_batch,
    write_jobs_manifest,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2024, 1, 3, tzinfo=UTC)
NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)


class FakeMetadata:
    def __init__(self, costs: dict[str, float]) -> None:
        self.costs = costs
        self.calls: list[dict[str, object]] = []

    def get_cost(self, **kwargs: object) -> float:
        self.calls.append(dict(kwargs))
        return self.costs[str(kwargs["schema"])]


class FakeBatch:
    def __init__(self, *, states: list[dict[str, str]] | None = None) -> None:
        self.states = states or []
        self.submit_calls: list[dict[str, object]] = []
        self.list_calls: list[dict[str, object]] = []
        self.download_calls: list[dict[str, object]] = []

    def submit_job(self, **kwargs: object) -> dict[str, str]:
        self.submit_calls.append(dict(kwargs))
        return {"id": f"job-{kwargs['schema']}"}

    def list_jobs(self, **kwargs: object) -> list[dict[str, str]]:
        self.list_calls.append(dict(kwargs))
        return self.states

    def download(self, job_id: str, *, output_dir: Path, **kwargs: object) -> list[Path]:
        del kwargs
        self.download_calls.append({"job_id": job_id, "output_dir": output_dir})
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{job_id}.dbn.zst"
        path.write_bytes(f"fake-{job_id}".encode("ascii"))
        return [path]


class FakeDatabentoClient:
    def __init__(
        self,
        *,
        costs: dict[str, float] | None = None,
        states: list[dict[str, str]] | None = None,
    ) -> None:
        self.metadata = FakeMetadata(costs or {})
        self.batch = FakeBatch(states=states)


def _spec() -> DatabentoRequestSpec:
    return DatabentoRequestSpec(
        symbols=("ES.v.0", "NQ.v.0"),
        stype_in="continuous",
        schemas=("ohlcv-1m", "definition"),
        start=START,
        end=END,
    )


def _write_valid_cost_manifest(tmp_path: Path, spec: DatabentoRequestSpec) -> Path:
    path = tmp_path / "cost.json"
    fake = FakeDatabentoClient(costs={"ohlcv-1m": 10.0, "definition": 5.0})
    run_cost_check(
        request_spec=spec,
        client=fake,
        max_cost_usd=20.0,
        env={"CI": "true"},
        output_path=path,
        now=NOW,
    )
    return path


def _write_custom_cost_manifest(
    tmp_path: Path,
    spec: DatabentoRequestSpec,
    *,
    path_name: str,
    total_usd: float,
    max_cost_usd: float,
    created_at: datetime,
) -> Path:
    path = tmp_path / path_name
    manifest = cost_check.CostManifest(
        request_spec_hash=request_spec_hash(spec),
        per_schema_usd={spec.schemas[0]: total_usd},
        total_usd=total_usd,
        max_cost_usd=max_cost_usd,
        under_budget=total_usd <= max_cost_usd,
        symbols=spec.symbols,
        stype_in=spec.stype_in,
        start=spec.start.isoformat(),
        end=spec.end.isoformat(),
        dataset=spec.dataset,
        created_at=created_at,
    )
    cost_check.write_cost_manifest(manifest, path)
    return path


def _write_jobs_manifest(tmp_path: Path, spec: DatabentoRequestSpec) -> Path:
    path = tmp_path / "jobs.json"
    manifest = JobsManifest(
        request_spec_hash=request_spec_hash(spec),
        jobs=tuple(
            SubmittedDatabentoJob(job_id=f"job-{schema}", schema=schema)
            for schema in spec.schemas
        ),
        dataset=spec.dataset,
        symbols=spec.symbols,
        stype_in=spec.stype_in,
        start=spec.start.isoformat(),
        end=spec.end.isoformat(),
        encoding=spec.encoding,
        compression=spec.compression,
        submitted_at=NOW,
    )
    write_jobs_manifest(manifest, path)
    return path


def test_request_spec_validates_allowed_databento_contract() -> None:
    spec = build_default_continuous_request_spec(START, END)

    assert spec.symbols == ("ES.v.0", "NQ.v.0", "RTY.v.0")
    assert spec.schemas == DATABENTO_ALLOWED_SCHEMAS
    assert spec.to_mapping()["as_of"] == END.isoformat()
    assert DatabentoRequestSpec.from_mapping(spec.to_mapping()) == spec
    assert request_spec_hash(spec) == request_spec_hash(spec.to_mapping())

    DatabentoRequestSpec(
        symbols=("ES.FUT", "RTY.FUT"),
        stype_in="parent",
        schemas=("status",),
        start=START,
        end=END,
    )


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"symbols": ("MES.v.0",), "stype_in": "continuous"}, "micro"),
        ({"schemas": ("trades",)}, "schemas"),
        ({"stype_in": "instrument_id"}, "stype_in"),
        ({"encoding": "csv"}, "encoding"),
    ],
)
def test_request_spec_rejects_micros_bad_schema_bad_stype_and_non_dbn(
    kwargs: dict[str, object],
    match: str,
) -> None:
    values = {
        "symbols": ("ES.v.0",),
        "stype_in": "continuous",
        "schemas": ("ohlcv-1m",),
        "start": START,
        "end": END,
    }
    values.update(kwargs)

    with pytest.raises(DataFoundationValidationError, match=match):
        DatabentoRequestSpec(**values)


def test_cost_check_under_budget_writes_manifest_without_key(tmp_path: Path) -> None:
    spec = _spec()
    fake = FakeDatabentoClient(costs={"ohlcv-1m": 7.5, "definition": 2.5})
    manifest_path = tmp_path / "cost.json"

    manifest = run_cost_check(
        request_spec=spec,
        client=fake,
        max_cost_usd=20.0,
        env={"CI": "true"},
        output_path=manifest_path,
        now=NOW,
    )

    assert manifest.under_budget is True
    assert manifest.total_usd == 10.0
    assert manifest_path.exists()
    assert "DATABENTO_API_KEY" not in manifest_path.read_text(encoding="utf-8")
    assert [call["schema"] for call in fake.metadata.calls] == list(spec.schemas)
    assert fake.metadata.calls[0]["dataset"] == "GLBX.MDP3"
    assert fake.metadata.calls[0]["mode"] == "historical"
    assert fake.metadata.calls[0]["symbols"] == list(spec.symbols)


def test_cost_check_over_budget_cli_writes_blocking_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / "spec.json"
    cost_path = tmp_path / "cost.json"
    write_json_mapping(spec_path, _spec().to_mapping())
    fake = FakeDatabentoClient(costs={"ohlcv-1m": 7.0, "definition": 6.0})

    @contextmanager
    def fake_context(**kwargs: object):
        del kwargs
        yield fake

    monkeypatch.setattr(cost_check, "_historical_client_context", fake_context)

    rc = cost_check.main(
        [
            "--request-spec",
            spec_path.as_posix(),
            "--output",
            cost_path.as_posix(),
            "--max-cost-usd",
            "10",
        ]
    )

    assert rc == 2
    payload = cost_path.read_text(encoding="utf-8")
    assert '"under_budget": false' in payload
    assert fake.batch.submit_calls == []


def test_live_cost_check_auth_gate_runs_before_client_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_build(*args: object, **kwargs: object) -> object:
        raise AssertionError("client build should not run before the auth gate")

    monkeypatch.setattr(cost_check, "build_historical_client", fail_build)

    with pytest.raises(DataFoundationValidationError, match="ALPHA_DATA_PULL_AUTHORIZED"):
        run_cost_check(request_spec=_spec(), env={})


def test_submit_batch_refuses_without_valid_under_budget_cost_manifest(tmp_path: Path) -> None:
    spec = _spec()
    cost_path = tmp_path / "over_budget.json"
    fake_cost = FakeDatabentoClient(costs={"ohlcv-1m": 60.0, "definition": 60.0})
    run_cost_check(
        request_spec=spec,
        client=fake_cost,
        max_cost_usd=110.0,
        output_path=cost_path,
        now=NOW,
    )
    fake_submit = FakeDatabentoClient()

    with pytest.raises(DataFoundationValidationError, match="under budget"):
        run_submit_batch(
            request_spec=spec,
            cost_manifest_path=cost_path,
            client=fake_submit,
            env={"CI": "true"},
            output_path=tmp_path / "jobs.json",
            now=NOW,
        )

    assert fake_submit.batch.submit_calls == []


@pytest.mark.parametrize(
    ("total_usd", "max_cost_usd", "path_name"),
    [
        (120.0, 1_000_000_000.0, "inflated_total_cost.json"),
        (15.0, 1_000_000_000.0, "inflated_max_cost.json"),
    ],
)
def test_submit_batch_refuses_cost_manifest_above_submit_hard_cap(
    tmp_path: Path,
    total_usd: float,
    max_cost_usd: float,
    path_name: str,
) -> None:
    spec = _spec()
    cost_path = _write_custom_cost_manifest(
        tmp_path,
        spec,
        path_name=path_name,
        total_usd=total_usd,
        max_cost_usd=max_cost_usd,
        created_at=NOW,
    )
    fake_submit = FakeDatabentoClient()

    with pytest.raises(DataFoundationValidationError, match="hard cap"):
        run_submit_batch(
            request_spec=spec,
            cost_manifest_path=cost_path,
            client=fake_submit,
            env={"CI": "true"},
            output_path=tmp_path / "jobs.json",
            now=NOW,
        )

    assert fake_submit.batch.submit_calls == []


def test_submit_batch_refuses_stale_cost_manifest_and_accepts_fresh(tmp_path: Path) -> None:
    spec = _spec()
    stale_cost_path = _write_custom_cost_manifest(
        tmp_path,
        spec,
        path_name="stale_cost.json",
        total_usd=15.0,
        max_cost_usd=20.0,
        created_at=NOW - timedelta(days=2),
    )
    stale_fake = FakeDatabentoClient()

    with pytest.raises(
        DataFoundationValidationError,
        match="cost manifest is stale; re-run cost_check before submitting",
    ):
        run_submit_batch(
            request_spec=spec,
            cost_manifest_path=stale_cost_path,
            client=stale_fake,
            env={"CI": "true"},
            output_path=tmp_path / "stale_jobs.json",
            now=NOW,
        )

    assert stale_fake.batch.submit_calls == []

    fresh_cost_path = _write_custom_cost_manifest(
        tmp_path,
        spec,
        path_name="fresh_cost.json",
        total_usd=15.0,
        max_cost_usd=20.0,
        created_at=NOW,
    )
    fresh_fake = FakeDatabentoClient()

    manifest = run_submit_batch(
        request_spec=spec,
        cost_manifest_path=fresh_cost_path,
        client=fresh_fake,
        env={"CI": "true"},
        output_path=tmp_path / "fresh_jobs.json",
        now=NOW,
    )

    assert tuple(job.schema for job in manifest.jobs) == spec.schemas
    assert [call["schema"] for call in fresh_fake.batch.submit_calls] == list(spec.schemas)


def test_submit_batch_submits_one_dbn_zstd_job_per_schema(tmp_path: Path) -> None:
    spec = _spec()
    cost_path = _write_valid_cost_manifest(tmp_path, spec)
    jobs_path = tmp_path / "jobs.json"
    fake = FakeDatabentoClient()

    manifest = run_submit_batch(
        request_spec=spec,
        cost_manifest_path=cost_path,
        client=fake,
        env={"CI": "true"},
        output_path=jobs_path,
        now=NOW,
    )

    assert jobs_path.exists()
    assert tuple(job.schema for job in manifest.jobs) == spec.schemas
    assert [call["schema"] for call in fake.batch.submit_calls] == list(spec.schemas)
    for call in fake.batch.submit_calls:
        assert call["dataset"] == "GLBX.MDP3"
        assert call["encoding"] == "dbn"
        assert call["compression"] == "zstd"
        assert call["stype_in"] == "continuous"
        assert call["stype_out"] == "instrument_id"
        assert call["split_symbols"] is False
        assert call["split_duration"] == "day"
        assert call["delivery"] == "download"


def test_download_batch_writes_only_under_output_root_and_rejects_repo_root(
    tmp_path: Path,
) -> None:
    spec = _spec()
    jobs_path = _write_jobs_manifest(tmp_path, spec)
    fake = FakeDatabentoClient(
        states=[{"id": f"job-{schema}", "state": "done"} for schema in spec.schemas],
    )
    output_root = tmp_path / "alpha_data"

    manifest = run_download_batch(
        jobs_manifest_path=jobs_path,
        output_root=output_root,
        client=fake,
        env={"CI": "true", "ALPHA_DATA_ROOT": tmp_path.as_posix()},
        now=NOW,
    )

    assert len(manifest.downloaded_files) == len(spec.schemas)
    for record in manifest.downloaded_files:
        path = Path(record.path)
        assert path.exists()
        path.relative_to(output_root)
        assert "alpha_system/tests" not in path.as_posix()

    with pytest.raises(DataFoundationValidationError, match="repository"):
        run_download_batch(
            jobs_manifest_path=jobs_path,
            output_root=Path.cwd() / "repo_raw_should_not_be_created",
            client=fake,
            env={"CI": "true", "ALPHA_DATA_ROOT": tmp_path.as_posix()},
        )


def test_download_batch_rejects_unsafe_manifest_segments_before_mkdir_or_download(
    tmp_path: Path,
) -> None:
    spec = _spec()
    escape_name = f"{tmp_path.name}-outside-download-root"
    malicious_stype = f"../../../../{escape_name}"
    jobs_path = tmp_path / "traversal_jobs.json"
    job_id = "job-ohlcv-1m"
    manifest = JobsManifest(
        request_spec_hash=request_spec_hash(spec),
        jobs=(SubmittedDatabentoJob(job_id=job_id, schema="ohlcv-1m"),),
        dataset=spec.dataset,
        symbols=spec.symbols,
        stype_in=malicious_stype,
        start=spec.start.isoformat(),
        end=spec.end.isoformat(),
        encoding=spec.encoding,
        compression=spec.compression,
        submitted_at=NOW,
    )
    write_jobs_manifest(manifest, jobs_path)
    fake = FakeDatabentoClient(states=[{"id": job_id, "state": "done"}])
    output_root = tmp_path / "alpha_data"
    escaped_root = tmp_path.parent / escape_name

    assert not output_root.exists()
    assert not escaped_root.exists()
    with pytest.raises(DataFoundationValidationError, match="safe path segment"):
        run_download_batch(
            jobs_manifest_path=jobs_path,
            output_root=output_root,
            client=fake,
            env={"CI": "true", "ALPHA_DATA_ROOT": tmp_path.as_posix()},
            now=NOW,
        )

    assert fake.batch.download_calls == []
    assert not output_root.exists()
    assert not escaped_root.exists()


def test_file_manifest_hashes_sizes_and_refuses_changed_overwrite(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw_root"
    first = raw_root / "raw" / "glbx_mdp3" / "continuous" / "ohlcv-1m" / "job-a" / "a.dbn.zst"
    second = raw_root / "raw" / "glbx_mdp3" / "continuous" / "bbo-1m" / "job-b" / "b.dbn.zst"
    first.parent.mkdir(parents=True, exist_ok=True)
    second.parent.mkdir(parents=True, exist_ok=True)
    first.write_bytes(b"alpha")
    second.write_bytes(b"beta")
    output = tmp_path / "files.json"

    manifest = run_manifest_files(raw_root=raw_root, output_path=output, now=NOW)

    assert output.exists()
    assert manifest.file_count == 2
    assert manifest.total_bytes == len(b"alpha") + len(b"beta")
    by_path = {record.relative_path: record for record in manifest.files}
    assert by_path[first.relative_to(raw_root).as_posix()].sha256 == hashlib.sha256(
        b"alpha"
    ).hexdigest()
    assert by_path[second.relative_to(raw_root).as_posix()].size_bytes == len(b"beta")

    same = run_manifest_files(raw_root=raw_root, output_path=output, now=NOW)
    assert same.manifest_hash == manifest.manifest_hash

    first.write_bytes(b"changed")
    with pytest.raises(DataFoundationValidationError, match="refusing overwrite"):
        run_manifest_files(raw_root=raw_root, output_path=output, now=NOW)
