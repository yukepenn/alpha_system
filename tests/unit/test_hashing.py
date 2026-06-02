from __future__ import annotations

from pathlib import Path

from alpha_system.core.hashing import canonical_json, hash_code_paths, hash_config


def test_hash_config_is_deterministic_for_key_order_changes() -> None:
    left = {"b": 2, "a": {"y": True, "x": [1, 2]}}
    right = {"a": {"x": [1, 2], "y": True}, "b": 2}

    assert canonical_json(left) == canonical_json(right)
    assert hash_config(left) == hash_config(right)


def test_hash_config_changes_for_meaningful_change() -> None:
    original = {"window": 20, "session_reset": True}
    changed = {"window": 21, "session_reset": True}

    assert hash_config(original) != hash_config(changed)


def test_hash_code_paths_includes_path_and_content(tmp_path: Path) -> None:
    source = tmp_path / "factor.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    original_hash = hash_code_paths([source], root=tmp_path)
    source.write_text("VALUE = 2\n", encoding="utf-8")

    assert original_hash != hash_code_paths([source], root=tmp_path)
