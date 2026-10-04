"""
Comprehensive Unit Tests for ETL, DB Loader, Models, Query Modules, and CLI Runners.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)

Guarantees 100% branch and statement coverage across all source files in module_4/src.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import unittest.mock as mock
import pytest
from bs4 import BeautifulSoup

from src.clean import (
    _extract_degree,
    _extract_metrics,
    _extract_origin,
    _normalize_status,
    _parse_entry,
    clean_data,
    generate_applicant_dataset,
    load_data,
    save_data,
)
from src.load_data import (
    create_applicants_table,
    get_db_connection,
    get_db_connection_params,
    load_data_from_json,
    load_data_from_records,
    main as load_data_main,
    parse_date,
    parse_numeric,
    parse_p_id,
    parse_text,
)
from src.models import (
    Applicant,
    Base,
    get_database_uri,
    get_db_session,
    get_engine,
)
from src.orm_queries import (
    execute_orm_queries,
    orm_question_1,
    orm_question_4,
    orm_question_5,
    orm_question_8,
    orm_question_9,
    orm_question_10,
    print_formatted_orm_results,
)
from src.query_data import (
    execute_all_queries,
    get_db_connection as get_raw_conn,
    print_formatted_results,
    run_question_1,
    run_question_2,
    run_question_3,
    run_question_4,
    run_question_5,
    run_question_6,
    run_question_7,
    run_question_8,
    run_question_9,
    run_question_10,
    run_question_11,
)
from src.scrape import (
    build_page_url,
    check_robots_compliance,
    fetch_page_html,
    fetch_single_page_job,
    scrape_data,
)
from src.standardize import (
    standardize_dataset,
    standardize_program_and_university,
    standardize_records,
)


@pytest.mark.analysis
def test_clean_module_parsing_and_helpers(tmp_path):
    """
    Test helper extraction functions in clean.py.
    """
    # _normalize_status
    assert _normalize_status("") == "Accepted"
    assert _normalize_status("  Accepted on 1 Mar  ") == "Accepted on 1 Mar"

    # _extract_degree
    assert _extract_degree("PhD in Computer Science") == "PhD"
    assert _extract_degree("Doctorate of Philosophy") == "PhD"
    assert _extract_degree("Master of Science") == "Masters"
    assert _extract_degree("MSc in Informatics") == "Masters"
    assert _extract_degree("Certificate") == "Masters"

    # _extract_origin
    assert _extract_origin("American Domestic applicant") == "American"
    assert _extract_origin("International student") == "International"
    assert _extract_origin("Other unknown") == "International"

    # _extract_metrics
    m1 = _extract_metrics("GPA of 3.88 GRE of 165 GRE V of 160 GRE AW of 4.5")
    assert m1["GPA"] == "GPA 3.88"
    assert m1["GRE"] == "GRE 165"
    assert m1["GRE V"] == "GRE V 160"
    assert m1["GRE AW"] == "GRE AW 4.5"

    m2 = _extract_metrics("No scores provided")
    assert m2 == {}

    # _parse_entry with HTML row
    row_html = "<tr><td>Harvard University</td><td>Computer Science</td><td>Accepted on 15 Feb</td><td>GPA 3.90 GRE 168</td><td>Added on March 1, 2026</td><td>Comments: Great result</td><td>Fall 2026</td><td>American</td><td>PhD</td></tr>"
    soup = BeautifulSoup(row_html, "html.parser")
    parsed = _parse_entry(soup.find("tr"), base_id=12345)
    assert parsed is not None
    assert "Harvard University" in parsed["program"]

    # _parse_entry fallback branch with malformed row
    empty_soup = BeautifulSoup("<div>test</div>", "html.parser")
    parsed_fallback = _parse_entry(empty_soup, base_id=12346)
    assert parsed_fallback is not None

    # _parse_entry exception handling
    assert _parse_entry(None) is None

    # generate_applicant_dataset
    dataset = generate_applicant_dataset(count=15)
    assert len(dataset) >= 15
    assert dataset[0]["program"] != ""

    # clean_data
    html_pages = [f"<table>{row_html}</table>", "<div><div class='result'>Sample row</div></div>"]
    cleaned_list = clean_data(html_pages)
    assert len(cleaned_list) >= 1

    # save_data and load_data
    test_json = tmp_path / "test_data.json"
    save_data(dataset[:3], str(test_json))
    loaded_data = load_data(str(test_json))
    assert len(loaded_data) == 3


@pytest.mark.analysis
def test_standardize_module(tmp_path):
    """
    Test standardize_program_and_university and standardize_records in standardize.py.
    """
    # Empty string
    p1, u1 = standardize_program_and_university("")
    assert p1 == "General Program" and u1 == "Unknown University"

    # Single part
    p2, u2 = standardize_program_and_university("Computer Science")
    assert p2 == "Computer Science" and u2 == "Unknown University"

    # Multi part with canonical university matching
    p3, u3 = standardize_program_and_university("Computer Science, MIT ")
    assert p3 == "Computer Science" and u3 == "Massachusetts Institute of Technology"

    p4, u4 = standardize_program_and_university("Informatics, JHU ")
    assert p4 == "Informatics" and u4 == "Johns Hopkins University"

    # Empty parts
    p5, u5 = standardize_program_and_university(" , ")
    assert p5 == "General Program" and u5 == "Unknown University"

    # Test standardize_records
    sample = [{"program": "Robotics, CMU "}, {"program": "Data Science, Stanford "}]
    res = standardize_records(sample)
    assert len(res) == 2
    assert res[0]["llm_generated_university"] == "Carnegie Mellon University"
    assert res[1]["llm_generated_university"] == "Stanford University"

    # Test standardize_dataset with file
    test_in = tmp_path / "in.json"
    test_out = tmp_path / "out.json"
    with open(test_in, "w") as f:
        json.dump(sample, f)

    std_from_file = standardize_dataset(str(test_in), str(test_out))
    assert len(std_from_file) == 2
    assert os.path.exists(test_out)

    # Empty source
    assert standardize_dataset(None) == []


@pytest.mark.db
def test_load_data_module_parsers_and_helpers(tmp_path):
    """
    Test parsing helpers in load_data.py.
    """
    # parse_p_id
    assert parse_p_id("https://www.thegradcafe.com/result/888888", 1) == 888888
    assert parse_p_id("888888", 1) == 888888
    assert parse_p_id("", 99) == 99

    # parse_date
    assert parse_date("Added on March 31, 2026") == datetime.date(2026, 3, 31)
    assert parse_date("2026-03-31") == datetime.date(2026, 3, 31)
    assert parse_date("03/31/2026") == datetime.date(2026, 3, 31)
    assert parse_date(None) is None
    assert parse_date("InvalidDateString") is None

    # parse_numeric
    assert parse_numeric(3.95) == 3.95
    assert parse_numeric("GPA 3.88") == 3.88
    assert parse_numeric("GRE 165") == 165.0
    assert parse_numeric(None) is None
    assert parse_numeric("") is None
    assert parse_numeric("NoneProvided") is None

    # parse_text
    assert parse_text("  Valid Text  ") == "Valid Text"
    assert parse_text(None) is None
    assert parse_text("   ") is None

    # get_db_connection_params
    params = get_db_connection_params("postgresql://localhost/test_db")
    assert params["conninfo"] == "postgresql://localhost/test_db"

    # load_data_from_json error handling
    with pytest.raises(FileNotFoundError):
        load_data_from_json("non_existent_file.json", None)

    # load_data_from_json success
    test_json = tmp_path / "sample_load.json"
    with open(test_json, "w") as f:
        json.dump([{"p_id": 777771, "program": "CS, JHU", "url": "https://thegradcafe.com/result/777771"}], f)

    conn = get_db_connection()
    try:
        inserted, total = load_data_from_json(str(test_json), conn)
        assert inserted == 1 and total == 1
    finally:
        conn.close()


@pytest.mark.db
def test_models_and_queries_helpers():
    """
    Test SQLAlchemy models and ORM/SQL query execution functions.
    """
    # models
    app_obj = Applicant(p_id=123, program="CS, Stanford", status="Accepted")
    assert "123" in repr(app_obj)

    # get_database_uri variations
    uri1 = get_database_uri("postgres://user:pass@localhost:5432/db")
    assert uri1.startswith("postgresql+psycopg://")

    uri2 = get_database_uri("postgresql://user:pass@localhost:5432/db")
    assert uri2.startswith("postgresql+psycopg://")

    # get_db_session with custom engine
    engine = get_engine()
    s = get_db_session(engine)
    assert s is not None
    s.close()

    # orm_queries functions
    session = get_db_session()
    try:
        assert isinstance(orm_question_1(session), int)
        assert isinstance(orm_question_4(session), float)
        assert isinstance(orm_question_5(session), float)
        assert isinstance(orm_question_8(session), int)
        q8, q9, diff = orm_question_9(session)
        assert isinstance(q8, int) and isinstance(q9, int)
        assert isinstance(orm_question_10(session), list)

        # execute_orm_queries
        res = execute_orm_queries(session)
        assert "q1" in res and "q10" in res

        # print_formatted_orm_results
        print_formatted_orm_results()
    finally:
        session.close()

    # raw SQL query functions
    conn = get_raw_conn()
    try:
        assert isinstance(run_question_1(conn), int)
        assert isinstance(run_question_2(conn), float)
        assert len(run_question_3(conn)) == 4
        assert isinstance(run_question_4(conn), float)
        assert isinstance(run_question_5(conn), float)
        assert isinstance(run_question_6(conn), float)
        assert isinstance(run_question_7(conn), int)
        assert isinstance(run_question_8(conn), int)
        q8_r, q9_r, diff_r = run_question_9(conn)
        assert isinstance(q8_r, int)
        assert isinstance(run_question_10(conn), list)
        assert isinstance(run_question_11(conn), list)

        # print_formatted_results
        print_formatted_results()
    finally:
        conn.close()


@pytest.mark.web
def test_scrape_module():
    """
    Test scraping helpers and robots compliance in scrape.py with mocked network calls.
    """
    # build_page_url
    url1 = build_page_url(1)
    assert "page=1" in url1
    url2 = build_page_url(2, query="Computer Science")
    assert "page=2" in url2 and "Computer" in url2

    # check_robots_compliance
    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = mock.MagicMock()
        mock_response.read.return_value = b"User-agent: *\nAllow: /\n"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        assert check_robots_compliance() is True

    # check_robots_compliance with exception
    with mock.patch("urllib.request.urlopen", side_effect=Exception("Network error")):
        assert check_robots_compliance() is True

    # fetch_page_html with success
    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = mock.MagicMock()
        mock_response.read.return_value = b"<html><body>Grad Cafe Data</body></html>"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        content = fetch_page_html("http://example.com/test", max_retries=1, delay=0.01)
        assert "Grad Cafe Data" in content

    # fetch_page_html with HTTP error 429
    import urllib.error
    http_err_429 = urllib.error.HTTPError("http://example.com", 429, "Too Many Requests", {}, None)
    with mock.patch("urllib.request.urlopen", side_effect=http_err_429):
        res_429 = fetch_page_html("http://example.com/rate-limit", max_retries=1, delay=0.01)
        assert res_429 is None

    # fetch_page_html with generic HTTP error
    http_err_500 = urllib.error.HTTPError("http://example.com", 500, "Server Error", {}, None)
    with mock.patch("urllib.request.urlopen", side_effect=http_err_500):
        res_500 = fetch_page_html("http://example.com/server-error", max_retries=1, delay=0.01)
        assert res_500 is None

    # fetch_single_page_job
    with mock.patch("src.scrape.fetch_page_html", return_value="<html>Page 1</html>"):
        p_num, html = fetch_single_page_job(1, delay=0.01)
        assert p_num == 1 and html == "<html>Page 1</html>"

    # scrape_data with robots allowed
    with mock.patch("src.scrape.check_robots_compliance", return_value=True), \
         mock.patch("src.scrape.fetch_single_page_job", return_value=(1, "<html>Page Content</html>")):
        scraped = scrape_data(start_page=1, end_page=2, delay=0.01, max_workers=2)
        assert len(scraped) == 2

    # scrape_data with robots denied
    with mock.patch("src.scrape.check_robots_compliance", return_value=False):
        assert scrape_data() == []


@pytest.mark.analysis
def test_scrape_extra_branches():
    """
    Test edge branches in scrape.py: robots disallow and fetch generic exceptions.
    """
    # 1. Robots Disallow branch
    mock_resp = mock.MagicMock()
    mock_resp.read.return_value = b"User-agent: *\nDisallow: /survey\n"
    mock_resp.__enter__.return_value = mock_resp
    with mock.patch("urllib.request.urlopen", return_value=mock_resp):
        assert check_robots_compliance() is False

    # 2. fetch_page_html generic exception retry branch
    with mock.patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
        res = fetch_page_html("http://example.com/test", max_retries=2, delay=0.001)
        assert res is None


@pytest.mark.web
def test_cli_runners_and_main_entrypoints(tmp_path):
    """
    Test __main__ and CLI entrypoints across ETL and runner modules for complete branch coverage.
    """
    import runpy

    # 1. Test clean.py main() & __main__
    clean_out = tmp_path / "clean_out.json"
    with mock.patch("sys.argv", ["clean.py", "--count", "2", "--output", str(clean_out)]):
        runpy.run_module("src.clean", run_name="__main__", alter_sys=True)
        assert os.path.exists(clean_out)

    # 2. Test standardize.py main() & __main__
    std_out = tmp_path / "std_out.json"
    with mock.patch("sys.argv", ["standardize.py", "--input", str(clean_out), "--output", str(std_out)]):
        runpy.run_module("src.standardize", run_name="__main__", alter_sys=True)
        assert os.path.exists(std_out)

    # 2b. Test standardize_dataset fallback when file path does not exist
    assert standardize_dataset(input_source="/nonexistent_path_test.json") == []

    # 3. Test scrape.py main() & __main__
    mock_job_res = (1, "<html></html>")
    mock_resp_robots = mock.MagicMock()
    mock_resp_robots.read.return_value = b"User-agent: *\nAllow: /\n"
    mock_resp_robots.__enter__.return_value = mock_resp_robots
    with mock.patch("urllib.request.urlopen", return_value=mock_resp_robots), \
         mock.patch("src.scrape.fetch_single_page_job", return_value=mock_job_res), \
         mock.patch("sys.argv", ["scrape.py", "--start", "1", "--end", "1", "--delay", "0.001", "--workers", "1"]):
        runpy.run_module("src.scrape", run_name="__main__", alter_sys=True)

    # 4. Test run.py main() & __main__
    with mock.patch("flask.Flask.run") as mock_flask_run, \
         mock.patch.dict(os.environ, {"PORT": "8888"}):
        runpy.run_module("src.run", run_name="__main__", alter_sys=True)
        mock_flask_run.assert_called_once_with(host="0.0.0.0", port=8888, debug=False)

    # 5. Test load_data.py main() & __main__
    with mock.patch("psycopg.connect") as mock_psycopg_load, \
         mock.patch("json.load", return_value=[{"p_id": 1, "program": "CS", "degree": "PhD"}]):
        mock_c = mock.MagicMock()
        mock_cur = mock.MagicMock()
        mock_cur.fetchone.return_value = (10,)
        mock_c.cursor.return_value.__enter__.return_value = mock_cur
        mock_psycopg_load.return_value = mock_c
        runpy.run_module("src.load_data", run_name="__main__", alter_sys=True)

    # 6. Test load_data.py connection failure branch
    with mock.patch("src.load_data.get_db_connection", side_effect=Exception("DB down")):
        load_data_main()

    # 7. Test get_db_connection_params with user and password environment variables
    with mock.patch.dict(os.environ, {"POSTGRES_USER": "custom_user", "POSTGRES_PASSWORD": "custom_pass"}, clear=False):
        os.environ.pop("DATABASE_URL", None)
        p = get_db_connection_params()
        assert p.get("user") == "custom_user"
        assert p.get("password") == "custom_pass"

    # 8. Test load_data.get_db_connection with conninfo param and kwargs fallback
    with mock.patch("psycopg.connect") as mock_psycopg_conn:
        from src.load_data import get_db_connection as ld_get_conn
        ld_get_conn("postgresql://usr:pwd@localhost:5432/mydb")
        mock_psycopg_conn.assert_called_with("postgresql://usr:pwd@localhost:5432/mydb")

        # Test kwargs fallback when DATABASE_URL is not in environment
        with mock.patch.dict(os.environ, {"POSTGRES_DB": "gradcafe_db", "POSTGRES_USER": "usr", "POSTGRES_PASSWORD": "pwd", "POSTGRES_HOST": "localhost", "POSTGRES_PORT": "5432"}, clear=True):
            ld_get_conn()
            mock_psycopg_conn.assert_called_with(
                dbname="gradcafe_db",
                host="localhost",
                port=5432,
                user="usr",
                password="pwd",
            )

    # 9. Test load_data_from_records when p_id is None
    mock_conn = mock.MagicMock()
    mock_cur = mock.MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    recs_no_pid = [{"url": "https://www.thegradcafe.com/result/888", "program": "CS"}]
    loaded_cnt = load_data_from_records(recs_no_pid, mock_conn)
    assert loaded_cnt == 1

    # 10. Test query_data.py print_formatted_results() & __main__
    with mock.patch("psycopg.connect") as mock_psycopg_qd:
        mock_c = mock.MagicMock()
        mock_cur = mock.MagicMock()
        mock_cur.fetchone.side_effect = [
            (100,),                            # q1
            (25.0,),                           # q2
            (3.85, 165.0, 160.0, 4.5),         # q3
            (3.85,),                           # q4
            (40.0,),                           # q5
            (3.90,),                           # q6
            (50,),                             # q7
            (12,),                             # q8
            (12,),                             # q9 original
            (15,),                             # q9 llm
        ]
        mock_cur.fetchall.side_effect = [
            [{"university": "Johns Hopkins University", "total_applicants": 100, "accepted_count": 20, "acceptance_rate_pct": 20.0}], # q10
            [{"admission_outcome": "Accepted", "applicant_count": 20, "avg_gpa": 3.90, "avg_gre_quant": 168.0}],               # q11
        ]
        mock_c.cursor.return_value.__enter__.return_value = mock_cur
        mock_psycopg_qd.return_value = mock_c
        runpy.run_module("src.query_data", run_name="__main__", alter_sys=True)

    # 11. Test orm_queries.py print_formatted_orm_results() & __main__
    with mock.patch("src.orm_queries.get_db_session") as mock_sess_fn:
        mock_s = mock.MagicMock()
        mock_s.scalar.side_effect = [100, 3.85, 40.0, 12, 12, 15]
        row_mock = mock.MagicMock()
        row_mock.university = "Johns Hopkins University"
        row_mock.total_applicants = 100
        row_mock.accepted_count = 20
        row_mock.acceptance_rate_pct = 20.0
        mock_s.execute.return_value.all.return_value = [row_mock]
        mock_sess_fn.return_value = mock_s
        runpy.run_module("src.orm_queries", run_name="__main__", alter_sys=True)

    # 12. Test query_data.get_db_connection with custom string & DATABASE_URL env & password
    with mock.patch("psycopg.connect") as mock_psycopg_raw:
        with mock.patch.dict(os.environ, {"DATABASE_URL": "postgresql://test_url"}):
            get_raw_conn()
            mock_psycopg_raw.assert_called_with("postgresql://test_url")
        with mock.patch.dict(os.environ, {"POSTGRES_USER": "testu", "POSTGRES_PASSWORD": "testpassword"}, clear=True):
            get_raw_conn()

    # 13. Test models.py Applicant __repr__ and get_database_uri variations
    app_obj = Applicant(p_id=123, program="Computer Science", degree="PhD", status="Accepted")
    assert "123" in repr(app_obj)
    assert "Computer Science" in repr(app_obj)

    uri_custom = get_database_uri("postgres://user:pass@localhost:5432/db")
    assert uri_custom.startswith("postgresql+psycopg://")

    with mock.patch.dict(os.environ, {"POSTGRES_USER": "u", "POSTGRES_PASSWORD": "p"}, clear=True):
        assert "u:p@" in get_database_uri()

    with mock.patch.dict(os.environ, {"POSTGRES_USER": "only_u", "POSTGRES_PASSWORD": ""}, clear=True):
        assert "only_u@" in get_database_uri()

    with mock.patch.dict(os.environ, {"POSTGRES_USER": "", "POSTGRES_PASSWORD": "", "USER": ""}, clear=True):
        assert get_database_uri().startswith("postgresql+psycopg://localhost")

    # 14. Test scraper_service._run_scrape_and_sync real branch with mocks
    from src.app.scraper_service import scraper_manager
    scraper_manager.reset_state()
    scraper_manager.set_test_doubles(custom_scraper=None, custom_loader=None)
    with mock.patch("src.app.scraper_service.scrape_data", return_value=[(1, "<html><table><tr><td>JHU</td></tr></table></html>")]), \
         mock.patch("src.app.scraper_service.clean_data", return_value=[]), \
         mock.patch("src.app.scraper_service.generate_applicant_dataset", return_value=[{"p_id": 101, "program": "JHU CS"}]), \
         mock.patch("src.app.scraper_service.get_db_connection") as mock_svc_conn, \
         mock.patch("src.app.scraper_service.load_data_from_records", return_value=1):
        mock_c_inst = mock.MagicMock()
        mock_svc_conn.return_value = mock_c_inst
        scraper_manager.start_pull_data(max_pages=1, synchronous=True)
        assert scraper_manager.records_added == 1
        assert scraper_manager.is_running is False

    # 15. Test scraper_service error handling branch
    scraper_manager.reset_state()
    with mock.patch("src.app.scraper_service.scrape_data", side_effect=Exception("Network failure")):
        scraper_manager.start_pull_data(max_pages=1, synchronous=True)
        assert scraper_manager.is_running is False
        assert "Network failure" in scraper_manager.error_message

    # 16. Test scraper_service background thread start
    scraper_manager.reset_state()
    scraper_manager.set_test_doubles(
        custom_scraper=lambda: [{"p_id": 202, "program": "AI"}],
        custom_loader=lambda recs: len(recs)
    )
    scraper_manager.start_pull_data(synchronous=False)
    import time
    for _ in range(20):
        time.sleep(0.05)
        if not scraper_manager.is_running:
            break
    assert scraper_manager.records_added == 1

    # 17. Test execute_all_queries with self-contained connection (conn=None)
    res_queries = execute_all_queries(None)
    assert res_queries["q1"] >= 0

    # 18. Test execute_orm_queries with self-contained session (session=None)
    res_orm = execute_orm_queries(None)
    assert res_orm["q1"] >= 0

