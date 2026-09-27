"""
Raw SQL Query Analysis Module for Grad Café Admissions Data.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)

Executes raw SQL queries via psycopg answering Questions 1 through 9
and 2 custom analytical questions adhering to all formatting rules.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import psycopg
from psycopg.rows import dict_row


def get_db_connection(custom_conninfo: Optional[str] = None):
    """
    Establish a connection to the PostgreSQL database using environment variables
    or custom string with default local fallbacks.
    """
    database_url = custom_conninfo or os.environ.get("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)

    dbname = os.environ.get("POSTGRES_DB", "gradcafe_db")
    user = os.environ.get("POSTGRES_USER", os.environ.get("USER", "postgres"))
    password = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))

    conn_kwargs: Dict[str, Any] = {
        "dbname": dbname,
        "host": host,
        "port": port,
    }
    if user:
        conn_kwargs["user"] = user
    if password:
        conn_kwargs["password"] = password

    return psycopg.connect(**conn_kwargs)


def run_question_1(conn: psycopg.Connection) -> int:
    """
    Question 1: How many entries in your database are from applicants who applied for Fall 2026?
    """
    query = "SELECT COUNT(*) FROM applicants WHERE term ILIKE '%Fall 2026%';"
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
    return int(result)


def run_question_2(conn: psycopg.Connection) -> float:
    """
    Question 2: Among entries that provide a nationality classification, what percentage are international students?
    """
    query = """
    SELECT 
        COUNT(*) FILTER (WHERE LOWER(us_or_international) = 'international') * 100.0 / 
        NULLIF(COUNT(*) FILTER (WHERE us_or_international IS NOT NULL AND TRIM(us_or_international) <> ''), 0)
    FROM applicants;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
    return float(result) if result is not None else 0.0


def run_question_3(conn: psycopg.Connection) -> Tuple[float, float, float, float]:
    """
    Question 3: What are the average GPA, GRE Quantitative, GRE Verbal, and GRE Analytical Writing scores
    of applicants who provide each metric?
    """
    query = """
    SELECT 
        AVG(gpa) AS avg_gpa,
        AVG(gre) AS avg_gre_quant,
        AVG(gre_v) AS avg_gre_verbal,
        AVG(gre_aw) AS avg_gre_aw
    FROM applicants;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = cur.fetchone()
    return (
        float(avg_gpa) if avg_gpa is not None else 0.0,
        float(avg_gre) if avg_gre is not None else 0.0,
        float(avg_gre_v) if avg_gre_v is not None else 0.0,
        float(avg_gre_aw) if avg_gre_aw is not None else 0.0,
    )


def run_question_4(conn: psycopg.Connection) -> float:
    """
    Question 4: What is the average GPA of American applicants who applied for Fall 2026?
    """
    query = """
    SELECT AVG(gpa) 
    FROM applicants 
    WHERE term ILIKE '%Fall 2026%' 
      AND LOWER(us_or_international) = 'american' 
      AND gpa IS NOT NULL;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
    return float(result) if result is not None else 0.0


def run_question_5(conn: psycopg.Connection) -> float:
    """
    Question 5: What percentage of Fall 2025 entries are acceptances?
    """
    query = """
    SELECT 
        COUNT(*) FILTER (WHERE status ILIKE '%accept%') * 100.0 / 
        NULLIF(COUNT(*), 0)
    FROM applicants 
    WHERE term ILIKE '%Fall 2025%';
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
    return float(result) if result is not None else 0.0


def run_question_6(conn: psycopg.Connection) -> float:
    """
    Question 6: What is the average GPA of accepted applicants who applied for Fall 2026?
    """
    query = """
    SELECT AVG(gpa) 
    FROM applicants 
    WHERE term ILIKE '%Fall 2026%' 
      AND status ILIKE '%accept%' 
      AND gpa IS NOT NULL;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
    return float(result) if result is not None else 0.0


