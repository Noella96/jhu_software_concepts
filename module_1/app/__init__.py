"""
Flask Application Factory for Module 1 Personal Website.
"""
from flask import Flask


def create_app() -> Flask:
    """
    Construct the core application and register blueprints.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static"
    )

    # Configure application settings
    app.config["SECRET_KEY"] = "jhu-software-concepts-secret-key"

    # Register sub-pages blueprint
    from app.routes.pages import pages_bp
    app.register_blueprint(pages_bp)

    return app
