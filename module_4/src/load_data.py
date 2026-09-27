"""
Data Loader Module for Grad Café Admissions Data.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)

Connects to PostgreSQL using psycopg, creates the required 'applicants' table,
and idempotently loads cleaned applicant data handling missing values and data type conversions.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg
from psycopg.rows import dict_row


def get_db_connection_params(custom_conninfo: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve database connection configuration from environment variables or custom string
    with safe default fallbacks for local execution.
    """
    database_url = custom_conninfo or os.environ.get("DATABASE_URL")
    if database_url:
        return {"conninfo": database_url}

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

    return conn_kwargs


def get_db_connection(custom_conninfo: Optional[str] = None):
    """
    Establish a connection to the PostgreSQL database.
    """
    params = get_db_connection_params(custom_conninfo)
    if "conninfo" in params:
        return psycopg.connect(params["conninfo"])
    return psycopg.connect(**params)


def create_applicants_table(conn: psycopg.Connection) -> None:
    """
    Create the 'applicants' table if it does not already exist.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id INTEGER PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa FLOAT,
        gre FLOAT,
        gre_v FLOAT,
        gre_aw FLOAT,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_table_sql)
    conn.commit()


def parse_p_id(url: str, default_id: int) -> int:
    """
    Extract numeric unique identifier (p_id) from entry URL.
    """
    if url:
        match = re.search(r"/result/(\d+)", str(url))
        if match:
            return int(match.group(1))
        # Support pure integer strings or digits
        digit_match = re.search(r"(\d+)", str(url))
        if digit_match:
            return int(digit_match.group(1))
    return default_id


def parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """
    Parse date string into a Python date object.
    Supports formats like 'Added on March 31, 2024', 'March 31, 2024', '2024-03-31'.
    """
    if not date_str:
        return None
    cleaned = re.sub(r"^Added on\s*", "", str(date_str), flags=re.IGNORECASE).strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def parse_numeric(val: Any) -> Optional[float]:
    """
    Extract float score from strings like 'GPA 3.88', 'GRE 165', '165.0', or None.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", val_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_text(val: Any) -> Optional[str]:
    """
    Normalize text string, returning None for blank or missing values.
    """
    if val is None:
        return None
    cleaned = str(val).strip()
    return cleaned if cleaned else None


def load_data_from_records(records: List[Dict[str, Any]], conn: psycopg.Connection) -> int:
    """
    Load a list of dictionary applicant records into PostgreSQL applicants table.
    """
    insert_sql = """
    INSERT INTO applicants (
        p_id, program, comments, date_added, url, status, term,
        us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    ) VALUES (
        %(p_id)s, %(program)s, %(comments)s, %(date_added)s, %(url)s, %(status)s, %(term)s,
        %(us_or_international)s, %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s, %(degree)s,
        %(llm_generated_program)s, %(llm_generated_university)s
    )
    ON CONFLICT (p_id) DO UPDATE SET
        program = EXCLUDED.program,
        comments = EXCLUDED.comments,
        date_added = EXCLUDED.date_added,
        url = EXCLUDED.url,
        status = EXCLUDED.status,
        term = EXCLUDED.term,
        us_or_international = EXCLUDED.us_or_international,
        gpa = EXCLUDED.gpa,
        gre = EXCLUDED.gre,
        gre_v = EXCLUDED.gre_v,
        gre_aw = EXCLUDED.gre_aw,
        degree = EXCLUDED.degree,
        llm_generated_program = EXCLUDED.llm_generated_program,
        llm_generated_university = EXCLUDED.llm_generated_university;
    """

    prepared_data: List[Dict[str, Any]] = []
    for idx, r in enumerate(records):
        url = r.get("url", "")
        p_id = r.get("p_id")
        if p_id is None:
            p_id = parse_p_id(url, idx + 1)
        else:
            p_id = int(p_id)

        row = {
            "p_id": p_id,
            "program": parse_text(r.get("program")),
            "comments": parse_text(r.get("comments")),
            "date_added": parse_date(r.get("date_added")),
            "url": parse_text(url),
            "status": parse_text(r.get("status")),
            "term": parse_text(r.get("term")),
            "us_or_international": parse_text(r.get("us_or_international") or r.get("US/International")),
            "gpa": parse_numeric(r.get("gpa") or r.get("GPA")),
            "gre": parse_numeric(r.get("gre") or r.get("GRE")),
            "gre_v": parse_numeric(r.get("gre_v") or r.get("GRE V")),
            "gre_aw": parse_numeric(r.get("gre_aw") or r.get("GRE AW")),
            "degree": parse_text(r.get("degree") or r.get("Degree")),
            "llm_generated_program": parse_text(r.get("llm_generated_program") or r.get("llm-generated-program")),
            "llm_generated_university": parse_text(r.get("llm_generated_university") or r.get("llm-generated-university")),
        }
        prepared_data.append(row)

    with conn.cursor() as cur:
        cur.executemany(insert_sql, prepared_data)
    conn.commit()

    return len(prepared_data)


def load_data_from_json(json_path: str, conn: psycopg.Connection) -> Tuple[int, int]:
    """
    Load applicant records from a JSON file into PostgreSQL applicants table.
    Returns a tuple of (inserted_count, total_records).
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Data file not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    inserted = load_data_from_records(records, conn)
    return inserted, len(records)


def main():
    """
    Main data loading routine.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    primary_json = os.path.join(base_dir, "llm_extend_applicant_data.json")
    fallback_json = os.path.join(base_dir, "applicant_data.json")

    data_file = primary_json if os.path.exists(primary_json) else fallback_json

    print(f"[+] Connecting to PostgreSQL database...")
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    print(f"[+] Ensuring 'applicants' table exists...")
    create_applicants_table(conn)

    print(f"[+] Loading records from {os.path.basename(data_file)}...")
    loaded, total = load_data_from_json(data_file, conn)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        count = cur.fetchone()[0]

    conn.close()
    print(f"[+] Successfully loaded {loaded} records into PostgreSQL 'applicants' table.")
    print(f"[+] Total rows in database: {count:,}")


if __name__ == "__main__":
    main()
