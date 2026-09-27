"""
Pytest Fixtures and Test Setup for Grad Café Analysis System.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, Generator, List
import pytest

# Ensure module_4 and module_4/src are in sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(TESTS_DIR)
SRC_DIR = os.path.join(MODULE_DIR, "src")
for path in (MODULE_DIR, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from src.app import create_app
from src.app.scraper_service import scraper_manager
from src.models import Applicant, Base, get_db_session, get_engine


@pytest.fixture(autouse=True)
def reset_scraper_state():
    """
    Ensure scraper manager singleton is reset before and after every single test.
    """
    scraper_manager.reset_state()
    yield
    scraper_manager.reset_state()


@pytest.fixture
def app():
    """
    Create a testable Flask application instance with testing enabled.
    """
    test_app = create_app({"TESTING": True, "SECRET_KEY": "test-key"})
    return test_app


@pytest.fixture
def client(app):
    """
    Provide Flask test client for making simulated HTTP requests.
    """
    return app.test_client()


@pytest.fixture
def db_session() -> Generator:
    """
    Provide a transactional database session for tests.
    """
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_records() -> List[Dict[str, Any]]:
    """
    Provide sample structured applicant records for testing.
    """
    return [
        {
            "p_id": 999901,
            "program": "Computer Science, Johns Hopkins University ",
            "comments": "Admitted with fellowship",
            "date_added": "Added on March 15, 2026",
            "url": "https://www.thegradcafe.com/result/999901",
            "status": "Accepted on 15 Mar",
            "term": "Fall 2026",
            "US/International": "American",
            "us_or_international": "American",
            "GPA": "GPA 3.92",
            "gpa": 3.92,
            "GRE": "GRE 168",
            "gre": 168.0,
            "GRE V": "GRE V 162",
            "gre_v": 162.0,
            "GRE AW": "GRE AW 5.0",
            "gre_aw": 5.0,
            "Degree": "Masters",
            "degree": "Masters",
            "llm-generated-program": "Computer Science",
            "llm_generated_program": "Computer Science",
            "llm-generated-university": "Johns Hopkins University",
            "llm_generated_university": "Johns Hopkins University"
        },
        {
            "p_id": 999902,
            "program": "Computer Science, Stanford University ",
            "comments": "Interview went well",
            "date_added": "Added on February 20, 2026",
            "url": "https://www.thegradcafe.com/result/999902",
            "status": "Accepted on 20 Feb",
            "term": "Fall 2026",
            "US/International": "International",
            "us_or_international": "International",
            "GPA": "GPA 3.85",
            "gpa": 3.85,
            "GRE": "GRE 169",
            "gre": 169.0,
            "GRE V": "GRE V 160",
            "gre_v": 160.0,
            "GRE AW": "GRE AW 4.5",
            "gre_aw": 4.5,
            "Degree": "PhD",
            "degree": "PhD",
            "llm-generated-program": "Computer Science",
            "llm_generated_program": "Computer Science",
            "llm-generated-university": "Stanford University",
            "llm_generated_university": "Stanford University"
        }
    ]
