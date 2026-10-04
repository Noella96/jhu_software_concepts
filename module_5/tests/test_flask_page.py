"""
Flask Web Page and Route Rendering Unit Tests.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

import re
import pytest
from bs4 import BeautifulSoup

from src.app import create_app


@pytest.mark.web
def test_app_factory_and_routes_registration():
    """
    Test app factory creates configured Flask app with all expected routes.
    """
    app = create_app({"TESTING": True, "CUSTOM_TEST_VAR": "enabled"})
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["CUSTOM_TEST_VAR"] == "enabled"

    # Check registered route endpoints
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert "/" in rules
    assert "/analysis" in rules
    assert "/pull-data" in rules
    assert "/update-analysis" in rules
    assert "/api/status" in rules


@pytest.mark.web
def test_get_analysis_page_load(client):
    """
    Test GET /analysis loads with status 200 and required elements.
    """
    response = client.get("/analysis")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")

    # Verify page text includes 'Analysis'
    assert "Analysis" in soup.get_text()

    # Verify both 'Pull Data' and 'Update Analysis' buttons exist
    pull_btn = soup.find(attrs={"data-testid": "pull-data-btn"}) or soup.find("button", string=re.compile(r"Pull\s*Data", re.I))
    assert pull_btn is not None, "Pull Data button not found on page"
    assert "Pull Data" in pull_btn.get_text()

    update_btn = soup.find(attrs={"data-testid": "update-analysis-btn"}) or soup.find("button", string=re.compile(r"Update\s*Analysis", re.I))
    assert update_btn is not None, "Update Analysis button not found on page"
    assert "Update Analysis" in update_btn.get_text()

    # Verify at least one 'Answer:' label is rendered
    assert "Answer:" in html, "Page must include at least one 'Answer:' label"


@pytest.mark.web
def test_get_root_page_load(client):
    """
    Test GET / root route alias loads analysis dashboard with status 200.
    """
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Grad Café Admissions Analysis" in html
    assert "data-testid=\"pull-data-btn\"" in html
    assert "data-testid=\"update-analysis-btn\"" in html
    assert "Answer:" in html
