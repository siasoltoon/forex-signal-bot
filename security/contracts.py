from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Permission:
    resource: str
    action: str


@dataclass(frozen=True, slots=True)
class AuthContext:
    subject: str
    roles: tuple[str, ...] = ()
    permissions: tuple[Permission, ...] = ()

    def can(self, resource: str, action: str) -> bool:
        return Permission(resource, action) in self.permissions


@dataclass(frozen=True, slots=True)
class SecurityAuditEvent:
    event_id: str
    actor: str
    action: str
    resource: str
    outcome: str
    timestamp: str
    metadata: dict[str, object] | None = None


__all__ = ["AuthContext", "Permission", "SecurityAuditEvent"]
