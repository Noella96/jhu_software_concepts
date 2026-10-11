"""
Unit Tests for Database Loader and Watermark Management.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import datetime
import json
from unittest.mock import MagicMock, patch
import pytest

from src.db.load_data import (
    create_all_tables,
    create_applicants_table,
    create_watermarks_table,
    get_db_connection,
    get_db_connection_params,
    get_watermark,
    load_data_from_json,
    load_data_from_records,
    main as db_main,
    parse_date,
    parse_numeric,
    parse_p_id,
    parse_text,
    update_watermark,
)


@pytest.mark.db
def test_get_db_connection_params(monkeypatch):
    """Test connection params extraction with and without DATABASE_URL."""
    custom = get_db_connection_params("postgresql://user:pass@host:5432/db")
    assert custom == {"conninfo": "postgresql://user:pass@host:5432/db"}

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_NAME", "my_db")
    monkeypatch.setenv("DB_USER", "my_user")
    monkeypatch.setenv("DB_PASSWORD", "my_pass")
    monkeypatch.setenv("DB_HOST", "my_host")
    monkeypatch.setenv("DB_PORT", "5435")

    params = get_db_connection_params()
    assert params["dbname"] == "my_db"
    assert params["user"] == "my_user"
    assert params["password"] == "my_pass"
    assert params["host"] == "my_host"
    assert params["port"] == 5435


@pytest.mark.db
def test_get_db_connection():
    """Test get_db_connection handles both conninfo and keyword arguments."""
    with patch("psycopg.connect") as mock_connect:
        get_db_connection("postgresql://localhost:5432/db")
        mock_connect.assert_called_with("postgresql://localhost:5432/db")


@pytest.mark.db
def test_create_tables():
    """Test create_applicants_table and create_watermarks_table execute DDL."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    create_applicants_table(mock_conn)
    create_watermarks_table(mock_conn)
    create_all_tables(mock_conn)
    assert mock_cur.execute.call_count >= 3
    assert mock_conn.commit.call_count >= 3


@pytest.mark.db
def test_watermark_operations():
    """Test get_watermark and update_watermark behavior."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_cur.fetchone.return_value = ("2026-03-15",)
    res = get_watermark(mock_conn, "test_source")
    assert res == "2026-03-15"

    mock_cur.fetchone.return_value = None
    res_none = get_watermark(mock_conn, "empty_source")
    assert res_none is None

    update_watermark(mock_conn, "test_source", "2026-04-01")
    assert mock_cur.execute.call_count >= 1


@pytest.mark.db
def test_parsers():
    """Test parsing helper functions for p_id, date, numeric, and text."""
    assert parse_p_id("https://thegradcafe.com/result/12345", 1) == 12345
    assert parse_p_id("id_67890", 1) == 67890
    assert parse_p_id("", 99) == 99

    assert parse_date("Added on March 31, 2026") == datetime.date(2026, 3, 31)
    assert parse_date("2026-03-31") == datetime.date(2026, 3, 31)
    assert parse_date(None) is None
    assert parse_date("invalid_date") is None

    assert parse_numeric(3.88) == 3.88
    assert parse_numeric("GPA 3.95") == 3.95
    assert parse_numeric(None) is None
    assert parse_numeric("no_numbers") is None

    assert parse_text("  Harvard University  ") == "Harvard University"
    assert parse_text(None) is None
    assert parse_text("   ") is None


@pytest.mark.db
def test_load_data_from_json(tmp_path, sample_records):
    """Test loading records from temporary JSON file and missing file handling."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    with pytest.raises(FileNotFoundError):
        load_data_from_json("/nonexistent/file.json", mock_conn)

    data_file = tmp_path / "test_data.json"
    data_file.write_text(json.dumps(sample_records), encoding="utf-8")

    rec_loaded = load_data_from_records(sample_records, mock_conn)
    assert rec_loaded == len(sample_records)

    inserted, total = load_data_from_json(str(data_file), mock_conn)
    assert inserted == len(sample_records)
    assert total == len(sample_records)


@pytest.mark.db
def test_db_main_routine():
    """Test main() database loading entrypoint."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = (500,)

    with patch("src.db.load_data.get_db_connection", return_value=mock_conn), \
         patch("src.db.load_data.load_data_from_json", return_value=(10, 10)), \
         patch("os.path.exists", return_value=True):
        db_main()
        mock_conn.close.assert_called_once()

    # Connection failure branch
    with patch("src.db.load_data.get_db_connection", side_effect=Exception("DB Fail")):
        db_main()
