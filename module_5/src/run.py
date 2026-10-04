#!/usr/bin/env python3
"""
Application Runner for Grad Café Admissions Analysis Dashboard.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
import os
import sys

from src.app import create_app

app = create_app()


def main() -> None:
    """Run the Flask dashboard development server."""
    port = int(os.environ.get("PORT", 8080))
    print(f"[*] Starting Grad Café Admissions Analysis Web Server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
