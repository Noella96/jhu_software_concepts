"""
Button Behavior and Busy-State Gating Unit Tests.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

import json
import pytest

from src.app.scraper_service import scraper_manager


@pytest.mark.buttons
def test_post_pull_data_idle_success(client, sample_records):
    """
    Test POST /pull-data returns 200/202 with {"ok": true} and triggers mocked loader.
    """
    loader_called = []

    def fake_scraper():
        return sample_records

    def fake_loader(records):
        loader_called.append(len(records))
        return len(records)

    scraper_manager.set_test_doubles(custom_scraper=fake_scraper, custom_loader=fake_loader)

    # Use synchronous mode query param or json to execute deterministically in test
    response = client.post("/pull-data?sync=true")
    assert response.status_code in (200, 202)
    data = response.get_json()
    assert data["ok"] is True
    assert data["busy"] is False
    assert len(loader_called) == 1
    assert loader_called[0] == 2


@pytest.mark.buttons
def test_post_update_analysis_idle_success(client):
    """
    Test POST /update-analysis returns 200 when not busy.
    """
    response = client.post("/update-analysis")
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["busy"] is False
    assert "data" in data
    assert "q1" in data["data"]


@pytest.mark.buttons
def test_busy_gating_update_analysis(client):
    """
    Test that when a pull is in progress, POST /update-analysis returns 409 {"busy": true}.
    """
    # Simulate active pull state via observable manager without arbitrary sleep()
    with scraper_manager._thread_lock:
        scraper_manager.is_running = True
        scraper_manager.last_status = "Scraping Grad Café..."

    response = client.post("/update-analysis")
    assert response.status_code == 409
    data = response.get_json()
    assert data["busy"] is True
    assert data["ok"] is False


@pytest.mark.buttons
def test_busy_gating_pull_data(client):
    """
    Test that when a pull is in progress, POST /pull-data returns 409 {"busy": true}.
    """
    with scraper_manager._thread_lock:
        scraper_manager.is_running = True
        scraper_manager.last_status = "Scraping Grad Café..."

    response = client.post("/pull-data")
    assert response.status_code == 409
    data = response.get_json()
    assert data["busy"] is True
    assert data["ok"] is False


@pytest.mark.buttons
def test_pull_data_error_path(client):
    """
    Test negative error-path: loader error produces non-crashing state and reports error in status.
    """
    def failing_loader(records):
        raise RuntimeError("Database connection timed out during test")

    scraper_manager.set_test_doubles(custom_scraper=lambda: [], custom_loader=failing_loader)

    # Run pull
    response = client.post("/pull-data?sync=true")
    assert response.status_code == 200

    # Status should reflect failure without crashing server
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    status = status_res.get_json()
    assert status["is_running"] is False
    assert "Database connection timed out" in str(status["error"])
