import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://leo:leo@localhost:5432/leo_tickets",
    )
    # Render/Heroku-style URLs use postgres://; SQLAlchemy 2.x expects postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_AUTH_REDIRECT_URI = os.environ.get(
        "GOOGLE_AUTH_REDIRECT_URI", "http://localhost:5000/google/auth"
    )
    BASE_URI = os.environ.get("BASE_URI", "http://localhost:5000/")

    SUPERADMIN_EMAIL = os.environ.get("SUPERADMIN_EMAIL", "")

    SCAN_DEDUP_SECONDS = int(os.environ.get("SCAN_DEDUP_SECONDS", "60"))

    SCANNER_API_KEY = os.environ.get("SCANNER_API_KEY", "")
    ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")


def validate_config(app) -> None:
    """Refuse to start in production without required secrets."""
    if os.environ.get("FLASK_DEBUG", "0") == "1":
        return
    if os.environ.get("ALLOW_INSECURE_CONFIG") == "1":
        return

    is_production = bool(
        os.environ.get("RENDER")
        or os.environ.get("RAILWAY_ENVIRONMENT")
        or os.environ.get("FLASK_ENV") == "production"
    )
    if not is_production:
        return

    missing = []
    if not app.config.get("SECRET_KEY") or app.config["SECRET_KEY"] == "dev-secret-change-in-production":
        missing.append("SECRET_KEY")
    if not app.config.get("GOOGLE_CLIENT_ID"):
        missing.append("GOOGLE_CLIENT_ID")
    if not app.config.get("GOOGLE_CLIENT_SECRET"):
        missing.append("GOOGLE_CLIENT_SECRET")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        missing.append("DATABASE_URL")

    if missing:
        raise RuntimeError(
            "Missing required production environment variables: " + ", ".join(missing)
        )
