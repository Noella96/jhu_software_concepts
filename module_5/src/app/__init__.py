"""
Flask Application Factory for Grad Café Admissions Dashboard.
Module 5 - Software Assurance & Secure SQL (SQLi Defense)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
from flask import Flask

from src.app.routes import main_bp


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure the Flask application with optional configuration overrides.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "jhu-software-concepts-module-5-secret-key"
    )
    app.config["TESTING"] = False

    if config:
        app.config.update(config)

    app.register_blueprint(main_bp)

    return app
