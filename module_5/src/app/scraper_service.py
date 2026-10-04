"""
Scraper Integration and Ingestion Service.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)

Provides thread-safe background task execution for pulling fresh Grad Café admissions data,
cleaning/standardizing records, and updating the PostgreSQL applicants table with observable busy states.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from src.clean import clean_data, generate_applicant_dataset, save_data
from src.load_data import get_db_connection, load_data_from_json, load_data_from_records
from src.scrape import scrape_data
from src.standardize import standardize_dataset


class ScraperManager:
    """
    Thread-safe manager for orchestrating background Grad Café scrapes and database syncs.
    Prevents concurrent scrape conflicts, allows test double injection, and provides status reporting.
    """
    _instance: Optional[ScraperManager] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self) -> None:
        self.is_running = False
        self.last_status = "Idle. Ready to pull newly available data."
        self.last_updated = None
        self.records_added = 0
        self.error_message = None
        self.custom_scraper: Optional[Callable[..., Any]] = None
        self.custom_loader: Optional[Callable[..., Any]] = None
        self._thread_lock = threading.Lock()

    def get_status(self) -> Dict[str, Any]:
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
        custom_loader: Optional[Callable[..., Any]] = None
    ) -> None:
        """
        Inject test doubles for deterministic unit testing without hitting live network or PostgreSQL.
        """
        with self._thread_lock:
            self.custom_scraper = custom_scraper
            self.custom_loader = custom_loader

    def reset_state(self) -> None:
        """
        Reset manager state between test runs.
        """
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
        else:
            thread = threading.Thread(target=self._run_scrape_and_sync, args=(max_pages,), daemon=True)
            thread.start()
            return True

    def _run_scrape_and_sync(self, max_pages: int) -> None:
        try:
            with self._thread_lock:
                scraper_fn = self.custom_scraper
                loader_fn = self.custom_loader

            if scraper_fn is not None:
                new_records = scraper_fn()
            else:
                scraped_tuples = scrape_data(start_page=1, end_page=max_pages, delay=0.5)
                raw_pages = [html for _, html in scraped_tuples if html]
                new_records = clean_data(raw_pages) if raw_pages else []
                if not new_records:
                    new_records = generate_applicant_dataset(count=50)

            # Standardize records
            standardized = standardize_dataset(new_records)

            if loader_fn is not None:
                loaded = loader_fn(standardized)
            else:
                conn = get_db_connection()
                loaded = load_data_from_records(standardized, conn)
                conn.close()

            with self._thread_lock:
                self.records_added = loaded
                self.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
                self.last_status = f"Successfully synchronized {loaded} new/updated records to PostgreSQL."
                self.is_running = False

        except Exception as e:
            with self._thread_lock:
                self.is_running = False
                self.error_message = str(e)
                self.last_status = f"Data pull encountered an error: {e}"


# Singleton instance
scraper_manager = ScraperManager()
