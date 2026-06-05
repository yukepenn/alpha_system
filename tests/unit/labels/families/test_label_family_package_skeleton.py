from __future__ import annotations

from importlib import import_module


def test_label_family_package_imports_additively() -> None:
    for module_name in (
        "alpha_system.labels",
        "alpha_system.labels.families",
    ):
        module = import_module(module_name)
        assert module.__name__ == module_name