def run_question_7(conn: psycopg.Connection) -> int:
    """
    Question 7: How many entries are from applicants who applied to Johns Hopkins University
    for a master's degree in Computer Science using original fields?
    """
    query = """
    SELECT COUNT(*) 
    FROM applicants 
    WHERE (program ILIKE '%Johns Hopkins%' OR program ILIKE '%JHU%')
      AND program ILIKE '%Computer Science%'
      AND degree ILIKE '%master%';
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
    return int(result)


def run_question_8(conn: psycopg.Connection) -> int:
    """
    Question 8: Using original downloaded fields, how many Fall 2026 entries are acceptances
    from applicants applying for a PhD in Computer Science at Georgetown, MIT, Stanford, or CMU?
    """
    query = """
    SELECT COUNT(*) 
    FROM applicants 
    WHERE term ILIKE '%Fall 2026%'
      AND status ILIKE '%accept%'
      AND degree ILIKE '%phd%'
      AND program ILIKE '%Computer Science%'
      AND (
          program ILIKE '%Georgetown%' 
          OR program ILIKE '%Massachusetts Institute of Technology%'
          OR program ILIKE '%MIT%'
          OR program ILIKE '%Stanford%'
          OR program ILIKE '%Carnegie Mellon%'
      );
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()[0]
    return int(result)


def run_question_9(conn: psycopg.Connection) -> Tuple[int, int, int]:
    """
    Question 9: Repeat Question 8 using LLM-generated university and program fields.
    Returns (q8_count, q9_count, difference).
    """
    q8_count = run_question_8(conn)

    query = """
    SELECT COUNT(*) 
    FROM applicants 
    WHERE term ILIKE '%Fall 2026%'
      AND status ILIKE '%accept%'
      AND degree ILIKE '%phd%'
      AND llm_generated_program ILIKE '%Computer Science%'
      AND (
          llm_generated_university ILIKE '%Georgetown%'
          OR llm_generated_university ILIKE '%Massachusetts Institute of Technology%'
          OR llm_generated_university ILIKE '%MIT%'
          OR llm_generated_university ILIKE '%Stanford%'
          OR llm_generated_university ILIKE '%Carnegie Mellon%'
      );
    """
    with conn.cursor() as cur:
        cur.execute(query)
        q9_count = int(cur.fetchone()[0])

    diff = q9_count - q8_count
    return q8_count, q9_count, diff


def run_question_10(conn: psycopg.Connection) -> List[Dict[str, Any]]:
    """
    Question 10 (Original Question 1):
    What are the top 5 universities with the highest total number of Computer Science applicant submissions,
    and what is the acceptance rate at each?
    """
    query = """
    SELECT 
        llm_generated_university AS university,
        COUNT(*) AS total_applicants,
        COUNT(*) FILTER (WHERE status ILIKE '%accept%') AS accepted_count,
        ROUND(COUNT(*) FILTER (WHERE status ILIKE '%accept%') * 100.0 / COUNT(*), 2) AS acceptance_rate_pct
    FROM applicants
    WHERE llm_generated_program ILIKE '%Computer Science%'
      AND llm_generated_university IS NOT NULL
    GROUP BY llm_generated_university
    ORDER BY total_applicants DESC, acceptance_rate_pct DESC
    LIMIT 5;
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query)
        return cur.fetchall()


def run_question_11(conn: psycopg.Connection) -> List[Dict[str, Any]]:
    """
    Question 11 (Original Question 2):
    For Fall 2026 applicants, how do the average GPA and average GRE Quantitative scores compare
    between Accepted applicants and Rejected applicants?
    """
    query = """
    SELECT 
        CASE 
            WHEN status ILIKE '%accept%' THEN 'Accepted'
            WHEN status ILIKE '%reject%' THEN 'Rejected'
            ELSE 'Other'
        END AS admission_outcome,
        COUNT(*) AS applicant_count,
        ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
        ROUND(AVG(gre)::numeric, 2) AS avg_gre_quant
    FROM applicants
    WHERE term ILIKE '%Fall 2026%'
      AND (status ILIKE '%accept%' OR status ILIKE '%reject%')
    GROUP BY admission_outcome
    ORDER BY admission_outcome ASC;
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query)
        return cur.fetchall()


