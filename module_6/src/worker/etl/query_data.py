"""
Secure Raw SQL Query Analysis Module for Grad Café Admissions Data.
Module 5 - Software Assurance & Secure SQL (SQLi Defense)
Johns Hopkins University - Software Concepts (EN.605.601)

Features:
- SQL Injection Defense using psycopg safe composition (sql.SQL, sql.Identifier, sql.Placeholder).
- Complete separation of statement construction from parameter execution.
- Strict LIMIT enforcement and clamping across all queries.
- Least-privilege environment variable loading.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

DEFAULT_MAX_LIMIT: int = 100


def clamp_limit(
    limit: Optional[int],
    default_limit: int = 100,
    max_limit: int = DEFAULT_MAX_LIMIT,
) -> int:
    """
    Validate and clamp query LIMIT values to prevent denial of service or excessive exposure.

    :param limit: Requested limit (can be None or invalid)
    :param default_limit: Fallback limit if none provided or non-positive
    :param max_limit: Maximum permissible limit (hard ceiling)
    :return: Sanitized integer limit clamped between 1 and max_limit
    """
    if limit is None or not isinstance(limit, int) or limit <= 0:
        return default_limit
    return min(limit, max_limit)


def get_db_connection(custom_conninfo: Optional[str] = None) -> psycopg.Connection:
    """
    Establish a connection to the PostgreSQL database using environment variables
    or custom connection string with safe defaults.
    """
    database_url = custom_conninfo or os.environ.get("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)

    dbname = os.environ.get("DB_NAME", os.environ.get("POSTGRES_DB", "gradcafe_db"))
    user = os.environ.get(
        "DB_USER",
        os.environ.get("POSTGRES_USER", os.environ.get("USER", "postgres")),
    )
    password = os.environ.get("DB_PASSWORD", os.environ.get("POSTGRES_PASSWORD", ""))
    host = os.environ.get("DB_HOST", os.environ.get("POSTGRES_HOST", "localhost"))
    port = int(os.environ.get("DB_PORT", os.environ.get("POSTGRES_PORT", "5432")))

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


def run_question_1(conn: psycopg.Connection, term_pattern: str = "%Fall 2026%") -> int:
    """
    Question 1: How many entries are from applicants who applied for Fall 2026?
    Uses safe psycopg SQL composition and parameter binding.
    """
    stmt = sql.SQL(
        "SELECT COUNT(*) FROM {table} WHERE {term_col} ILIKE {param};"
    ).format(
        table=sql.Identifier("applicants"),
        term_col=sql.Identifier("term"),
        param=sql.Placeholder(),
    )
    with conn.cursor() as cur:
        cur.execute(stmt, (term_pattern,))
        row = cur.fetchone()
        result = row[0] if row else 0
    return int(result)


def run_question_2(conn: psycopg.Connection) -> float:
    """
    Question 2: Among entries providing nationality classification, what percentage
    are international students?
    """
    stmt = sql.SQL(
        """
        SELECT 
            COUNT(*) FILTER (WHERE LOWER({nat_col}) = %s) * 100.0 / 
            NULLIF(COUNT(*) FILTER (WHERE {nat_col} IS NOT NULL AND TRIM({nat_col}) <> %s), 0)
        FROM {table};
        """
    ).format(
        nat_col=sql.Identifier("us_or_international"),
        table=sql.Identifier("applicants"),
    )
    with conn.cursor() as cur:
        cur.execute(stmt, ("international", ""))
        row = cur.fetchone()
        result = row[0] if row and row[0] is not None else 0.0
    return float(result)


def run_question_3(conn: psycopg.Connection) -> Tuple[float, float, float, float]:
    """
    Question 3: Average GPA, GRE Quantitative, GRE Verbal, and GRE AW scores.
    """
    stmt = sql.SQL(
        """
        SELECT 
            AVG({gpa_col}) AS avg_gpa,
            AVG({gre_col}) AS avg_gre_quant,
            AVG({gre_v_col}) AS avg_gre_verbal,
            AVG({gre_aw_col}) AS avg_gre_aw
        FROM {table};
        """
    ).format(
        gpa_col=sql.Identifier("gpa"),
        gre_col=sql.Identifier("gre"),
        gre_v_col=sql.Identifier("gre_v"),
        gre_aw_col=sql.Identifier("gre_aw"),
        table=sql.Identifier("applicants"),
    )
    with conn.cursor() as cur:
        cur.execute(stmt)
        row = cur.fetchone()
        if not row:
            return 0.0, 0.0, 0.0, 0.0
        avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = row
    return (
        float(avg_gpa) if avg_gpa is not None else 0.0,
        float(avg_gre) if avg_gre is not None else 0.0,
        float(avg_gre_v) if avg_gre_v is not None else 0.0,
        float(avg_gre_aw) if avg_gre_aw is not None else 0.0,
    )


def run_question_4(
    conn: psycopg.Connection,
    term_pattern: str = "%Fall 2026%",
    origin: str = "american",
) -> float:
    """
    Question 4: Average GPA of American applicants applying for Fall 2026.
    """
    stmt = sql.SQL(
        """
        SELECT AVG({gpa_col}) 
        FROM {table} 
        WHERE {term_col} ILIKE %s 
          AND LOWER({origin_col}) = %s 
          AND {gpa_col} IS NOT NULL;
        """
    ).format(
        gpa_col=sql.Identifier("gpa"),
        table=sql.Identifier("applicants"),
        term_col=sql.Identifier("term"),
        origin_col=sql.Identifier("us_or_international"),
    )
    with conn.cursor() as cur:
        cur.execute(stmt, (term_pattern, origin.lower()))
        row = cur.fetchone()
        result = row[0] if row and row[0] is not None else 0.0
    return float(result)


def run_question_5(conn: psycopg.Connection, term_pattern: str = "%Fall 2025%") -> float:
    """
    Question 5: Percentage of Fall 2025 entries that are acceptances.
    """
    stmt = sql.SQL(
        """
        SELECT 
            COUNT(*) FILTER (WHERE {status_col} ILIKE %s) * 100.0 / 
            NULLIF(COUNT(*), 0)
        FROM {table} 
        WHERE {term_col} ILIKE %s;
        """
    ).format(
        status_col=sql.Identifier("status"),
        table=sql.Identifier("applicants"),
        term_col=sql.Identifier("term"),
    )
    with conn.cursor() as cur:
        cur.execute(stmt, ("%accept%", term_pattern))
        row = cur.fetchone()
        result = row[0] if row and row[0] is not None else 0.0
    return float(result)


def run_question_6(conn: psycopg.Connection, term_pattern: str = "%Fall 2026%") -> float:
    """
    Question 6: Average GPA of accepted applicants who applied for Fall 2026.
    """
    stmt = sql.SQL(
        """
        SELECT AVG({gpa_col}) 
        FROM {table} 
        WHERE {term_col} ILIKE %s 
          AND {status_col} ILIKE %s 
          AND {gpa_col} IS NOT NULL;
        """
    ).format(
        gpa_col=sql.Identifier("gpa"),
        table=sql.Identifier("applicants"),
        term_col=sql.Identifier("term"),
        status_col=sql.Identifier("status"),
    )
    with conn.cursor() as cur:
        cur.execute(stmt, (term_pattern, "%accept%"))
        row = cur.fetchone()
        result = row[0] if row and row[0] is not None else 0.0
    return float(result)


def run_question_7(conn: psycopg.Connection) -> int:
    """
    Question 7: JHU Computer Science Master's applicants using original fields.
    """
    stmt = sql.SQL(
        """
        SELECT COUNT(*) 
        FROM {table} 
        WHERE ({prog_col} ILIKE %s OR {prog_col} ILIKE %s)
          AND {prog_col} ILIKE %s
          AND {deg_col} ILIKE %s;
        """
    ).format(
        table=sql.Identifier("applicants"),
        prog_col=sql.Identifier("program"),
        deg_col=sql.Identifier("degree"),
    )
    with conn.cursor() as cur:
        cur.execute(stmt, ("%Johns Hopkins%", "%JHU%", "%Computer Science%", "%master%"))
        row = cur.fetchone()
        result = row[0] if row else 0
    return int(result)


def run_question_8(conn: psycopg.Connection) -> int:
    """
    Question 8: Fall 2026 accepted CS PhDs at Georgetown, MIT, Stanford, or CMU (original fields).
    """
    stmt = sql.SQL(
        """
        SELECT COUNT(*) 
        FROM {table} 
        WHERE {term_col} ILIKE %s
          AND {status_col} ILIKE %s
          AND {deg_col} ILIKE %s
          AND {prog_col} ILIKE %s
          AND (
              {prog_col} ILIKE %s 
              OR {prog_col} ILIKE %s
              OR {prog_col} ILIKE %s
              OR {prog_col} ILIKE %s
              OR {prog_col} ILIKE %s
          );
        """
    ).format(
        table=sql.Identifier("applicants"),
        term_col=sql.Identifier("term"),
        status_col=sql.Identifier("status"),
        deg_col=sql.Identifier("degree"),
        prog_col=sql.Identifier("program"),
    )
    params = (
        "%Fall 2026%",
        "%accept%",
        "%phd%",
        "%Computer Science%",
        "%Georgetown%",
        "%Massachusetts Institute of Technology%",
        "%MIT%",
        "%Stanford%",
        "%Carnegie Mellon%",
    )
    with conn.cursor() as cur:
        cur.execute(stmt, params)
        row = cur.fetchone()
        result = row[0] if row else 0
    return int(result)


def run_question_9(conn: psycopg.Connection) -> Tuple[int, int, int]:
    """
    Question 9: Repeat Question 8 using LLM-standardized university and program fields.
    Returns (q8_count, q9_count, difference).
    """
    q8_count = run_question_8(conn)

    stmt = sql.SQL(
        """
        SELECT COUNT(*) 
        FROM {table} 
        WHERE {term_col} ILIKE %s
          AND {status_col} ILIKE %s
          AND {deg_col} ILIKE %s
          AND {llm_prog_col} ILIKE %s
          AND (
              {llm_uni_col} ILIKE %s
              OR {llm_uni_col} ILIKE %s
              OR {llm_uni_col} ILIKE %s
              OR {llm_uni_col} ILIKE %s
              OR {llm_uni_col} ILIKE %s
          );
        """
    ).format(
        table=sql.Identifier("applicants"),
        term_col=sql.Identifier("term"),
        status_col=sql.Identifier("status"),
        deg_col=sql.Identifier("degree"),
        llm_prog_col=sql.Identifier("llm_generated_program"),
        llm_uni_col=sql.Identifier("llm_generated_university"),
    )
    params = (
        "%Fall 2026%",
        "%accept%",
        "%phd%",
        "%Computer Science%",
        "%Georgetown%",
        "%Massachusetts Institute of Technology%",
        "%MIT%",
        "%Stanford%",
        "%Carnegie Mellon%",
    )
    with conn.cursor() as cur:
        cur.execute(stmt, params)
        row = cur.fetchone()
        q9_count = int(row[0]) if row else 0

    diff = q9_count - q8_count
    return q8_count, q9_count, diff


def run_question_10(
    conn: psycopg.Connection,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Question 10 (Original Question 1): Top universities by CS applicants and acceptance rate.
    Enforces clamped LIMIT parameterization.
    """
    safe_limit = clamp_limit(limit, default_limit=5, max_limit=50)
    stmt = sql.SQL(
        """
        SELECT 
            {uni_col} AS university,
            COUNT(*) AS total_applicants,
            COUNT(*) FILTER (WHERE {status_col} ILIKE %s) AS accepted_count,
            ROUND(
                COUNT(*) FILTER (WHERE {status_col} ILIKE %s) * 100.0 / COUNT(*),
                2
            ) AS acceptance_rate_pct
        FROM {table}
        WHERE {prog_col} ILIKE %s
          AND {uni_col} IS NOT NULL
        GROUP BY {uni_col}
        ORDER BY total_applicants DESC, acceptance_rate_pct DESC
        LIMIT %s;
        """
    ).format(
        uni_col=sql.Identifier("llm_generated_university"),
        status_col=sql.Identifier("status"),
        table=sql.Identifier("applicants"),
        prog_col=sql.Identifier("llm_generated_program"),
    )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, ("%accept%", "%accept%", "%Computer Science%", safe_limit))
        return cur.fetchall()


