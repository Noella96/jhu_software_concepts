"""
Flask Application Factory for Grad Café Admissions Dashboard.
Module 3 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "jhu-software-concepts-module-3-secret-key"

    from module_3.app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