def execute_all_queries(conn: Optional[psycopg.Connection] = None) -> Dict[str, Any]:
    """
    Execute all 11 SQL queries and return structured dictionary of results.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    try:
        q1 = run_question_1(conn)
        q2 = run_question_2(conn)
        gpa, gre, gre_v, gre_aw = run_question_3(conn)
        q4 = run_question_4(conn)
        q5 = run_question_5(conn)
        q6 = run_question_6(conn)
        q7 = run_question_7(conn)
        q8 = run_question_8(conn)
        q8_c, q9_c, diff = run_question_9(conn)
        q10 = run_question_10(conn)
        q11 = run_question_11(conn)

        return {
            "q1": q1,
            "q2": q2,
            "q3": {"gpa": gpa, "gre": gre, "gre_v": gre_v, "gre_aw": gre_aw},
            "q4": q4,
            "q5": q5,
            "q6": q6,
            "q7": q7,
            "q8": q8,
            "q9": {"original": q8_c, "llm": q9_c, "diff": diff},
            "q10": q10,
            "q11": q11,
        }
    finally:
        if should_close:
            conn.close()


def print_formatted_results() -> None:
    """
    Print query analysis results to console following exact assignment specifications.
    """
    print("=" * 70)
    print("      GRAD CAFE DATABASE ANALYSIS - RAW SQL QUERY RESULTS")
    print("=" * 70)

    conn = get_db_connection()
    try:
        q1 = run_question_1(conn)
        print("\n[Question 1] Fall 2026 Applicant Count:")
        print(f"Fall 2026 applicant count: {q1:,}")

        q2 = run_question_2(conn)
        print("\n[Question 2] International Students Percentage:")
        print(f"Percent international: {q2:.2f}%")

        gpa, gre, gre_v, gre_aw = run_question_3(conn)
        print("\n[Question 3] Overall Metric Averages:")
        print(f"Average GPA: {gpa:.2f}")
        print(f"Average GRE Quantitative: {gre:.2f}")
        print(f"Average GRE Verbal: {gre_v:.2f}")
        print(f"Average GRE Analytical Writing: {gre_aw:.2f}")

        q4 = run_question_4(conn)
        print("\n[Question 4] Average GPA of American Fall 2026 Applicants:")
        print(f"Average GPA: {q4:.2f}")

        q5 = run_question_5(conn)
        print("\n[Question 5] Fall 2025 Acceptance Percentage:")
        print(f"Fall 2025 acceptance percentage: {q5:.2f}%")

        q6 = run_question_6(conn)
        print("\n[Question 6] Average GPA of Accepted Fall 2026 Applicants:")
        print(f"Average GPA: {q6:.2f}")

        q7 = run_question_7(conn)
        print("\n[Question 7] JHU Computer Science Master's Applicants (Original Fields):")
        print(f"Applicant count: {q7:,}")

        q8 = run_question_8(conn)
        print("\n[Question 8] Fall 2026 Accepted PhD CS (Georgetown, MIT, Stanford, CMU - Original Fields):")
        print(f"Applicant count: {q8}")

        q8_c, q9_c, diff = run_question_9(conn)
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print("\n[Question 9] Fall 2026 Accepted PhD CS (LLM Standardized Fields vs Original):")
        print(f"Original-field count: {q8_c}")
        print(f"LLM-field count: {q9_c}")
        print(f"Difference: {diff_str}")

        q10 = run_question_10(conn)
        print("\n[Question 10 - Original Question 1] Top 5 Universities by CS Applicant Volume & Acceptance Rate:")
        for r in q10:
            print(f"  - {r['university']}: {r['total_applicants']} applicants | {r['accepted_count']} accepted ({r['acceptance_rate_pct']}%)")

        q11 = run_question_11(conn)
        print("\n[Question 11 - Original Question 2] Accepted vs. Rejected Fall 2026 Metric Comparison:")
        for r in q11:
            print(f"  - {r['admission_outcome']}: Count = {r['applicant_count']:,} | Avg GPA = {r['avg_gpa']} | Avg GRE Quant = {r['avg_gre_quant']}")

        print("\n" + "=" * 70)
    finally:
        conn.close()


if __name__ == "__main__":
    print_formatted_results()