def run_question_11(
    conn: psycopg.Connection,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Question 11 (Original Question 2): Accepted vs. Rejected metric comparison for Fall 2026.
    Enforces clamped LIMIT parameterization.
    """
    safe_limit = clamp_limit(limit, default_limit=10, max_limit=50)
    stmt = sql.SQL(
        """
        SELECT 
            CASE 
                WHEN {status_col} ILIKE %s THEN 'Accepted'
                WHEN {status_col} ILIKE %s THEN 'Rejected'
                ELSE 'Other'
            END AS admission_outcome,
            COUNT(*) AS applicant_count,
            ROUND(AVG({gpa_col})::numeric, 2) AS avg_gpa,
            ROUND(AVG({gre_col})::numeric, 2) AS avg_gre_quant
        FROM {table}
        WHERE {term_col} ILIKE %s
          AND ({status_col} ILIKE %s OR {status_col} ILIKE %s)
        GROUP BY admission_outcome
        ORDER BY admission_outcome ASC
        LIMIT %s;
        """
    ).format(
        status_col=sql.Identifier("status"),
        gpa_col=sql.Identifier("gpa"),
        gre_col=sql.Identifier("gre"),
        table=sql.Identifier("applicants"),
        term_col=sql.Identifier("term"),
    )
    params = (
        "%accept%",
        "%reject%",
        "%Fall 2026%",
        "%accept%",
        "%reject%",
        safe_limit,
    )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, params)
        return cur.fetchall()


def query_applicants_dynamic(
    conn: psycopg.Connection,
    table_name: str = "applicants",
    filter_column: str = "term",
    filter_value: str = "Fall 2026",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Safe dynamic query builder demonstrating SQL injection defense across identifiers and values.
    Validates identifiers against allow-list and parameterizes filter values and clamped limit.
    """
    allowed_tables = {"applicants"}
    allowed_columns = {
        "p_id",
        "program",
        "comments",
        "date_added",
        "url",
        "status",
        "term",
        "us_or_international",
        "gpa",
        "gre",
        "gre_v",
        "gre_aw",
        "degree",
        "llm_generated_program",
        "llm_generated_university",
    }

    if table_name not in allowed_tables:
        raise ValueError(f"Unauthorized table name identifier: {table_name}")
    if filter_column not in allowed_columns:
        raise ValueError(f"Unauthorized column name identifier: {filter_column}")

    safe_limit = clamp_limit(limit, default_limit=50, max_limit=100)

    stmt = sql.SQL(
        """
        SELECT * 
        FROM {table} 
        WHERE {column} ILIKE %s 
        ORDER BY {order_col} DESC 
        LIMIT %s;
        """
    ).format(
        table=sql.Identifier(table_name),
        column=sql.Identifier(filter_column),
        order_col=sql.Identifier("p_id"),
    )

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (f"%{filter_value}%", safe_limit))
        return cur.fetchall()


