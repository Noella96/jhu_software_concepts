"""
SQLAlchemy ORM Query Analysis Module for Grad Café Admissions Data.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)

Executes pure SQLAlchemy 2.0 ORM queries repeating Questions 1, 4, 5, 8, 9,
and Original Question 10 without using raw SQL or text() constructs.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, case, cast, desc, func, or_, select, Float, Integer, Numeric
from sqlalchemy.orm import Session

try:
    from src.models import Applicant, get_db_session
except ImportError:
    try:
        from module_4.src.models import Applicant, get_db_session
    except ImportError:
        from models import Applicant, get_db_session


def orm_question_1(session: Session) -> int:
    """
    Question 1: How many entries in your database are from applicants who applied for Fall 2026?
    """
    stmt = select(func.count(Applicant.p_id)).where(
        Applicant.term.ilike("%Fall 2026%")
    )
    result = session.scalar(stmt)
    return int(result) if result is not None else 0


def orm_question_4(session: Session) -> float:
    """
    Question 4: What is the average GPA of American applicants who applied for Fall 2026?
    """
    stmt = select(func.avg(Applicant.gpa)).where(
        and_(
            Applicant.term.ilike("%Fall 2026%"),
            func.lower(Applicant.us_or_international) == "american",
            Applicant.gpa.isnot(None)
        )
    )
    result = session.scalar(stmt)
    return float(result) if result is not None else 0.0


def orm_question_5(session: Session) -> float:
    """
    Question 5: What percentage of Fall 2025 entries are acceptances?
    """
    accepted_case = case((Applicant.status.ilike("%accept%"), 1), else_=0)
    stmt = select(
        cast(func.sum(accepted_case), Float) * 100.0 / func.nullif(func.count(Applicant.p_id), 0)
    ).where(
        Applicant.term.ilike("%Fall 2025%")
    )
    result = session.scalar(stmt)
    return float(result) if result is not None else 0.0


def orm_question_8(session: Session) -> int:
    """
    Question 8: Using original downloaded fields, how many Fall 2026 entries are acceptances
    from applicants applying for a PhD in Computer Science at Georgetown, MIT, Stanford, or CMU?
    """
    uni_filters = or_(
        Applicant.program.ilike("%Georgetown%"),
        Applicant.program.ilike("%Massachusetts Institute of Technology%"),
        Applicant.program.ilike("%MIT%"),
        Applicant.program.ilike("%Stanford%"),
        Applicant.program.ilike("%Carnegie Mellon%")
    )

    stmt = select(func.count(Applicant.p_id)).where(
        and_(
            Applicant.term.ilike("%Fall 2026%"),
            Applicant.status.ilike("%accept%"),
            Applicant.degree.ilike("%phd%"),
            Applicant.program.ilike("%Computer Science%"),
            uni_filters
        )
    )
    result = session.scalar(stmt)
    return int(result) if result is not None else 0


def orm_question_9(session: Session) -> Tuple[int, int, int]:
    """
    Question 9: Repeat Question 8 using LLM-generated university and program fields.
    Returns (q8_count, q9_count, difference).
    """
    q8_count = orm_question_8(session)

    uni_filters = or_(
        Applicant.llm_generated_university.ilike("%Georgetown%"),
        Applicant.llm_generated_university.ilike("%Massachusetts Institute of Technology%"),
        Applicant.llm_generated_university.ilike("%MIT%"),
        Applicant.llm_generated_university.ilike("%Stanford%"),
        Applicant.llm_generated_university.ilike("%Carnegie Mellon%")
    )

    stmt = select(func.count(Applicant.p_id)).where(
        and_(
            Applicant.term.ilike("%Fall 2026%"),
            Applicant.status.ilike("%accept%"),
            Applicant.degree.ilike("%phd%"),
            Applicant.llm_generated_program.ilike("%Computer Science%"),
            uni_filters
        )
    )
    q9_count = int(session.scalar(stmt) or 0)
    diff = q9_count - q8_count
    return q8_count, q9_count, diff


def orm_question_10(session: Session) -> List[Dict[str, Any]]:
    """
    Original Question 10: Top 5 Universities by Computer Science Applicant Volume & Acceptance Rate.
    """
    accepted_case = case((Applicant.status.ilike("%accept%"), 1), else_=0)
    pct_expr = cast(func.sum(accepted_case) * 100.0 / func.count(Applicant.p_id), Numeric)
    stmt = select(
        Applicant.llm_generated_university.label("university"),
        func.count(Applicant.p_id).label("total_applicants"),
        func.sum(accepted_case).label("accepted_count"),
        func.round(pct_expr, 2).label("acceptance_rate_pct")
    ).where(
        and_(
            Applicant.llm_generated_program.ilike("%Computer Science%"),
            Applicant.llm_generated_university.isnot(None)
        )
    ).group_by(
        Applicant.llm_generated_university
    ).order_by(
        desc("total_applicants"),
        desc("acceptance_rate_pct")
    ).limit(5)

    results = session.execute(stmt).all()
    output: List[Dict[str, Any]] = []
    for row in results:
        output.append({
            "university": row.university,
            "total_applicants": int(row.total_applicants),
            "accepted_count": int(row.accepted_count),
            "acceptance_rate_pct": float(row.acceptance_rate_pct),
        })
    return output


def execute_orm_queries(session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Execute all ORM queries and return dictionary of results.
    """
    should_close = False
    if session is None:
        session = get_db_session()
        should_close = True

    try:
        q1 = orm_question_1(session)
        q4 = orm_question_4(session)
        q5 = orm_question_5(session)
        q8 = orm_question_8(session)
        q8_c, q9_c, diff = orm_question_9(session)
        q10 = orm_question_10(session)

        return {
            "q1": q1,
            "q4": q4,
            "q5": q5,
            "q8": q8,
            "q9": {"original": q8_c, "llm": q9_c, "diff": diff},
            "q10": q10,
        }
    finally:
        if should_close:
            session.close()


