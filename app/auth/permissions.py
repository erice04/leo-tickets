import enum


class Role(str, enum.Enum):
    SCANNER = "scanner"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


# Permission -> roles that grant it
PERMISSIONS: dict[str, frozenset[Role]] = {
    "event:read": frozenset({Role.ADMIN, Role.SUPERADMIN, Role.SCANNER}),
    "event:write": frozenset({Role.ADMIN, Role.SUPERADMIN}),
    "allowlist:read": frozenset({Role.ADMIN, Role.SUPERADMIN}),
    "allowlist:write": frozenset({Role.ADMIN, Role.SUPERADMIN}),
    "scans:read": frozenset({Role.ADMIN, Role.SUPERADMIN, Role.SCANNER}),
    "scans:write": frozenset({Role.ADMIN, Role.SUPERADMIN, Role.SCANNER}),
    "scans:manage": frozenset({Role.ADMIN, Role.SUPERADMIN}),
    "users:read": frozenset({Role.SUPERADMIN}),
    "users:write": frozenset({Role.SUPERADMIN}),
    "database:read": frozenset({Role.ADMIN, Role.SUPERADMIN}),
}


def roles_for_permission(permission: str) -> frozenset[Role]:
    return PERMISSIONS.get(permission, frozenset())