def execute_all_queries(conn: Optional[psycopg.Connection] = None) -> Dict[str, Any]:
    """
    Execute all 11 secure SQL queries and return structured dictionary of results.
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
    print("      GRAD CAFE DATABASE ANALYSIS - SECURE SQL QUERY RESULTS")
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
        print("\n[Question 8] Fall 2026 Accepted PhD CS (Top 4 Universities - Original):")
        print(f"Applicant count: {q8}")

        q8_c, q9_c, diff = run_question_9(conn)
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print("\n[Question 9] Fall 2026 Accepted PhD CS (LLM Standardized vs Original):")
        print(f"Original-field count: {q8_c}")
        print(f"LLM-field count: {q9_c}")
        print(f"Difference: {diff_str}")

        q10 = run_question_10(conn)
        print("\n[Question 10 - Original Question 1] Top 5 Universities by Volume:")
        for r in q10:
            uni = r['university']
            tot = r['total_applicants']
            acc = r['accepted_count']
            pct = r['acceptance_rate_pct']
            print(f"  - {uni}: {tot} applicants | {acc} accepted ({pct}%)")

        q11 = run_question_11(conn)
        print("\n[Question 11 - Original Question 2] Accepted vs. Rejected Metrics:")
        for r in q11:
            outcome = r['admission_outcome']
            cnt = r['applicant_count']
            avg_g = r['avg_gpa']
            avg_q = r['avg_gre_quant']
            print(f"  - {outcome}: Count = {cnt:,} | Avg GPA = {avg_g} | Avg GRE Quant = {avg_q}")

        print("\n" + "=" * 70)
    finally:
        conn.close()


if __name__ == "__main__":
    print_formatted_results()
