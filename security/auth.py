from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    USER = "USER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    role: Role


class Authorization:
    def require(self, principal: Principal, *allowed: Role) -> None:
        if principal.role not in allowed:
            raise PermissionError(f"role {principal.role} is not authorized")
