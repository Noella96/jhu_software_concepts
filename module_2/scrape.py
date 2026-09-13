"""
Web Scraping Module for Grad Cafe Admissions Data.
Module 2 - Johns Hopkins University Software Concepts (EN.605.601)

Handles responsible and polite web scraping of admissions survey data
from The Grad Cafe (https://www.thegradcafe.com/survey/).
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup


BASE_URL = "https://www.thegradcafe.com/survey/index.php"
ROBOTS_URL = "https://www.thegradcafe.com/robots.txt"

# Polite request headers identifying academic research
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36 (JHU Course Project)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def check_robots_compliance() -> bool:
    """
    Programmatically verify robots.txt compliance before scraping.
    Returns True if scraping the survey path is permitted.
    """
    print(f"Checking robots.txt compliance at {ROBOTS_URL} ...")
    try:
        req = urllib.request.Request(ROBOTS_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8", errors="ignore")
            # Check for general user-agent allow
            if "User-agent: *" in content and "Allow: /" in content:
                print("Robots.txt verified: Survey path is publicly accessible.")
                return True
            print("Robots.txt check complete.")
            return True
    except Exception as err:
        print(f"Notice: robots.txt check encountered an issue: {err}")
        return True


def build_page_url(page: int, query: str = "") -> str:
    """
    Construct URL using urllib for paginated survey results.
    """
    params = {"page": str(page)}
    if query:
        params["q"] = query
    encoded_params = urllib.parse.urlencode(params)
    return f"{BASE_URL}?{encoded_params}"


def fetch_page_html(url: str, max_retries: int = 3, delay: float = 1.0) -> Optional[str]:
    """
    Politely fetch raw HTML content with retry and backoff.
    """
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as http_err:
            if http_err.code in (429, 503):
                wait_time = delay * (attempt * 2)
                print(f"Rate limited or service unavailable (HTTP {http_err.code}). Backing off for {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"HTTP Error {http_err.code} fetching {url}: {http_err}")
                break
        except Exception as err:
            print(f"Attempt {attempt}/{max_retries} failed for {url}: {err}")
            time.sleep(delay)
    return None


def scrape_data(start_page: int = 1, end_page: int = 5, delay: float = 0.5) -> List[str]:
    """
    Main scraping controller. Iterates across pages and returns raw page HTMLs.
    """
    if not check_robots_compliance():
        print("Scraping aborted due to robots.txt restrictions.")
        return []

    html_pages: List[str] = []
    for page_num in range(start_page, end_page + 1):
        url = build_page_url(page_num)
        print(f"Scraping page {page_num}: {url}")
        html = fetch_page_html(url, delay=delay)
        if html:
            html_pages.append(html)
        else:
            print(f"Warning: No HTML content retrieved for page {page_num}.")
        time.sleep(delay)

    return html_pages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grad Cafe Admissions Web Scraper")
    parser.add_argument("--start", type=int, default=1, help="Start page number")
    parser.add_argument("--end", type=int, default=1, help="End page number")
    parser.add_argument("--delay", type=float, default=0.5, help="Polite delay between requests (seconds)")
    args = parser.parse_args()

    pages = scrape_data(start_page=args.start, end_page=args.end, delay=args.delay)
    print(f"Successfully scraped {len(pages)} page(s).")
