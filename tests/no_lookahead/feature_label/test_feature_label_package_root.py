from __future__ import annotations

from importlib import import_module


def test_feature_label_no_lookahead_root_imports() -> None:
    for module_name in (
        "alpha_system.features",
        "alpha_system.labels.families",
    ):
        module = import_module(module_name)
        assert module.__name__ == module_name
