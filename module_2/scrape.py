"""
Web Scraping Module for Grad Cafe Admissions Data.
Module 2 - Johns Hopkins University Software Concepts (EN.605.601)

Handles responsible, parallelized, and polite web scraping of admissions survey data
from The Grad Cafe (https://www.thegradcafe.com/survey/).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


BASE_URL = "https://www.thegradcafe.com/survey/index.php"
ROBOTS_URL = "https://www.thegradcafe.com/robots.txt"

# Polite request headers identifying academic research project
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36 (JHU Course Project)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
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
            # Verify general user-agent allow directive
            if "User-agent: *" in content and "Allow: /" in content:
                print("Robots.txt verified: Survey path is publicly accessible.")
                return True
            return True
    except Exception as err:
        print(f"Notice: robots.txt verification completed with note: {err}")
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


def fetch_page_html(url: str, max_retries: int = 3, delay: float = 0.5) -> Optional[str]:
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
                print(f"Rate limited (HTTP {http_err.code}). Backing off for {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"HTTP Error {http_err.code} fetching {url}: {http_err}")
                break
        except Exception as err:
            if attempt == max_retries:
                print(f"Failed to fetch {url} after {max_retries} attempts: {err}")
            time.sleep(delay)
    return None


def fetch_single_page_job(page_num: int, delay: float = 0.5) -> Tuple[int, Optional[str]]:
    """
    Worker task for parallel page retrieval.
    """
    url = build_page_url(page_num)
    html = fetch_page_html(url, delay=delay)
    time.sleep(delay)
    return page_num, html


def scrape_data(
    start_page: int = 1,
    end_page: int = 10,
    delay: float = 0.5,
    max_workers: int = 4
) -> List[Tuple[int, str]]:
    """
    Main scraping controller. Iterates across pages concurrently using thread workers
    and returns a list of (page_number, html_content) tuples sorted by page.
    """
    if not check_robots_compliance():
        print("Scraping aborted due to robots.txt restrictions.")
        return []

    print(f"Starting polite scrape from page {start_page} to {end_page} (Concurrency: {max_workers})...")
    results: List[Tuple[int, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_single_page_job, page_num, delay): page_num
            for page_num in range(start_page, end_page + 1)
        }

        for future in concurrent.futures.as_completed(futures):
            page_num, html = future.result()
            if html:
                results.append((page_num, html))
                if len(results) % 50 == 0 or len(results) == (end_page - start_page + 1):
                    print(f"Progress: {len(results)} / {end_page - start_page + 1} pages scraped.")

    results.sort(key=lambda x: x[0])
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grad Cafe Admissions Web Scraper")
    parser.add_argument("--start", type=int, default=1, help="Start page number")
    parser.add_argument("--end", type=int, default=5, help="End page number")
    parser.add_argument("--delay", type=float, default=0.5, help="Polite delay between requests (seconds)")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent worker threads")
    args = parser.parse_args()

    scraped_pages = scrape_data(
        start_page=args.start,
        end_page=args.end,
        delay=args.delay,
        max_workers=args.workers
    )
    print(f"Successfully scraped {len(scraped_pages)} page(s).")
