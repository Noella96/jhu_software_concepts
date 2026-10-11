"""
Coverage Booster Test Suite for Complete 100% Branch and Statement Coverage.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import json
import runpy
import urllib.error
from unittest.mock import MagicMock, mock_open, patch
import pytest

from src.db.load_data import (
    load_data_from_records,
    main as db_main,
    parse_numeric,
    parse_p_id,
)
from src.web.app.routes import fetch_all_dashboard_data
from src.web.models import get_database_uri
from src.web.orm_queries import (
    execute_orm_queries as web_exec_orm,
    orm_question_8,
    orm_question_9,
)
from src.web.query_data import (
    execute_all_queries as web_exec_all,
    get_db_connection as web_get_raw_conn,
    query_applicants_dynamic as web_dynamic,
    run_question_3 as web_q3,
)
from src.worker.consumer import (
    handle_scrape_new_data,
    process_message,
    run_worker,
)
from src.worker.etl.clean import (
    _extract_degree,
    _extract_origin,
    _parse_entry,
    clean_data,
    generate_applicant_dataset,
)
from src.worker.etl.incremental_scraper import (
    check_robots_compliance,
    fetch_page_html,
    scrape_data,
)
from src.worker.etl.query_data import (
    clamp_limit as worker_clamp_limit,
    execute_all_queries as worker_exec_all,
    get_db_connection as worker_get_raw_conn,
    print_formatted_results as worker_print_results,
    query_applicants_dynamic as worker_query_dynamic,
    run_question_1 as worker_q1,
    run_question_2 as worker_q2,
    run_question_3 as worker_q3,
    run_question_4 as worker_q4,
    run_question_5 as worker_q5,
    run_question_6 as worker_q6,
    run_question_7 as worker_q7,
    run_question_8 as worker_q8,
    run_question_9 as worker_q9,
    run_question_10 as worker_q10,
    run_question_11 as worker_q11,
)
from src.worker.etl.standardize import (
    standardize_dataset,
    standardize_program_and_university,
)


@pytest.mark.worker
def test_worker_consumer_scraper_branches():
    """Test default scraping flow in handle_scrape_new_data both success and exception."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Success branch with standardize_dataset called
    sample_html = (
        "<table><tr><td>Harvard</td><td>CS</td><td>Accepted</td>"
        "<td>GPA 3.9</td><td>Added on March 1, 2026</td><td></td>"
        "<td>Fall 2026</td><td>American</td><td>Masters</td></tr></table>"
    )
    with patch("src.worker.consumer.scrape_data", return_value=[(1, sample_html)]), \
         patch("src.worker.consumer.clean_data", return_value=[{"applicant_id": 99}]), \
         patch(
             "src.worker.consumer.generate_applicant_dataset",
             return_value=[{"applicant_id": 99, "program": "CS"}],
         ), \
         patch(
             "src.worker.consumer.standardize_dataset",
             return_value=[{"p_id": 99, "program": "CS"}],
         ):
        res = handle_scrape_new_data(mock_conn, payload={})
        assert res["inserted"] >= 0

    # Exception fallback branch loading applicant_data.json
    mock_data = [{"p_id": 1, "program": "CS", "date_added": "2026-03-31"}]
    with patch("src.worker.consumer.scrape_data", side_effect=RuntimeError("Network Error")), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        res2 = handle_scrape_new_data(mock_conn, payload={"source": "fallback"})
        assert res2["inserted"] >= 1


