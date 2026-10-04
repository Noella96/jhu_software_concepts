"""
Flask Application Routes for Admissions Analysis Dashboard.
Module 5 - Software Assurance & Secure SQL (SQLi Defense)
Johns Hopkins University - Software Concepts (EN.605.601)

Features:
- Dynamic analysis metrics serving via ORM and secure SQL.
- Hardened endpoints with parameterized search (/api/applicants) defending against SQL injection.
- Strict LIMIT clamping and validation on user queries.
"""
from __future__ import annotations

from typing import Any, Dict
from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func, select

from src.app.scraper_service import scraper_manager
from src.models import Applicant, get_db_session
from src.orm_queries import (
    orm_question_1,
    orm_question_4,
    orm_question_5,
    orm_question_8,
    orm_question_9,
    orm_question_10,
)
from src.query_data import (
    clamp_limit,
    query_applicants_dynamic,
    run_question_2,
    run_question_3,
    run_question_6,
    run_question_7,
    run_question_11,
)

main_bp = Blueprint("main", __name__)


def fetch_all_dashboard_data(custom_session=None) -> Dict[str, Any]:
    """
    Fetch all 11 analysis metrics from PostgreSQL using SQLAlchemy ORM and secure raw queries.
    """
    session = custom_session or get_db_session()
    should_close = custom_session is None
    try:
        total_records = session.scalar(select(func.count(Applicant.p_id))) or 0
        q1 = orm_question_1(session)

        # Use connection for raw SQL queries
        raw_conn = session.connection().connection
        q2 = run_question_2(raw_conn)
        gpa, gre, gre_v, gre_aw = run_question_3(raw_conn)
        q4 = orm_question_4(session)
        q5 = orm_question_5(session)
        q6 = run_question_6(raw_conn)
        q7 = run_question_7(raw_conn)
        q8 = orm_question_8(session)
        q8_c, q9_c, diff = orm_question_9(session)
        q10 = orm_question_10(session)
        q11 = run_question_11(raw_conn)

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
        if should_close:
            session.close()


@main_bp.route("/")
@main_bp.route("/analysis")
def index():
    """
    Render main dynamic admissions analysis dashboard.
    """
    data = fetch_all_dashboard_data()
    status_info = scraper_manager.get_status()
    return render_template("analysis.html", data=data, status_info=status_info)


@main_bp.route("/update-analysis", methods=["GET", "POST"])
@main_bp.route("/api/update-analysis", methods=["GET", "POST"])
def update_analysis():
    """
    Re-query PostgreSQL database and return current analysis metrics.
    Returns 409 {"busy": true} when a pull is currently in progress.
    """
    status_info = scraper_manager.get_status()
    if status_info.get("is_running") or status_info.get("busy"):
        return jsonify({
            "ok": False,
            "success": False,
            "busy": True,
            "error": "A data pull is currently in progress. Please wait for it to complete.",
            "status_message": status_info["status"]
        }), 409

    data = fetch_all_dashboard_data()
    return jsonify({
        "ok": True,
        "success": True,
        "busy": False,
        "is_scraping": False,
        "status_message": status_info["status"],
        "data": data,
    }), 200


@main_bp.route("/pull-data", methods=["POST"])
@main_bp.route("/api/pull-data", methods=["POST"])
def pull_data():
    """
    Trigger background scraping and ingestion of newly submitted Grad Café entries.
    Returns 200/202 {"ok": true} when started, or 409 {"busy": true} if already running.
    """
    json_data = request.get_json(silent=True) if request.is_json else {}
    sync_mode = request.args.get("sync", "false").lower() == "true" or (
        bool(json_data and json_data.get("sync") is True)
    )
    started = scraper_manager.start_pull_data(synchronous=sync_mode)
    if started:
        return jsonify({
            "ok": True,
            "success": True,
            "busy": False,
            "message": (
                "Pull Data started. Scraping Grad Café for newly submitted application results..."
            ),
            "is_running": not sync_mode
        }), 200

    return jsonify({
        "ok": False,
        "success": False,
        "busy": True,
        "error": "A data pull is already in progress. Please wait for it to complete.",
        "message": "A data pull is already in progress. Please wait for it to complete.",
        "is_running": True
    }), 409


@main_bp.route("/api/applicants", methods=["GET"])
def search_applicants():
    """
    Secure search endpoint demonstrating SQL injection defense and LIMIT clamping.
    Accepts filter_column, filter_value, and limit query parameters.
    """
    filter_col = request.args.get("column", "program")
    filter_val = request.args.get("value", "")
    raw_limit = request.args.get("limit", 20)
    try:
        limit_val = int(raw_limit)
    except (ValueError, TypeError):
        limit_val = 20

    session = get_db_session()
    try:
        raw_conn = session.connection().connection
        results = query_applicants_dynamic(
            conn=raw_conn,
            table_name="applicants",
            filter_column=filter_col,
            filter_value=filter_val,
            limit=limit_val,
        )
        return jsonify({
            "ok": True,
            "count": len(results),
            "limit_applied": clamp_limit(limit_val, default_limit=20, max_limit=100),
            "results": results,
        }), 200
    except ValueError as err:
        return jsonify({"ok": False, "error": str(err)}), 400
    finally:
        session.close()


@main_bp.route("/api/status", methods=["GET"])
def get_status():
    """
    Get current scraper execution status.
    """
    return jsonify(scraper_manager.get_status()), 200
