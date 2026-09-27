"""
Database Schema, Insertion, and Idempotency Unit Tests.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

import pytest
from sqlalchemy import select, func

from src.load_data import create_applicants_table, get_db_connection, load_data_from_records
from src.models import Applicant, get_db_session
from src.query_data import execute_all_queries


@pytest.mark.db
def test_database_table_creation_and_schema():
    """
    Test that the applicants table exists with the required Module 3 columns.
    """
    conn = get_db_connection()
    try:
        create_applicants_table(conn)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'applicants';
            """)
            columns = {row[0]: row[1] for row in cur.fetchall()}

        required_cols = [
            "p_id", "program", "comments", "date_added", "url", "status",
            "term", "us_or_international", "gpa", "gre", "gre_v", "gre_aw",
            "degree", "llm_generated_program", "llm_generated_university"
        ]
        for col in required_cols:
            assert col in columns, f"Required column '{col}' missing from applicants table"
    finally:
        conn.close()


@pytest.mark.db
def test_db_insert_and_idempotency(sample_records):
    """
    Test inserting records, validating non-null values, and ensuring duplicate pulls do not create duplicate rows.
    """
    conn = get_db_connection()
    try:
        # Load sample records
        loaded_first = load_data_from_records(sample_records, conn)
        assert loaded_first == len(sample_records)

        # Query using SQLAlchemy
        session = get_db_session()
        try:
            r1 = session.get(Applicant, 999901)
            assert r1 is not None
            assert r1.p_id == 999901
            assert "Johns Hopkins" in r1.program
            assert r1.term == "Fall 2026"
            assert r1.gpa == 3.92
            assert r1.gre == 168.0
            assert r1.llm_generated_university == "Johns Hopkins University"

            # Repeat load with same records (Idempotency test)
            loaded_second = load_data_from_records(sample_records, conn)
            assert loaded_second == len(sample_records)

            # Count rows for this p_id to ensure no duplication
            count = session.scalar(select(func.count(Applicant.p_id)).where(Applicant.p_id == 999901))
            assert count == 1, "Duplicate records were created on repeated load"
        finally:
            session.close()
    finally:
        conn.close()


@pytest.mark.db
def test_query_function_returns_expected_keys():
    """
    Test that execute_all_queries returns a dictionary containing all expected Module 3 analytical keys.
    """
    conn = get_db_connection()
    try:
        results = execute_all_queries(conn)
        assert isinstance(results, dict)
        expected_keys = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10", "q11"]
        for key in expected_keys:
            assert key in results, f"Expected key '{key}' missing from execute_all_queries dictionary"

        # Check nested structures
        assert "gpa" in results["q3"]
        assert "gre" in results["q3"]
        assert "original" in results["q9"]
        assert "llm" in results["q9"]
        assert "diff" in results["q9"]
    finally:
        conn.close()
