from __future__ import annotations

from importlib import import_module


def test_feature_package_skeleton_imports() -> None:
    for module_name in (
        "alpha_system.features",
        "alpha_system.features.families",
        "alpha_system.features.primitives",
        "alpha_system.features.engine",
    ):
        module = import_module(module_name)
        assert module.__name__ == module_name
