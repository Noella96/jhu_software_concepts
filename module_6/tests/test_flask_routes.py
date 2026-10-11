"""
Unit and Integration Tests for Web Service Flask Routes.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

from unittest.mock import patch
import pytest

from src.web.app import routes
from src.web.run import main as run_web_main


@pytest.mark.web
def test_index_page_loads_html(client):
    """Test dashboard index page renders HTML template with analysis data."""
    full_metrics = {
        "total_records": 100,
        "q1": 10,
        "q2": 10,
        "q3": {"gpa": 3.8, "gre": 165.0, "gre_v": 160.0, "gre_aw": 4.5},
        "q4": 3.8,
        "q5": 50.0,
        "q6": 10,
        "q7": 10,
        "q8": 10,
        "q9": {"original": 10, "llm": 12, "diff": 2},
        "q10": [],
        "q11": [],
    }
    with patch.object(routes, "fetch_all_dashboard_data", return_value=full_metrics):
        res = client.get("/")
        assert res.status_code == 200
        assert b"html" in res.data.lower() or b"grad" in res.data.lower()

        res_analysis = client.get("/analysis")
        assert res_analysis.status_code == 200


@pytest.mark.web
def test_index_page_handles_db_exception(client):
    """Test dashboard index page falls back to default empty metrics if DB is offline."""
    with patch.object(routes, "fetch_all_dashboard_data", side_effect=RuntimeError("DB Offline")):
        res = client.get("/")
        assert res.status_code == 200


@pytest.mark.web
def test_pull_data_post_queues_task(client):
    """Test POST /pull-data publishes task to RabbitMQ and immediately returns HTTP 202."""
    with patch.object(routes.publisher, "publish_task") as mock_publish:
        res = client.post("/pull-data")
        assert res.status_code == 202
        data = res.get_json()
        assert data["ok"] is True
        assert data["status"] == "queued"
        assert data["kind"] == "scrape_new_data"
        mock_publish.assert_called_once_with(
            kind="scrape_new_data", payload={"source": "gradcafe_scraper"}
        )


@pytest.mark.web
def test_pull_data_post_broker_failure_returns_503(client):
    """Test POST /pull-data returns HTTP 503 if RabbitMQ broker is unreachable."""
    with patch.object(routes.publisher, "publish_task", side_effect=ConnectionError("Down")):
        res = client.post("/pull-data")
        assert res.status_code == 503
        data = res.get_json()
        assert data["ok"] is False
        assert "Failed to publish" in data["error"]


@pytest.mark.web
def test_update_analysis_post_queues_task(client):
    """Test POST /update-analysis publishes recompute task returning HTTP 202."""
    with patch.object(routes.publisher, "publish_task") as mock_publish:
        res = client.post("/update-analysis")
        assert res.status_code == 202
        data = res.get_json()
        assert data["ok"] is True
        assert data["status"] == "queued"
        assert data["kind"] == "recompute_analytics"
        mock_publish.assert_called_once_with(kind="recompute_analytics", payload={})


@pytest.mark.web
def test_update_analysis_post_broker_failure_returns_503(client):
    """Test POST /update-analysis returns HTTP 503 when broker raises exception."""
    with patch.object(routes.publisher, "publish_task", side_effect=RuntimeError("Broker Error")):
        res = client.post("/update-analysis")
        assert res.status_code == 503
        data = res.get_json()
        assert data["ok"] is False


@pytest.mark.web
def test_update_analysis_get_returns_json_metrics(client):
    """Test GET /update-analysis returns freshly queried metrics as JSON."""
    mock_metrics = {"total_records": 50, "q1": 5}
    with patch.object(routes, "fetch_all_dashboard_data", return_value=mock_metrics):
        res = client.get("/update-analysis")
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert data["data"] == mock_metrics


@pytest.mark.web
def test_api_status_endpoint(client):
    """Test GET /api/status returns operational JSON payload."""
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "operational"
    assert data["broker"] == "rabbitmq"
    assert data["service"] == "gradcafe_web"


@pytest.mark.web
def test_api_applicants_search(client):
    """Test GET /api/applicants filters safely with limit clamping."""
    mock_results = [{"p_id": 1, "program": "Computer Science"}]
    with patch.object(routes, "get_db_session"), \
         patch.object(routes, "query_applicants_dynamic", return_value=mock_results):
        res = client.get("/api/applicants?column=program&value=Computer&limit=15")
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert data["count"] == 1
        assert data["limit_applied"] == 15
        assert data["results"] == mock_results


@pytest.mark.web
def test_api_applicants_search_invalid_column(client):
    """Test GET /api/applicants returns HTTP 400 on invalid column parameter."""
    with patch.object(routes, "get_db_session"), \
         patch.object(
             routes,
             "query_applicants_dynamic",
             side_effect=ValueError("Unauthorized column name"),
         ):
        res = client.get("/api/applicants?column=drop_table")
        assert res.status_code == 400
        data = res.get_json()
        assert data["ok"] is False
        assert "column" in data["error"].lower()


@pytest.mark.web
def test_run_web_main():
    """Test web entrypoint main() starts Flask app with configured port."""
    with patch("src.web.run.app.run") as mock_app_run:
        run_web_main()
        mock_app_run.assert_called_once_with(host="0.0.0.0", port=8080, debug=False)
