#!/usr/bin/env python3
"""
Application Runner for Grad Café Admissions Analysis Dashboard.
Module 3 - Johns Hopkins University Software Concepts (EN.605.601)
"""
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from module_3.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[*] Starting Grad Café Admissions Analysis Web Server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
