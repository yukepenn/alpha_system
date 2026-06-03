from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_l2_feature_phase_does_not_add_forbidden_runtime_modules() -> None:
    l2_root = REPO_ROOT / "src" / "alpha_system" / "l2"
    forbidden_names = {
        "replay.py",
        "book_reconstruction.py",
        "queue_model.py",
        "passive_fills.py",
        "order_book_replay.py",
    }

    assert not {
        path.name
        for path in l2_root.glob("*.py")
        if path.name in forbidden_names or "replay" in path.name or "queue" in path.name
    }


def test_l2_feature_tests_leave_repo_artifact_roots_clean() -> None:
    allowed_placeholder_names = {"README.md", ".gitkeep"}
    roots = (
        REPO_ROOT / "data" / "factors",
        REPO_ROOT / "artifacts",
        REPO_ROOT / "metadata",
    )

    for root in roots:
        if not root.exists():
            continue
        unexpected = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.name not in allowed_placeholder_names
        ]
        assert unexpected == []
