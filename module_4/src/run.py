#!/usr/bin/env python3
"""
Application Runner for Grad Café Admissions Analysis Dashboard.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
import os
import sys

# Ensure module_4 root and src are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
for path in (BASE_DIR, PARENT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from src.app import create_app
except ImportError:
    from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[*] Starting Grad Café Admissions Analysis Web Server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