def print_formatted_orm_results() -> None:
    """
    Print ORM analysis results to console following exact assignment specifications.
    """
    print("=" * 70)
    print("      GRAD CAFE DATABASE ANALYSIS - SQLALCHEMY ORM RESULTS")
    print("=" * 70)

    session = get_db_session()
    try:
        q1 = orm_question_1(session)
        print("\n[Question 1] Fall 2026 Applicant Count (ORM):")
        print(f"Fall 2026 applicant count: {q1:,}")

        q4 = orm_question_4(session)
        print("\n[Question 4] Average GPA of American Fall 2026 Applicants (ORM):")
        print(f"Average GPA: {q4:.2f}")

        q5 = orm_question_5(session)
        print("\n[Question 5] Fall 2025 Acceptance Percentage (ORM):")
        print(f"Fall 2025 acceptance percentage: {q5:.2f}%")

        q8 = orm_question_8(session)
        print("\n[Question 8] Fall 2026 Accepted PhD CS (Georgetown, MIT, Stanford, CMU - Original Fields - ORM):")
        print(f"Applicant count: {q8}")

        q8_c, q9_c, diff = orm_question_9(session)
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print("\n[Question 9] Fall 2026 Accepted PhD CS (LLM Standardized Fields vs Original - ORM):")
        print(f"Original-field count: {q8_c}")
        print(f"LLM-field count: {q9_c}")
        print(f"Difference: {diff_str}")

        q10 = orm_question_10(session)
        print("\n[Question 10 - Original Question 1] Top 5 Universities by CS Applicant Volume & Acceptance Rate (ORM):")
        for r in q10:
            print(f"  - {r['university']}: {r['total_applicants']} applicants | {r['accepted_count']} accepted ({r['acceptance_rate_pct']}%)")

        print("\n" + "=" * 70)
    finally:
        session.close()


if __name__ == "__main__":
    print_formatted_orm_results()
