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

    # Blueprints will be imported and registered here in Step 3
    # from app.routes.pages import pages_bp
    # app.register_blueprint(pages_bp)

    @app.route("/")
    def index():
        return "<h1>Module 1 Web Application Running</h1>"

    return app

