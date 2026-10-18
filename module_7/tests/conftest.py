"""
Pytest configuration and test fixtures for Module 7 test suite.
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List
import pytest


@pytest.fixture
def sample_applicant_records() -> List[Dict[str, Any]]:
    """Fixture providing valid applicant records for pipeline testing."""
    return [
        {
            "p_id": 935454,
            "program": "Computer Science, Johns Hopkins University",
            "comments": "Accepted into MS CS with funding",
            "date_added": "Added on March 31, 2026",
            "url": "https://www.thegradcafe.com/result/935454",
            "status": "Accepted",
            "term": "Fall 2026",
            "us_or_international": "American",
            "gpa": 3.92,
            "gre": 168.0,
            "gre_v": 162.0,
            "gre_aw": 4.5,
            "degree": "Masters",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Johns Hopkins University",
        },
        {
            "p_id": 935455,
            "program": "Electrical Engineering, MIT",
            "comments": "PhD applicant",
            "date_added": "Added on March 30, 2026",
            "url": "https://www.thegradcafe.com/result/935455",
            "status": "Accepted",
            "term": "Fall 2026",
            "us_or_international": "International",
            "gpa": 3.88,
            "gre": 170.0,
            "gre_v": 160.0,
            "gre_aw": 5.0,
            "degree": "PhD",
            "llm_generated_program": "Electrical Engineering",
            "llm_generated_university": "Massachusetts Institute of Technology",
        },
    ]


@pytest.fixture
def sample_json_file(tmp_path, sample_applicant_records):  # pylint: disable=redefined-outer-name
    """Fixture providing a temporary valid JSON dataset file."""
    fpath = tmp_path / "sample_applicant_data.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(sample_applicant_records, f)
    return str(fpath)
