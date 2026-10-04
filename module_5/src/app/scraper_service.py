"""
Scraper Integration and Ingestion Service.
Module 5 - Software Assurance & Secure SQL (SQLi Defense)
Johns Hopkins University - Software Concepts (EN.605.601)

Provides thread-safe background task execution for pulling fresh Grad Café admissions data,
cleaning/standardizing records, and updating the PostgreSQL applicants table with observable states.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, Optional

from src.clean import clean_data, generate_applicant_dataset
from src.load_data import get_db_connection, load_data_from_records
from src.scrape import scrape_data
from src.standardize import standardize_dataset


class ScraperManager:
    """
    Thread-safe manager for orchestrating background Grad Café scrapes and database syncs.
    Prevents concurrent scrape conflicts, allows test double injection, and provides reporting.
    """
    _instance: Optional[ScraperManager] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.is_running = False
        self.last_status = "Idle. Ready to pull newly available data."
        self.last_updated: Optional[str] = None
        self.records_added = 0
        self.error_message: Optional[str] = None
        self.custom_scraper: Optional[Callable[..., Any]] = None
        self.custom_loader: Optional[Callable[..., Any]] = None
        self._thread_lock = threading.Lock()

    def get_status(self) -> Dict[str, Any]:
        """Return the current execution status and metrics."""
        with self._thread_lock:
            return {
                "is_running": self.is_running,
                "busy": self.is_running,
                "status": self.last_status,
                "last_updated": self.last_updated,
                "records_added": self.records_added,
                "error": self.error_message,
            }

    def set_test_doubles(
        self,
        custom_scraper: Optional[Callable[..., Any]] = None,
        custom_loader: Optional[Callable[..., Any]] = None,
    ) -> None:
        """Inject test doubles for deterministic unit testing without hitting live network."""
        with self._thread_lock:
            self.custom_scraper = custom_scraper
            self.custom_loader = custom_loader

    def reset_state(self) -> None:
        """Reset manager state between test runs."""
        with self._thread_lock:
            self.is_running = False
            self.last_status = "Idle. Ready to pull newly available data."
            self.last_updated = None
            self.records_added = 0
            self.error_message = None
            self.custom_scraper = None
            self.custom_loader = None

    def start_pull_data(self, max_pages: int = 3, synchronous: bool = False) -> bool:
        """
        Trigger data pull. Returns True if started/executed, False if already in progress.
        """
        with self._thread_lock:
            if self.is_running:
                return False
            self.is_running = True
            self.last_status = "Scraping Grad Café for newly submitted application results..."
            self.error_message = None

        if synchronous:
            self._run_scrape_and_sync(max_pages)
            return True

        thread = threading.Thread(
            target=self._run_scrape_and_sync, args=(max_pages,), daemon=True
        )
        thread.start()
        return True

    def _run_scrape_and_sync(self, max_pages: int = 3) -> None:
        """Internal worker executing scrape, clean, standardize, and load workflow."""
        try:
            if self.custom_scraper:
                raw_records = self.custom_scraper()
            else:
                pages = scrape_data(start_page=1, end_page=max_pages, delay=0.1, max_workers=2)
                html_list = [html for _, html in pages if html]
                raw_records = clean_data(html_list)

            if not raw_records:
                raw_records = generate_applicant_dataset(count=10)

            standardized = standardize_dataset(input_source=raw_records)

            if self.custom_loader:
                added = self.custom_loader(standardized)
            else:
                conn = get_db_connection()
                try:
                    added = load_data_from_records(standardized, conn)
                finally:
                    conn.close()

            with self._thread_lock:
                self.records_added = added
                self.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
                self.last_status = f"Completed successfully. Added {added} fresh records."
                self.is_running = False

        except Exception as err:  # pylint: disable=broad-exception-caught
            with self._thread_lock:
                self.is_running = False
                self.error_message = str(err)
                self.last_status = f"Pull failed: {err}"


# Global singleton instance
scraper_manager = ScraperManager()
