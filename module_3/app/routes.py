"""
Flask Application Routes for Admissions Analysis Dashboard.
Module 3 - Johns Hopkins University Software Concepts (EN.605.601)

Connects to PostgreSQL using the SQLAlchemy Applicant model to dynamically serve
analysis metrics, trigger background data pulls, and handle analysis refreshes.
"""
from __future__ import annotations

from typing import Any, Dict
from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func, select

from module_3.app.scraper_service import scraper_manager
from module_3.models import Applicant, get_db_session
from module_3.orm_queries import (
    orm_question_1,
    orm_question_4,
    orm_question_5,
    orm_question_8,
    orm_question_9,
    orm_question_10,
)
from module_3.query_data import (
    run_question_2,
    run_question_3,
    run_question_6,
    run_question_7,
    run_question_11,
)

main_bp = Blueprint("main", __name__)


def fetch_all_dashboard_data() -> Dict[str, Any]:
    """
    Fetch all 11 analysis metrics from PostgreSQL using SQLAlchemy ORM (and helper models).
    """
    session = get_db_session()
    try:
        # Total rows in DB
        total_records = session.scalar(select(func.count(Applicant.p_id))) or 0

        # Question 1 (ORM)
        q1 = orm_question_1(session)

        # Question 2 (SQL / Connection helper)
        conn = session.connection().connection
        q2 = run_question_2(conn)

        # Question 3 (Overall averages)
        gpa, gre, gre_v, gre_aw = run_question_3(conn)

        # Question 4 (ORM)
        q4 = orm_question_4(session)

        # Question 5 (ORM)
        q5 = orm_question_5(session)

        # Question 6
        q6 = run_question_6(conn)

        # Question 7
        q7 = run_question_7(conn)

        # Question 8 (ORM)
        q8 = orm_question_8(session)

        # Question 9 (ORM)
        q8_c, q9_c, diff = orm_question_9(session)

        # Question 10 (ORM - Original 1)
        q10 = orm_question_10(session)

        # Question 11 (Original 2)
        q11 = run_question_11(conn)

        return {
            "total_records": total_records,
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
        session.close()


@main_bp.route("/")
def index():
    """
    Render main dynamic admissions analysis dashboard.
    """
    data = fetch_all_dashboard_data()
    status_info = scraper_manager.get_status()
    return render_template("analysis.html", data=data, status_info=status_info)


@main_bp.route("/api/update-analysis", methods=["GET", "POST"])
def update_analysis():
    """
    Re-query PostgreSQL database and return current analysis metrics.
    Does not initiate a scrape; alerts user if a scrape is active.
    """
    status_info = scraper_manager.get_status()
    data = fetch_all_dashboard_data()
    return jsonify({
        "success": True,
        "is_scraping": status_info["is_running"],
        "status_message": status_info["status"],
        "data": data,
    })


@main_bp.route("/api/pull-data", methods=["POST"])
def pull_data():
    """
    Trigger background scraping and ingestion of newly submitted Grad Café entries.
    """
    started = scraper_manager.start_pull_data()
    if started:
        return jsonify({
            "success": True,
            "message": "Pull Data started. Scraping Grad Café for newly submitted application results...",
            "is_running": True
        })
    else:
        return jsonify({
            "success": False,
            "message": "A data pull is already in progress. Please wait for it to complete.",
            "is_running": True
        }), 409


@main_bp.route("/api/status", methods=["GET"])
def get_status():
    """
    Get current scraper execution status.
    """
    return jsonify(scraper_manager.get_status())
