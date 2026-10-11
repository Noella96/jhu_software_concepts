"""
Comprehensive Unit Tests for ETL Pipeline, Analytics Queries, Models, and CLI Runners.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import pytest

from src.web.models import Applicant, get_database_uri, get_db_session, get_engine
from src.web.orm_queries import (
    execute_orm_queries,
    orm_question_1,
    orm_question_4,
    orm_question_5,
    orm_question_8,
    orm_question_9,
    orm_question_10,
    print_formatted_orm_results,
)
from src.web.query_data import (
    clamp_limit,
    execute_all_queries,
    get_db_connection as get_raw_db_conn,
    print_formatted_results,
    query_applicants_dynamic,
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
from src.worker.etl.clean import (
    _extract_degree,
    _extract_metrics,
    _extract_origin,
    _normalize_status,
    _parse_entry,
    clean_data,
    generate_applicant_dataset,
    load_data,
    main as clean_main,
    save_data,
)
from src.worker.etl.incremental_scraper import (
    build_page_url,
    check_robots_compliance,
    fetch_page_html,
    fetch_single_page_job,
    main as scraper_main,
    scrape_data,
)
from src.worker.etl.standardize import (
    main as standardize_main,
    standardize_dataset,
    standardize_program_and_university,
    standardize_records,
)


@pytest.mark.analysis
def test_clean_helpers_and_dataset(tmp_path):
    """Test cleaning extraction functions and dataset serialization."""
    assert _normalize_status("") == "Accepted"
    assert _normalize_status("Accepted on 1 Mar") == "Accepted on 1 Mar"

    assert _extract_degree("PhD in Computer Science") == "PhD"
    assert _extract_degree("Master of Science") == "Masters"
    assert _extract_degree("Certificate") == "Masters"

    assert _extract_origin("American citizen") == "American"
    assert _extract_origin("International student") == "International"

    m = _extract_metrics("GPA of 3.88 GRE of 165 GRE V of 160 GRE AW of 4.5")
    assert m["GPA"] == "GPA 3.88"
    assert m["GRE"] == "GRE 165"
    assert not _extract_metrics("No scores")

    row_html = (
        "<tr><td>MIT</td><td>Computer Science</td><td>Accepted</td>"
        "<td>GPA 3.90 GRE 168</td><td>Added on March 1, 2026</td>"
        "<td>Good</td><td>Fall 2026</td><td>American</td><td>PhD</td></tr>"
    )
    soup = BeautifulSoup(row_html, "html.parser")
    parsed = _parse_entry(soup.find("tr"), base_id=1001)
    assert parsed is not None
    assert "MIT" in parsed["program"]

    assert _parse_entry(BeautifulSoup("<div>empty</div>", "html.parser"), base_id=1002) is not None
    assert _parse_entry(None) is None

    dataset = generate_applicant_dataset(count=5)
    assert len(dataset) >= 5

    cleaned = clean_data([f"<table>{row_html}</table>"])
    assert len(cleaned) >= 1

    tfile = tmp_path / "data.json"
    save_data(dataset[:2], str(tfile))
    loaded = load_data(str(tfile))
    assert len(loaded) == 2


@pytest.mark.analysis
def test_standardize_helpers(tmp_path):
    """Test standardization and canonical university matching."""
    p1, u1 = standardize_program_and_university("")
    assert p1 == "General Program" and u1 == "Unknown University"

    p2, u2 = standardize_program_and_university("Computer Science")
    assert p2 == "Computer Science" and u2 == "Unknown University"

    p3, u3 = standardize_program_and_university("Informatics, JHU ")
    assert p3 == "Informatics" and u3 == "Johns Hopkins University"

    recs = standardize_records([{"program": "Robotics, CMU "}])
    assert recs[0]["llm_generated_university"] == "Carnegie Mellon University"

    t_in = tmp_path / "in.json"
    t_out = tmp_path / "out.json"
    t_in.write_text(json.dumps([{"program": "AI, MIT "}]), encoding="utf-8")
    out = standardize_dataset(str(t_in), str(t_out))
    assert len(out) == 1
    assert os.path.exists(t_out)
    assert not standardize_dataset(None)


@pytest.mark.worker
def test_scraper_module():
    """Test web scraper URL builder, robots checker, and page fetchers."""
    url = build_page_url(2, "computer science")
    assert "page=2" in url
    assert "computer+science" in url

    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"User-agent: *\nDisallow: /private\n"
        mock_url.return_value.__enter__.return_value = mock_resp
        assert check_robots_compliance() is True

        # Test robots exception fallback
        mock_url.side_effect = Exception("Network error")
        assert check_robots_compliance() is True

    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"<html>Survey Results</html>"
        mock_url.return_value.__enter__.return_value = mock_resp
        html = fetch_page_html("https://thegradcafe.com/survey/index.php")
        assert html == "<html>Survey Results</html>"

    with patch("src.worker.etl.incremental_scraper.fetch_page_html", return_value="<html></html>"):
        page_num, res_html = fetch_single_page_job(1, delay=0.0)
        assert page_num == 1
        assert res_html == "<html></html>"

    with patch("src.worker.etl.incremental_scraper.check_robots_compliance", return_value=True), \
         patch(
             "src.worker.etl.incremental_scraper.fetch_single_page_job",
             return_value=(1, "<html></html>"),
         ):
        pages = scrape_data(start_page=1, end_page=2, delay=0.0, max_workers=2)
        assert len(pages) == 2


@pytest.mark.web
def test_models_and_session(monkeypatch):
    """Test SQLAlchemy model representations and connection factories."""
    app_obj = Applicant(p_id=555, program="Data Science", status="Accepted")
    assert "Data Science" in repr(app_obj)

    uri1 = get_database_uri("postgres://user:pass@host:5432/db")
    assert uri1.startswith("postgresql+psycopg://")

    uri2 = get_database_uri("postgresql://user:pass@host:5432/db")
    assert uri2.startswith("postgresql+psycopg://")

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_NAME", "gradcafe_db")
    uri3 = get_database_uri()
    assert "gradcafe_db" in uri3

    engine = get_engine("sqlite:///:memory:")
    assert engine is not None

    session = get_db_session("sqlite:///:memory:")
    assert session is not None
    session.close()


@pytest.mark.analysis
def test_orm_queries_suite():
    """Test ORM analytical query functions with mock session."""
    mock_session = MagicMock()
    mock_session.scalar.return_value = 42

    mock_row = MagicMock()
    mock_row.university = "MIT"
    mock_row.total_applicants = 100
    mock_row.accepted_count = 50
    mock_row.acceptance_rate_pct = 50.0
    mock_session.execute.return_value.all.return_value = [mock_row]

    assert orm_question_1(mock_session) == 42
    assert orm_question_4(mock_session) == 42.0
    assert orm_question_5(mock_session) == 42.0
    assert orm_question_8(mock_session) == 42

    q10_res = orm_question_10(mock_session)
    assert len(q10_res) == 1
    assert q10_res[0]["university"] == "MIT"

    with patch("src.web.orm_queries.orm_question_8", return_value=10):
        q8_c, q9_c, diff = orm_question_9(mock_session)
        assert q8_c == 10
        assert q9_c == 42
        assert diff == 32

    sample_uni = [{
        "university": "MIT", "total_applicants": 10,
        "accepted_count": 5, "acceptance_rate_pct": 50.0,
    }]
    with patch("src.web.orm_queries.orm_question_9", return_value=(10, 12, 2)), \
         patch("src.web.orm_queries.orm_question_10", return_value=sample_uni):
        all_res = execute_orm_queries(mock_session)
        assert "q1" in all_res

        with patch("src.web.orm_queries.get_db_session", return_value=mock_session):
            print_formatted_orm_results()


@pytest.mark.db
def test_query_data_raw_suite():
    """Test secure raw query functions and clamp limit."""
    assert clamp_limit(None, 20, 100) == 20
    assert clamp_limit(-5, 20, 100) == 20
    assert clamp_limit(150, 20, 100) == 100
    assert clamp_limit(50, 20, 100) == 50

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    sample_uni = [{
        "university": "CS", "total_applicants": 10,
        "accepted_count": 5, "acceptance_rate_pct": 50.0,
    }]
    mock_cur.fetchone.return_value = (99, 99, 99, 99)
    mock_cur.fetchall.return_value = sample_uni

    assert run_question_1(mock_conn) == 99
    assert run_question_2(mock_conn) == 99
    assert run_question_3(mock_conn) == (99, 99, 99, 99)
    assert run_question_4(mock_conn) == 99
    assert run_question_5(mock_conn) == 99
    assert run_question_6(mock_conn) == 99
    assert run_question_7(mock_conn) == 99
    assert run_question_8(mock_conn) == 99
    assert run_question_9(mock_conn) == (99, 99, 0)
    assert len(run_question_10(mock_conn)) == 1
    assert len(run_question_11(mock_conn)) == 1

    res = query_applicants_dynamic(
        conn=mock_conn,
        table_name="applicants",
        filter_column="program",
        filter_value="CS",
        limit=10,
    )
    assert len(res) == 1

    with pytest.raises(ValueError, match="Unauthorized column"):
        query_applicants_dynamic(
            conn=mock_conn,
            table_name="applicants",
            filter_column="invalid_col",
            filter_value="CS",
            limit=10,
        )

    all_raw = execute_all_queries(mock_conn)
    assert "q1" in all_raw

    sample_outcome = [{
        "admission_outcome": "Accepted", "applicant_count": 10,
        "avg_gpa": 3.8, "avg_gre_quant": 165,
    }]
    with patch("src.web.query_data.get_db_connection", return_value=mock_conn), \
         patch("src.web.query_data.run_question_10", return_value=sample_uni), \
         patch("src.web.query_data.run_question_11", return_value=sample_outcome):
        print_formatted_results()

    with patch("psycopg.connect") as mock_psycopg:
        get_raw_db_conn("postgresql://localhost:5432/db")
        mock_psycopg.assert_called_with("postgresql://localhost:5432/db")


@pytest.mark.analysis
def test_cli_runners_entrypoints():
    """Test main() CLI entrypoint execution across all pipeline modules."""
    with patch("sys.argv", ["prog"]), \
         patch("src.worker.etl.clean.generate_applicant_dataset", return_value=[]), \
         patch("src.worker.etl.clean.save_data"):
        clean_main()

    with patch("sys.argv", ["prog"]), \
         patch("src.worker.etl.standardize.standardize_dataset", return_value=[]):
        standardize_main()

    with patch("sys.argv", ["prog"]), \
         patch("src.worker.etl.incremental_scraper.scrape_data", return_value=[]):
        scraper_main()

    with patch("src.web.orm_queries.orm_question_9", return_value=(10, 10, 0)), \
         patch("src.web.orm_queries.orm_question_10", return_value=[]):
        print_formatted_orm_results()

    with patch("src.web.query_data.run_question_3", return_value=(3.8, 165, 160, 4.5)), \
         patch("src.web.query_data.run_question_9", return_value=(10, 10, 0)), \
         patch("src.web.query_data.run_question_10", return_value=[]), \
         patch("src.web.query_data.run_question_11", return_value=[]):
        print_formatted_results()