@pytest.mark.worker
def test_worker_run_worker_keyboard_interrupt():
    """Test run_worker startup, message consumption callback, and keyboard interrupt."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_ch.start_consuming.side_effect = KeyboardInterrupt

    with patch("src.worker.consumer.setup_consumer", return_value=(mock_conn, mock_ch)):
        run_worker()
        assert mock_ch.basic_consume.call_count == 1
        mock_ch.stop_consuming.assert_called_once()
        mock_conn.close.assert_called_once()

        # Trigger message callback
        callback_fn = mock_ch.basic_consume.call_args.kwargs["on_message_callback"]
        with patch("src.worker.consumer.process_message") as mock_proc:
            callback_fn(mock_ch, MagicMock(), MagicMock(), b'{"test": 1}')
            mock_proc.assert_called_once()


@pytest.mark.worker
def test_worker_consumer_close_connection_branch():
    """Test process_message closing internally-created DB connection and scrape task."""
    mock_ch = MagicMock()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Test recompute_analytics task with db_conn=None (triggers close)
    body_recompute = json.dumps(
        {"kind": "recompute_analytics", "payload": {}}
    ).encode()
    with patch("src.worker.consumer.get_db_connection", return_value=mock_conn):
        with patch("src.worker.consumer.execute_all_queries", return_value={}):
            success = process_message(
                mock_ch, MagicMock(delivery_tag=1), MagicMock(), body_recompute, db_conn=None
            )
            assert success is True
            mock_conn.close.assert_called_once()

    # Test scrape_new_data dispatch (line 261)
    body_scrape = json.dumps(
        {"kind": "scrape_new_data", "payload": {"source": "unit_test"}}
    ).encode()
    with patch("src.worker.consumer.handle_scrape_new_data", return_value={"inserted": 1}):
        success2 = process_message(
            mock_ch, MagicMock(delivery_tag=2), MagicMock(), body_scrape, db_conn=mock_conn
        )
        assert success2 is True

    # Test rollback exception handler (lines 275-276)
    mock_failing_conn = MagicMock()
    mock_failing_conn.transaction.side_effect = RuntimeError("Transaction boom")
    mock_failing_conn.rollback.side_effect = RuntimeError("Rollback boom")
    success3 = process_message(
        mock_ch, MagicMock(delivery_tag=3), MagicMock(), body_scrape, db_conn=mock_failing_conn
    )
    assert success3 is False


@pytest.mark.worker
def test_worker_etl_clean_and_watermark_branches():
    """Test parse_p_id, load_data_from_records fallback, and clean_data div branch."""
    assert parse_p_id("https://thegradcafe.com/result/123", default_id=1) == 123
    assert parse_p_id("", default_id=99) == 99

    # clean_data div fallback (line 254)
    div_html = "<div class='entry'><div class='univ'>Stanford</div></div>"
    assert len(clean_data([div_html])) == 1

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = (5,)

    recs = [
        {"p_id": 1, "program": "CS", "university": "JHU", "term": "Fall 2026"},
        {"p_id": 2, "program": "EE", "university": "MIT", "term": "Fall 2026"},
    ]
    res = load_data_from_records(recs, mock_conn)
    assert res == 2


@pytest.mark.analysis
def test_worker_etl_query_data_complete():
    """Test query_data utility functions and queries in worker."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Test clamp_limit
    assert worker_clamp_limit("abc", 50, 100) == 50
    assert worker_clamp_limit(200, 50, 100) == 100
    assert worker_clamp_limit(-5, 50, 100) == 50
    assert worker_clamp_limit(25, 50, 100) == 25

    # Test custom_conninfo (line 49)
    with patch("psycopg.connect", return_value=mock_conn):
        c1 = worker_get_raw_conn(custom_conninfo="postgresql://test:5432/db")
        assert c1 == mock_conn

    # Test query functions with mock returns
    mock_cur.fetchone.return_value = (42,)
    assert worker_q1(mock_conn) == 42
    assert worker_q2(mock_conn) == 42.0

    mock_cur.fetchone.return_value = (3.8, 165.0, 160.0, 4.5)
    assert worker_q3(mock_conn) == (3.8, 165.0, 160.0, 4.5)

    mock_cur.fetchone.return_value = (3.75,)
    assert worker_q4(mock_conn) == 3.75
    assert worker_q5(mock_conn) == 3.75
    assert worker_q6(mock_conn) == 3.75

    mock_cur.fetchone.return_value = (15,)
    assert worker_q7(mock_conn) == 15
    assert worker_q8(mock_conn) == 15

    mock_cur.fetchone.side_effect = [(10,), (12,)]
    assert worker_q9(mock_conn) == (10, 12, 2)

    mock_cur.fetchall.return_value = [
        {"university": "JHU", "applicants": 100, "accepted": 50, "acceptance_rate": 50.0}
    ]
    assert len(worker_q10(mock_conn)) == 1

    mock_cur.fetchall.return_value = [
        {"decision": "Accepted", "applicant_count": 50, "avg_gpa": 3.8, "avg_gre": 165.0}
    ]
    q11_res = worker_q11(mock_conn)
    assert q11_res[0]["decision"] == "Accepted"

    # Test execute_all_queries with provided conn and conn=None (should_close=True)
    with patch("src.worker.etl.query_data.get_db_connection", return_value=mock_conn):
        with patch("src.worker.etl.query_data.run_question_1", return_value=1), \
             patch("src.worker.etl.query_data.run_question_2", return_value=2.0), \
             patch(
                 "src.worker.etl.query_data.run_question_3",
                 return_value=(3.0, 160.0, 150.0, 4.0),
             ), \
             patch("src.worker.etl.query_data.run_question_4", return_value=3.5), \
             patch("src.worker.etl.query_data.run_question_5", return_value=40.0), \
             patch("src.worker.etl.query_data.run_question_6", return_value=3.8), \
             patch("src.worker.etl.query_data.run_question_7", return_value=5), \
             patch("src.worker.etl.query_data.run_question_8", return_value=3), \
             patch("src.worker.etl.query_data.run_question_9", return_value=(3, 3, 0)), \
             patch("src.worker.etl.query_data.run_question_10", return_value=[]), \
             patch("src.worker.etl.query_data.run_question_11", return_value={}):
            worker_execute_all_res = worker_exec_all(mock_conn)
            assert "q1" in worker_execute_all_res
            res_null = worker_exec_all(conn=None)
            assert res_null["q1"] == 1
            mock_conn.close.assert_called_once()

    # Test query_applicants_dynamic
    mock_cur.fetchall.return_value = [{"p_id": 1}]
    dyn = worker_query_dynamic(mock_conn, filter_column="program", filter_value="CS", limit=10)
    assert len(dyn) == 1

    # Unauthorized column raises ValueError
    with pytest.raises(ValueError, match="Unauthorized column"):
        worker_query_dynamic(mock_conn, filter_column="malicious_col")

    # Unauthorized table raises ValueError
    with pytest.raises(ValueError, match="Unauthorized table"):
        worker_query_dynamic(mock_conn, table_name="forbidden_tbl")

    # Test print_formatted_results
    with patch("src.worker.etl.query_data.get_db_connection", return_value=mock_conn):
        with patch("src.worker.etl.query_data.run_question_1", return_value=10), \
             patch("src.worker.etl.query_data.run_question_2", return_value=20.0), \
             patch(
                 "src.worker.etl.query_data.run_question_3",
                 return_value=(3.8, 165.0, 160.0, 4.5),
             ), \
             patch("src.worker.etl.query_data.run_question_4", return_value=3.7), \
             patch("src.worker.etl.query_data.run_question_5", return_value=45.0), \
             patch("src.worker.etl.query_data.run_question_6", return_value=3.9), \
             patch("src.worker.etl.query_data.run_question_7", return_value=15), \
             patch("src.worker.etl.query_data.run_question_8", return_value=12), \
             patch("src.worker.etl.query_data.run_question_9", return_value=(12, 10, 2)), \
             patch(
                 "src.worker.etl.query_data.run_question_10",
                 return_value=[{
                     "university": "JHU",
                     "total_applicants": 10,
                     "accepted_count": 5,
                     "acceptance_rate_pct": 50.0,
                 }],
             ), \
             patch(
                 "src.worker.etl.query_data.run_question_11",
                 return_value=[{
                     "admission_outcome": "Accepted",
                     "applicant_count": 5,
                     "avg_gpa": 3.8,
                     "avg_gre_quant": 165.0,
                 }],
             ):
            worker_print_results()


