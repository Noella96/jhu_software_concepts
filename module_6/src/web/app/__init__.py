"""
Flask Application Factory for Admissions Analytics Dashboard.
Module 6 - Deploy Anywhere Assignment
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
from flask import Flask

try:
    from src.web.app.routes import main_bp
except ImportError:
    from app.routes import main_bp


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure the Flask application with optional configuration overrides.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "gradcafe_super_secret_microservice_key_2026"
    )
    app.config["TESTING"] = False

    if config:
        app.config.update(config)

    app.register_blueprint(main_bp)

    return app
