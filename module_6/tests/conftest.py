"""
Pytest Fixtures and Test Setup for Grad Café Microservice Stack.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List
from unittest.mock import MagicMock
import pytest

# Ensure module_6 and service directories are in sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(TESTS_DIR)
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from src.web.app import create_app  # pylint: disable=wrong-import-position


@pytest.fixture
def app():
    """Create a testable Flask application instance with testing enabled."""
    test_app = create_app({"TESTING": True, "SECRET_KEY": "test-key-2026"})
    return test_app


@pytest.fixture
def client(app):  # pylint: disable=redefined-outer-name
    """Provide Flask test client for making simulated HTTP requests."""
    return app.test_client()


@pytest.fixture
def mock_pika_channel():
    """Provide a mock pika channel with recorded publish calls."""
    mock_ch = MagicMock()
    mock_ch.is_open = True
    return mock_ch


@pytest.fixture
def mock_pika_connection(mock_pika_channel):  # pylint: disable=redefined-outer-name
    """Provide a mock pika BlockingConnection."""
    mock_conn = MagicMock()
    mock_conn.channel.return_value = mock_pika_channel
    mock_conn.is_open = True
    return mock_conn


@pytest.fixture
def sample_records() -> List[Dict[str, Any]]:
    """Provide sample structured applicant records for testing."""
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
            "llm_generated_university": "Johns Hopkins University",
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
            "GPA": "GPA 3.88",
            "gpa": 3.88,
            "GRE": "GRE 165",
            "gre": 165.0,
            "GRE V": "GRE V 160",
            "gre_v": 160.0,
            "GRE AW": "GRE AW 4.5",
            "gre_aw": 4.5,
            "Degree": "PhD",
            "degree": "PhD",
            "llm-generated-program": "Computer Science",
            "llm_generated_program": "Computer Science",
            "llm-generated-university": "Stanford University",
            "llm_generated_university": "Stanford University",
        },
    ]
