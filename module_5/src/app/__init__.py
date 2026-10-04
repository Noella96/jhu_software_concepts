"""
Flask Application Factory for Grad Café Admissions Dashboard.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from flask import Flask


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure the Flask application with optional test configuration overrides.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "jhu-software-concepts-module-4-secret-key"
    app.config["TESTING"] = False

    if config:
        app.config.update(config)

    from src.app.routes import main_bp

    app.register_blueprint(main_bp)

    return app
