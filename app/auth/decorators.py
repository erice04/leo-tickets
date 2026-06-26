from functools import wraps

from flask import current_app, g, jsonify, redirect, render_template, request, url_for

from app.auth import google_auth
from app.auth.permissions import Role
from app.auth.rbac import AuthContext, normalize_email, resolve_roles_for_email


def _api_key_roles() -> set[str] | None:
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    scanner_key = current_app.config.get("SCANNER_API_KEY", "")
    admin_key = current_app.config.get("ADMIN_API_KEY", "")

    if not api_key:
        return None
    if scanner_key and api_key == scanner_key:
        return {Role.SCANNER.value}
    if admin_key and api_key == admin_key:
        return {Role.ADMIN.value, Role.SCANNER.value}
    return None


def get_auth_context() -> AuthContext | None:
    if hasattr(g, "auth_context"):
        return g.auth_context

    api_roles = _api_key_roles()
    if api_roles:
        g.auth_context = AuthContext(
            email="api-key",
            roles=api_roles,
            auth_method="api_key",
        )
        return g.auth_context

    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        email = normalize_email(user_info["email"])
        roles = resolve_roles_for_email(email)
        g.auth_context = AuthContext(email=email, roles=roles, auth_method="session")
        return g.auth_context

    g.auth_context = None
    return None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not google_auth.is_logged_in():
            return redirect(url_for("google_auth.login"), code=302)
        return view(*args, **kwargs)

    return wrapper


def permission_required(permission: str, *, api: bool = False):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            ctx = get_auth_context()
            if ctx is None:
                if api:
                    return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}), 401
                return render_template("general_error.html")
            if not ctx.has_permission(permission):
                if api:
                    return jsonify({"error": {"code": "FORBIDDEN", "message": "Insufficient permissions"}}), 403
                return render_template("general_error.html")
            return view(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not google_auth.is_logged_in():
            return redirect(url_for("google_auth.login"), code=302)
        ctx = get_auth_context()
        if ctx is None or not ctx.has_permission("event:write"):
            return render_template("general_error.html")
        return view(*args, **kwargs)

    return wrapper


def api_auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if get_auth_context() is None:
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}), 401
        return view(*args, **kwargs)

    return wrapper
