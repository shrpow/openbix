from backend.user.core.role import ROLES, Permission
from backend.user.dto import UserDTO


class InsufficientPermissionsError(Exception):
    ...


class AuthzService:
    def check_permissions(self, user: UserDTO, permissions: list[Permission]):
        if not ROLES[user.role].has_permissions(permissions=permissions):
            raise InsufficientPermissionsError(f"{user=} {permissions=}")
