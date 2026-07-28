from flask import current_app

from app.auth.permissions import Role, roles_for_permission
from app.extensions import db
from app.models import AllowedEmail, BlacklistedEmail, User


class AuthContext:
    __slots__ = ("email", "roles", "auth_method")

    def __init__(self, email: str, roles: set[str], auth_method: str):
        self.email = email
        self.roles = roles
        self.auth_method = auth_method

    def has_permission(self, permission: str) -> bool:
        allowed = roles_for_permission(permission)
        if not allowed:
            return False
        allowed_names = {r.value for r in allowed}
        return bool(allowed_names & self.roles)

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "roles": sorted(self.roles),
            "auth_method": self.auth_method,
        }


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(email: str) -> User | None:
    return User.query.filter(User.email.ilike(normalize_email(email))).first()


def resolve_roles_for_email(email: str) -> set[str]:
    email = normalize_email(email)
    roles: set[str] = set()

    superadmin = current_app.config.get("SUPERADMIN_EMAIL", "").strip().lower()
    if superadmin and email == superadmin:
        roles.add(Role.SUPERADMIN.value)

    user = get_user_by_email(email)
    if user and user.is_active:
        roles.update(user.role_names())

    return roles


def is_blacklisted(email: str) -> bool:
    normalized = normalize_email(email)
    return (
        BlacklistedEmail.query.filter(BlacklistedEmail.email.ilike(normalized)).first()
        is not None
    )


def is_on_allowlist(email: str) -> bool:
    normalized = normalize_email(email)
    return (
        AllowedEmail.query.filter(AllowedEmail.email.ilike(normalized)).first()
        is not None
    )


def is_attendee(email: str) -> bool:
    """True if the user may receive a ticket (allowlisted and not blacklisted)."""
    if is_blacklisted(email):
        return False
    return is_on_allowlist(email)


def ensure_user_with_roles(email: str, roles: list[Role]) -> User:
    email = normalize_email(email)
    user = get_user_by_email(email)
    if user is None:
        user = User(email=email)
        db.session.add(user)
    user.is_active = True
    for role in roles:
        user.grant_role(role)
    db.session.commit()
    return user