@pytest.mark.web
def test_web_routes_and_dashboard_helpers(client):
    """Test dashboard data helpers and remaining route paths."""
    with patch("src.web.app.routes.get_db_session") as mock_session_fn, \
         patch("src.web.app.routes.run_question_2", return_value=50.0), \
         patch("src.web.app.routes.run_question_3", return_value=(3.8, 165.0, 160.0, 4.5)), \
         patch("src.web.app.routes.run_question_6", return_value=3.9), \
         patch("src.web.app.routes.run_question_7", return_value=12), \
         patch("src.web.app.routes.run_question_11", return_value={}):
        mock_sess = MagicMock()
        mock_sess.scalar.return_value = 50
        mock_session_fn.return_value = mock_sess

        data = fetch_all_dashboard_data()
        assert data["total_records"] == 50
        assert "q1" in data
        assert "q3" in data

    # Trigger /api/applicants dynamic search with empty filter
    res = client.get("/api/applicants?filter_column=program&filter_value=&limit=5")
    assert res.status_code == 200

    # Trigger /api/tasks/status with non-existent task
    res_status = client.get("/api/tasks/status?task_id=nonexistent-id")
    assert res_status.status_code == 404


@pytest.mark.db
def test_db_load_data_main():
    """Test main execution function in db load_data with and without data file."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = (500,)

    with patch("src.db.load_data.get_db_connection", return_value=mock_conn), \
         patch("src.db.load_data.load_data_from_json", return_value=(500, 500)), \
         patch("os.path.exists", return_value=True):
        db_main()

    # Test file not found warning branch (line 327)
    with patch("src.db.load_data.get_db_connection", return_value=mock_conn), \
         patch("os.path.exists", return_value=False):
        db_main()


@pytest.mark.web
def test_models_and_queries_coverage(client):
    """Test models.py, web query_data, orm_queries, and search limit param."""
    # routes limit parse exception
    res = client.get("/api/applicants?limit=not_a_number")
    assert res.status_code == 200

    # parse_numeric whitespace returns None
    assert parse_numeric("   ") is None
    assert parse_numeric(None) is None

    # models get_database_uri with env user and pass
    with patch.dict(
        "os.environ",
        {
            "DATABASE_URL": "",
            "POSTGRES_USER": "usr",
            "POSTGRES_PASSWORD": "pwd",
            "DB_NAME": "db",
        },
        clear=True,
    ):
        uri = get_database_uri()
        assert "usr:pwd" in uri

    # models get_database_uri with empty user
    with patch.dict(
        "os.environ",
        {
            "DATABASE_URL": "",
            "POSTGRES_USER": "",
            "POSTGRES_PASSWORD": "",
            "DB_NAME": "testdb",
        },
        clear=True,
    ):
        uri_no_user = get_database_uri()
        assert "postgresql+psycopg://localhost:5432/testdb" in uri_no_user

    # web query_data with password and question 3 empty row
    mock_c = MagicMock()
    mock_cr = MagicMock()
    mock_c.cursor.return_value.__enter__.return_value = mock_cr
    mock_cr.fetchone.return_value = (3.8, 165.0, 160.0, 4.5)
    with patch("psycopg.connect", return_value=mock_c):
        with patch.dict(
            "os.environ",
            {"DB_USER": "u", "DB_PASSWORD": "p", "DATABASE_URL": ""},
            clear=True,
        ):
            web_get_raw_conn()
            worker_get_raw_conn()
            web_q3(mock_c)

    # question 3 empty row branch
    mock_cr.fetchone.return_value = None
    assert web_q3(mock_c) == (0.0, 0.0, 0.0, 0.0)
    assert worker_q3(mock_c) == (0.0, 0.0, 0.0, 0.0)

    # query_applicants_dynamic bad table
    with pytest.raises(ValueError, match="Unauthorized table"):
        web_dynamic(mock_c, table_name="bad_table")

    # web execute_all_queries with conn=None (should_close=True)
    with patch("src.web.query_data.get_db_connection", return_value=mock_c):
        with patch("src.web.query_data.run_question_1", return_value=1), \
             patch("src.web.query_data.run_question_2", return_value=2.0), \
             patch(
                 "src.web.query_data.run_question_3",
                 return_value=(3.0, 160.0, 150.0, 4.0),
             ), \
             patch("src.web.query_data.run_question_4", return_value=3.5), \
             patch("src.web.query_data.run_question_5", return_value=40.0), \
             patch("src.web.query_data.run_question_6", return_value=3.8), \
             patch("src.web.query_data.run_question_7", return_value=5), \
             patch("src.web.query_data.run_question_8", return_value=3), \
             patch("src.web.query_data.run_question_9", return_value=(3, 3, 0)), \
             patch("src.web.query_data.run_question_10", return_value=[]), \
             patch("src.web.query_data.run_question_11", return_value={}):
            res_web_null = web_exec_all(conn=None)
            assert res_web_null["q1"] == 1
            mock_c.close.assert_called_once()

    # orm_question_8 and execute_orm_queries with session=None
    mock_s = MagicMock()
    mock_s.scalar.return_value = 15
    assert orm_question_8(mock_s) == 15
    assert orm_question_9(mock_s) == (15, 15, 0)

    with patch("src.web.orm_queries.get_db_session", return_value=mock_s):
        with patch("src.web.orm_queries.orm_question_1", return_value=1), \
             patch("src.web.orm_queries.orm_question_4", return_value=3.5), \
             patch("src.web.orm_queries.orm_question_5", return_value=50.0), \
             patch("src.web.orm_queries.orm_question_8", return_value=2), \
             patch("src.web.orm_queries.orm_question_9", return_value=(2, 2, 0)), \
             patch("src.web.orm_queries.orm_question_10", return_value=[]):
            res_orm_null = web_exec_orm(session=None)
            assert res_orm_null["q1"] == 1
            mock_s.close.assert_called_once()


@pytest.mark.analysis
def test_clean_and_standardize_edge_cases():
    """Test edge cases in clean, incremental_scraper, and standardize."""
    assert _extract_degree("Non-degree certificate") == "Masters"
    assert _extract_origin("Other unknown country") == "International"

    assert _parse_entry("not_a_tag") is None

    # generate_applicant_dataset multi outcomes
    ds = generate_applicant_dataset(count=50)
    assert len(ds) >= 50

    # standardize_program_and_university comma only
    assert standardize_program_and_university(" , ") == (
        "General Program",
        "Unknown University",
    )

    # standardize_dataset list input
    std_res = standardize_dataset(
        input_source=[{"program": "Computer Science, Stanford University"}]
    )
    assert len(std_res) == 1
    assert std_res[0]["llm_generated_university"] == "Stanford University"

    # check_robots_compliance disallow
    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"User-agent: *\nDisallow: /survey\n"
        mock_url.return_value.__enter__.return_value = mock_resp
        assert check_robots_compliance() is False

    # fetch_page_html rate limit backoff
    err = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
    mock_retry_resp = MagicMock()
    mock_retry_resp.read.return_value = b"<html>retry</html>"
    mock_retry_ctx = MagicMock()
    mock_retry_ctx.__enter__.return_value = mock_retry_resp

    with patch("urllib.request.urlopen", side_effect=[err, mock_retry_ctx]):
        html = fetch_page_html(
            "https://thegradcafe.com/survey/index.php", max_retries=2, delay=0.01
        )
        assert html == "<html>retry</html>"

    # fetch_page_html 404 HTTP Error (non-429)
    err_404 = urllib.error.HTTPError("http://test", 404, "Not Found", {}, None)
    with patch("urllib.request.urlopen", side_effect=err_404):
        assert fetch_page_html("http://test", max_retries=1, delay=0.01) is None

    # fetch_page_html Generic Exception
    with patch("urllib.request.urlopen", side_effect=OSError("network unreachable")):
        assert fetch_page_html("http://test", max_retries=1, delay=0.01) is None

    # scrape_data robots disallow branch
    with patch(
        "src.worker.etl.incremental_scraper.check_robots_compliance", return_value=False
    ):
        assert not scrape_data()

    # get_database_uri fallback branches
    uri = get_database_uri("sqlite:///:memory:")
    assert "sqlite" in uri


@pytest.mark.analysis
def test_runpy_entrypoints(tmp_path):
    """Test __main__ blocks via runpy across services."""
    # 1. src.worker.etl.clean
    clean_out = tmp_path / "clean.json"
    with patch("sys.argv", ["clean.py", "--count", "2", "--output", str(clean_out)]):
        runpy.run_module("src.worker.etl.clean", run_name="__main__", alter_sys=True)

    # 2. src.worker.etl.standardize
    std_out = tmp_path / "std.json"
    with patch("sys.argv", ["std.py", "--input", str(clean_out), "--output", str(std_out)]):
        runpy.run_module("src.worker.etl.standardize", run_name="__main__", alter_sys=True)

    # 3. src.worker.etl.incremental_scraper
    with patch("src.worker.etl.incremental_scraper.scrape_data", return_value=[]), \
         patch("sys.argv", ["scrape.py", "--start", "1", "--end", "1"]):
        runpy.run_module(
            "src.worker.etl.incremental_scraper", run_name="__main__", alter_sys=True
        )

    # 4. src.web.run
    with patch("flask.Flask.run") as mock_frun:
        runpy.run_module("src.web.run", run_name="__main__", alter_sys=True)
        mock_frun.assert_called_once()

    # 5. src.db.load_data
    with patch("psycopg.connect") as mock_psc:
        mock_c = MagicMock()
        mock_cr = MagicMock()
        mock_c.cursor.return_value.__enter__.return_value = mock_cr
        mock_cr.fetchone.return_value = (10,)
        mock_psc.return_value = mock_c
        with patch("src.db.load_data.load_data_from_json", return_value=(10, 10)):
            runpy.run_module("src.db.load_data", run_name="__main__", alter_sys=True)

    # 6. src.web.query_data
    with patch("src.web.query_data.print_formatted_results"):
        runpy.run_module("src.web.query_data", run_name="__main__", alter_sys=True)

    # 7. src.worker.etl.query_data
    with patch("src.worker.etl.query_data.print_formatted_results"):
        runpy.run_module("src.worker.etl.query_data", run_name="__main__", alter_sys=True)

    # 8. src.web.orm_queries
    with patch("src.web.orm_queries.print_formatted_orm_results"):
        runpy.run_module("src.web.orm_queries", run_name="__main__", alter_sys=True)

    # 9. src.worker.consumer
    mock_pika_conn = MagicMock()
    with patch("pika.BlockingConnection", return_value=mock_pika_conn):
        runpy.run_module("src.worker.consumer", run_name="__main__", alter_sys=True)
