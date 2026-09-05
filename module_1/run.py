"""
Entry point for starting the Module 1 Flask web application.
Runs on host 0.0.0.0 and port 8080 as specified by project requirements.
"""
import sys
import os

# Add module_1 directory to Python path if running directly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting Module 1 Web Application on http://0.0.0.0:8080 ...")
    app.run(host="0.0.0.0", port=8080, debug=True)
