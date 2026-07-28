from flask import Flask

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from app.config import Config, validate_config
from app.extensions import db, migrate
from app.auth.google_auth import bp as google_auth_bp
from app.routes.main import bp as main_bp
from app.api.v1.routes import bp as api_v1_bp
from app.routes.spa import bp as spa_bp


def create_app(config_class=Config):
    # static_url_path must not be "" — Flask's /<path:filename> route would
    # intercept SPA paths like /admin and 404 before the catch-all runs.
    app = Flask(__name__, static_folder="static", static_url_path="/__static__")
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(google_auth_bp)
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(spa_bp)

    validate_config(app)

    return app
