"""Discovery-based Agent Factory role registry."""

from __future__ import annotations

from alpha_system.agent_factory.roles.contracts import AgentRole


class RoleRegistry:
    """In-memory registry populated by role modules at import time."""

    def __init__(self) -> None:
        self._roles: dict[str, AgentRole] = {}

    def register(self, role: AgentRole) -> AgentRole:
        """Register one role contract, rejecting duplicate role ids."""

        if not isinstance(role, AgentRole):
            raise TypeError("role must be an AgentRole")
        role.validate()
        if role.role_id in self._roles:
            raise ValueError(f"role_id already registered: {role.role_id}")
        self._roles[role.role_id] = role
        return role

    def get(self, role_id: str) -> AgentRole:
        """Return one role by id, failing closed when absent."""

        if not isinstance(role_id, str) or not role_id:
            raise ValueError("role_id must be a non-empty str")
        try:
            return self._roles[role_id]
        except KeyError as error:
            raise KeyError(f"unknown role_id: {role_id}") from error

    def all_roles(self) -> tuple[AgentRole, ...]:
        """Return every registered role in deterministic role_id order."""

        return tuple(self._roles[role_id] for role_id in self.role_ids())

    def role_ids(self) -> tuple[str, ...]:
        """Return every registered role id in deterministic order."""

        return tuple(sorted(self._roles))


_REGISTRY = RoleRegistry()


def register(role: AgentRole) -> AgentRole:
    """Register a role with the module-level discovery registry."""

    return _REGISTRY.register(role)


def get(role_id: str) -> AgentRole:
    """Return one role from the module-level discovery registry."""

    return _REGISTRY.get(role_id)


def all_roles() -> tuple[AgentRole, ...]:
    """Return all roles from the module-level discovery registry."""

    return _REGISTRY.all_roles()


def role_ids() -> tuple[str, ...]:
    """Return role ids from the module-level discovery registry."""

    return _REGISTRY.role_ids()
