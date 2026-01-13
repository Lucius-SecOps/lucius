"""Flask application factory."""

from typing import Any

from flask import Flask
from flask_cors import CORS

from shared.logging import get_logger
from talon.api import api_blueprint
from talon.config import config
from talon.extensions import db, migrate

logger = get_logger(__name__)


def create_app(config_override: dict[str, Any] | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_override: Optional configuration overrides

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    app.config["SECRET_KEY"] = config.secret_key
    app.config["DEBUG"] = config.debug
    app.config["SQLALCHEMY_DATABASE_URI"] = config.database.url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": config.database.pool_size,
        "pool_recycle": config.database.pool_recycle,
        "echo": config.database.echo,
    }

    # Apply overrides
    if config_override:
        app.config.update(config_override)

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(api_blueprint, url_prefix="/api/v1")

    # Register health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "talon"}

    # Register error handlers
    register_error_handlers(app)

    logger.info("Talon application initialized")

    return app


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application."""

    @app.errorhandler(400)
    def bad_request(error):
        return {"error": "Bad Request", "message": str(error)}, 400

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not Found", "message": str(error)}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {"error": "Internal Server Error", "message": "An unexpected error occurred"}, 500
