"""Default-deny Agent Factory tool contract registry."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from alpha_system.agent_factory.tools.contracts import (
    ToolArtifactPolicy,
    ToolContract,
    ToolContractStatus,
    ToolGroup,
)
from alpha_system.agent_factory.tools.results import AgentToolResult


def _default_config_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "configs" / "agent_factory" / "tools" / "registry.toml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("configs/agent_factory/tools/registry.toml is missing")


DEFAULT_CONFIG_PATH = _default_config_path()


class ToolRegistry:
    """Read-only registry of allowed tool contracts."""

    def __init__(self, contracts: tuple[ToolContract, ...]) -> None:
        if not isinstance(contracts, tuple):
            raise TypeError("contracts must be a tuple[ToolContract, ...]")
        by_name: dict[str, ToolContract] = {}
        for contract in contracts:
            if not isinstance(contract, ToolContract):
                raise TypeError("contracts must contain only ToolContract instances")
            contract.validate()
            if contract.name in by_name:
                raise ValueError(f"duplicate tool contract: {contract.name}")
            by_name[contract.name] = contract
        self._contracts: Mapping[str, ToolContract] = MappingProxyType(by_name)

    @classmethod
    def from_config(cls, config_path: Path = DEFAULT_CONFIG_PATH) -> ToolRegistry:
        """Load the declarative value-free tool contract table."""

        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
        raw_tools = payload.get("tools")
        if not isinstance(raw_tools, list) or not raw_tools:
            raise ValueError("tool registry config must contain [[tools]] entries")
        contracts = tuple(_contract_from_config_entry(entry) for entry in raw_tools)
        return cls(contracts)

    def contract_for(self, tool_name: str) -> ToolContract:
        """Return one registered contract without granting call authority."""

        _validate_non_empty_text("tool_name", tool_name)
        try:
            return self._contracts[tool_name]
        except KeyError as error:
            raise KeyError(f"unknown tool: {tool_name}") from error

    def resolve(self, tool_name: str, caller_role: str) -> ToolContract:
        """Return a contract only when both tool and caller are explicitly allowed."""

        contract = self.contract_for(tool_name)
        _validate_non_empty_text("caller_role", caller_role)
        if not contract.allows(caller_role):
            raise PermissionError(f"{caller_role} is not allowed to call {tool_name}")
        return contract

    def all_contracts(self) -> tuple[ToolContract, ...]:
        """Return all contracts in deterministic tool-name order."""

        return tuple(self._contracts[name] for name in self.tool_names())

    def tool_names(self) -> tuple[str, ...]:
        """Return registered tool names in deterministic order."""

        return tuple(sorted(self._contracts))

    def groups(self) -> tuple[str, ...]:
        """Return registered groups in deterministic order."""

        return tuple(sorted({contract.group.value for contract in self._contracts.values()}))

    def list_by_group(self, group: ToolGroup | str) -> tuple[ToolContract, ...]:
        """Return contracts for one registered group in deterministic order."""

        group_value = _coerce_group(group).value
        return tuple(
            contract for contract in self.all_contracts() if contract.group.value == group_value
        )


def _contract_from_config_entry(entry: object) -> ToolContract:
    if not isinstance(entry, Mapping):
        raise ValueError("each tool config entry must be a mapping")
    allowed_keys = {
        "name",
        "group",
        "allowed_callers",
        "permission_matrix_refs",
        "required_inputs",
        "forbidden_side_effects",
        "artifact_policy",
        "failure_states",
        "required_reviewer",
        "reviewer_independence_note",
        "status",
    }
    unknown_keys = set(entry).difference(allowed_keys)
    if unknown_keys:
        raise ValueError(f"unknown tool config keys: {sorted(unknown_keys)}")
    return ToolContract(
        name=_required_str(entry, "name"),
        group=ToolGroup(_required_str(entry, "group")),
        allowed_callers=_required_tuple(entry, "allowed_callers"),
        permission_matrix_refs=_required_tuple(entry, "permission_matrix_refs"),
        required_inputs=_required_tuple(entry, "required_inputs"),
        output_schema=AgentToolResult,
        forbidden_side_effects=_required_tuple(entry, "forbidden_side_effects"),
        artifact_policy=ToolArtifactPolicy(_required_str(entry, "artifact_policy")),
        failure_states=_required_tuple(entry, "failure_states"),
        required_reviewer=_required_str(entry, "required_reviewer"),
        reviewer_independence_note=_required_str(entry, "reviewer_independence_note"),
        status=ToolContractStatus(_required_str(entry, "status")),
    )


def _required_str(entry: Mapping[str, Any], key: str) -> str:
    value = entry.get(key)
    _validate_non_empty_text(key, value)
    return value


def _required_tuple(entry: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = entry.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    result = tuple(value)
    for item in result:
        _validate_non_empty_text(key, item)
    return result


def _coerce_group(group: ToolGroup | str) -> ToolGroup:
    if isinstance(group, ToolGroup):
        return group
    if isinstance(group, str):
        _validate_non_empty_text("group", group)
        try:
            return ToolGroup(group)
        except ValueError as error:
            raise KeyError(f"unknown tool group: {group}") from error
    raise TypeError("group must be a ToolGroup or str")


def _validate_non_empty_text(field_name: str, value: object) -> None:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty str")


TOOL_REGISTRY = ToolRegistry.from_config()


def contract_for(tool_name: str) -> ToolContract:
    """Return one registered contract from the module-level registry."""

    return TOOL_REGISTRY.contract_for(tool_name)


def resolve(tool_name: str, caller_role: str) -> ToolContract:
    """Resolve a callable tool contract, failing closed on unknown or disallowed calls."""

    return TOOL_REGISTRY.resolve(tool_name, caller_role)


def all_contracts() -> tuple[ToolContract, ...]:
    """Return all contracts from the module-level registry."""

    return TOOL_REGISTRY.all_contracts()


def tool_names() -> tuple[str, ...]:
    """Return all registered tool names."""

    return TOOL_REGISTRY.tool_names()


def groups() -> tuple[str, ...]:
    """Return all registered tool groups."""

    return TOOL_REGISTRY.groups()


def list_by_group(group: ToolGroup | str) -> tuple[ToolContract, ...]:
    """Return registered contracts for one group."""

    return TOOL_REGISTRY.list_by_group(group)
