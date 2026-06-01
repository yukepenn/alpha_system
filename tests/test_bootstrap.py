from pathlib import Path

from tools.frontier import bootstrap


def _create_required_doctor_paths(root: Path, *, omit: str | None = None) -> None:
    files = ["AGENTS.md", "CLAUDE.md", "frontier.yaml"]
    dirs = ["campaigns", "specs", "handoffs", "reviews"]

    for item in files:
        if item != omit:
            (root / item).write_text("placeholder\n", encoding="utf-8")
    for item in dirs:
        if item != omit:
            (root / item).mkdir()


def test_doctor_passes_when_runs_dir_is_absent(tmp_path, monkeypatch, capsys) -> None:
    _create_required_doctor_paths(tmp_path)
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)

    result = bootstrap.doctor()

    output = capsys.readouterr().out
    assert result == 0
    assert "runs/ is local-only runtime state" in output
    assert "Frontier doctor passed." in output
    assert not (tmp_path / "runs").exists()


def test_doctor_does_not_report_runs_as_required(tmp_path, monkeypatch, capsys) -> None:
    _create_required_doctor_paths(tmp_path, omit="specs")
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)

    result = bootstrap.doctor()

    output = capsys.readouterr().out
    assert result == 1
    assert "- specs" in output
    assert "- runs" not in output
    assert not (tmp_path / "runs").exists()
