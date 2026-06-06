"""Agent role contracts and registration surface."""

from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.roles.registry import (
    RoleRegistry,
    all_roles,
    get,
    register,
    role_ids,
)

__all__ = [
    "AgentRole",
    "RoleRegistry",
    "all_roles",
    "get",
    "register",
    "role_ids",
]
