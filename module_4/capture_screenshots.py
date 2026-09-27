"""
Automated Deliverable Screenshot Generator for Module 3.
Module 3 - Johns Hopkins University Software Concepts (EN.605.601)

Generates:
1. screenshot_sql.png: High-resolution rendered image of raw SQL terminal execution output.
2. screenshot_orm.png: High-resolution rendered image of SQLAlchemy ORM terminal execution output.
3. screenshot_flask.png: Full-page browser screenshot of the live Flask analysis dashboard.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PIL import Image, ImageDraw, ImageFont


def render_terminal_screenshot(text_content: str, output_path: str, title: str = "Terminal Output") -> None:
    """
    Render realistic dark-mode developer terminal screenshot with window chrome and syntax accents.
    """
    # Base dimensions
    width = 1100
    lines = text_content.strip().split("\n")
    line_height = 20
    header_height = 45
    padding = 25
    height = header_height + (len(lines) * line_height) + (padding * 2)

    img = Image.new("RGB", (width, height), color="#0f172a")  # Dark slate background
    draw = ImageDraw.Draw(img)

    # Window Header Bar
    draw.rectangle([(0, 0), (width, header_height)], fill="#1e293b")
    draw.line([(0, header_height), (width, header_height)], fill="#334155", width=1)

    # macOS window buttons
    draw.ellipse([(18, 16), (30, 28)], fill="#ef4444")  # Red
    draw.ellipse([(38, 16), (50, 28)], fill="#f59e0b")  # Yellow
    draw.ellipse([(58, 16), (70, 28)], fill="#10b981")  # Green

    # Window Title
    try:
        font_header = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
        font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.dfont", 12)
    except Exception:
        font_header = ImageFont.load_default()
        font_mono = ImageFont.load_default()

    draw.text((width // 2 - 100, 15), title, fill="#94a3b8", font=font_header)

    # Draw lines with simple color coding
    y = header_height + padding
    for line in lines:
        if line.startswith("="):
            color = "#64748b"
        elif line.startswith("[Question") or line.startswith("[+]"):
            color = "#38bdf8"  # Light blue
        elif "count:" in line.lower() or "average" in line.lower() or "percent" in line.lower() or "difference:" in line.lower():
            color = "#4ade80"  # Green
        elif line.strip().startswith("-"):
            color = "#f1f5f9"  # White
        else:
            color = "#cbd5e1"  # Light gray

        draw.text((padding, y), line, fill=color, font=font_mono)
        y += line_height

    img.save(output_path, "PNG")
    print(f"[+] Saved screenshot to {output_path}")


def capture_flask_webpage_screenshot(output_path: str, port: int = 8089) -> None:
    """
    Launch Flask in a daemon thread and capture browser screenshot using headless Selenium.
    """
    import threading
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from werkzeug.serving import make_server
    from module_3.app import create_app

    flask_app = create_app()
    server = make_server("127.0.0.1", port, flask_app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(1)

    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1440,1100")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"http://127.0.0.1:{port}/")
        time.sleep(2)
        driver.save_screenshot(output_path)
        driver.quit()
        print(f"[+] Captured Flask webpage screenshot: {output_path}")
    finally:
        server.shutdown()


def main():
    import sys
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Capture Raw SQL Output
    res_sql = subprocess.run(
        [sys.executable, os.path.join(base_dir, "query_data.py")],
        capture_output=True,
        text=True,
        check=True
    )
    render_terminal_screenshot(
        res_sql.stdout,
        os.path.join(base_dir, "screenshot_sql.png"),
        title="zsh - python module_3/query_data.py"
    )

    # 2. Capture ORM Output
    res_orm = subprocess.run(
        [sys.executable, os.path.join(base_dir, "orm_queries.py")],
        capture_output=True,
        text=True,
        check=True
    )
    render_terminal_screenshot(
        res_orm.stdout,
        os.path.join(base_dir, "screenshot_orm.png"),
        title="zsh - python module_3/orm_queries.py"
    )

    # 3. Capture Flask Dashboard Screenshot
    try:
        capture_flask_webpage_screenshot(os.path.join(base_dir, "screenshot_flask.png"), port=8088)
    except Exception as e:
        print(f"[-] Selenium browser screenshot error: {e}")


if __name__ == "__main__":
    import sys
    main()
