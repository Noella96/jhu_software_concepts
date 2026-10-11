"""
Web Service Entrypoint for Admissions Analytics Dashboard.
Module 6 - Deploy Anywhere Assignment
Johns Hopkins University - Software Concepts (EN.605.601)
"""
import os

try:
    from app import create_app
except ImportError:
    from src.web.app import create_app

app = create_app()


def main() -> None:
    """Run Flask application binding to 0.0.0.0:8080."""
    port = int(os.environ.get("PORT", "8080"))
    print(f"[*] Starting Grad Café Admissions Analysis Web Service on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
