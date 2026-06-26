from app.auth.permissions import Role
from app.auth.rbac import get_user_by_email, normalize_email
from app.extensions import db
from app.models import RoleAssignment, User


def list_users() -> list[User]:
    return User.query.order_by(User.email.asc()).all()


def create_or_update_user(email: str, roles: list[str], *, is_active: bool = True) -> User:
    email = normalize_email(email)
    valid_roles = {Role.SCANNER.value, Role.ADMIN.value, Role.SUPERADMIN.value}
    role_set = {role for role in roles if role in valid_roles}

    user = get_user_by_email(email)
    if user is None:
        user = User(email=email, is_active=is_active)
        db.session.add(user)
        db.session.flush()
    else:
        user.is_active = is_active
        RoleAssignment.query.filter_by(user_id=user.id).delete()

    for role_name in sorted(role_set):
        db.session.add(RoleAssignment(user_id=user.id, role=role_name))

    db.session.commit()
    db.session.refresh(user)
    return user


def delete_user(user_id: int) -> bool:
    user = db.session.get(User, user_id)
    if user is None:
        return False
    db.session.delete(user)
    db.session.commit()
    return True
