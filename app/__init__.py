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
from app.routes.admin import bp as admin_bp
from app.api.v1.routes import bp as api_v1_bp


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(google_auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_v1_bp)

    validate_config(app)

    return app
