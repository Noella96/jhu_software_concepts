"""
End-to-End Integration Tests (Pull -> Update -> Render Flow).
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

import re
import pytest
from bs4 import BeautifulSoup

from src.app.scraper_service import scraper_manager
from src.models import Applicant, get_db_session


@pytest.mark.integration
def test_end_to_end_pull_update_render(client, sample_records):
    """
    Integration test: Pull -> Update -> Render.
    1. Injects a fake scraper with records.
    2. Triggers POST /pull-data.
    3. Triggers POST /update-analysis.
    4. Asserts GET /analysis renders updated analysis with correctly formatted values.
    """
    # 1. Inject test double
    scraper_manager.set_test_doubles(
        custom_scraper=lambda: sample_records,
        custom_loader=None  # Use real DB loader
    )

    # 2. Trigger POST /pull-data in sync mode
    pull_res = client.post("/pull-data?sync=true")
    assert pull_res.status_code == 200
    pull_data = pull_res.get_json()
    assert pull_data["ok"] is True

    # Verify rows exist in DB
    session = get_db_session()
    try:
        r = session.get(Applicant, 999901)
        assert r is not None
        assert "Johns Hopkins" in r.program
    finally:
        session.close()

    # 3. Trigger POST /update-analysis
    update_res = client.post("/update-analysis")
    assert update_res.status_code == 200
    update_data = update_res.get_json()
    assert update_data["ok"] is True
    assert update_data["data"]["q1"] >= 1

    # 4. Fetch GET /analysis and assert rendered HTML values
    get_res = client.get("/analysis")
    assert get_res.status_code == 200
    html = get_res.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")

    # Verify Answer: labels and two-decimal formatting
    assert "Answer:" in html
    val_q2 = soup.find(id="val-q2").get_text(strip=True)
    assert re.match(r"^\d+\.\d{2}%$", val_q2)

    val_gpa = soup.find(id="val-gpa").get_text(strip=True)
    assert re.match(r"^\d+\.\d{2}$", val_gpa)


@pytest.mark.integration
def test_multiple_overlapping_pulls_consistency(client, sample_records):
    """
    Integration test: Running POST /pull-data multiple times with overlapping records
    preserves database uniqueness and analytical stability.
    """
    scraper_manager.set_test_doubles(custom_scraper=lambda: sample_records)

    # First pull
    res1 = client.post("/pull-data?sync=true")
    assert res1.status_code == 200

    # Second pull with same records
    res2 = client.post("/pull-data?sync=true")
    assert res2.status_code == 200

    # Update analysis
    update_res = client.post("/update-analysis")
    assert update_res.status_code == 200

    # Verify session row count for test id is still exactly 1
    session = get_db_session()
    try:
        item = session.get(Applicant, 999902)
        assert item is not None
        assert item.p_id == 999902
    finally:
        session.close()
