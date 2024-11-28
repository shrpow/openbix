import enum
from dataclasses import dataclass


class RoleName(enum.StrEnum):
    ADMIN = enum.auto()
    CUSTOMER = enum.auto()


class Permission(enum.IntEnum):
    UPDATE_USERS = enum.auto()
    UPDATE_GAME_ACCOUNTS = enum.auto()


@dataclass
class Role:
    name: str
    permissions: list[Permission]

    def has_permissions(self, permissions: list[Permission]) -> bool:
        return all([permission in self.permissions for permission in permissions])


ROLES = {
    RoleName.ADMIN: Role(
        name=RoleName.ADMIN,
        permissions=[Permission.UPDATE_USERS, Permission.UPDATE_GAME_ACCOUNTS],
    ),
    RoleName.CUSTOMER: Role(
        name=RoleName.CUSTOMER,
        permissions=[Permission.UPDATE_GAME_ACCOUNTS],
    ),
}
