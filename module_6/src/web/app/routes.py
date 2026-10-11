"""
Flask Application Routes for Admissions Analysis Dashboard.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)

Features:
- Stateless presentation tier offloading long-running/write tasks to RabbitMQ.
- Button click endpoints (/pull-data, /update-analysis) publish AMQP tasks and
  immediately return HTTP 202.
- 503 Service Unavailable error response on broker failure.
- Read-only dashboard queries with SQL injection defense.
"""
from __future__ import annotations

from typing import Any, Dict
from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func, select

try:
    from models import Applicant, get_db_session
    from orm_queries import (
        orm_question_1,
        orm_question_4,
        orm_question_5,
        orm_question_8,
        orm_question_9,
        orm_question_10,
    )
    from publisher import publish_task
    from query_data import (
        clamp_limit,
        query_applicants_dynamic,
        run_question_2,
        run_question_3,
        run_question_6,
        run_question_7,
        run_question_11,
    )
except ImportError:
    from src.web.models import Applicant, get_db_session
    from src.web.orm_queries import (
        orm_question_1,
        orm_question_4,
        orm_question_5,
        orm_question_8,
        orm_question_9,
        orm_question_10,
    )
    from src.web.publisher import publish_task
    from src.web.query_data import (
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
    Fetch all 11 analysis metrics from PostgreSQL using SQLAlchemy ORM and secure queries.
    """
    session = custom_session or get_db_session()
    should_close = custom_session is None
    try:
        total_records = session.scalar(select(func.count(Applicant.p_id))) or 0
        q1 = orm_question_1(session)

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
    """Render main dynamic admissions analysis dashboard."""
    try:
        data = fetch_all_dashboard_data()
    except Exception:  # pylint: disable=broad-exception-caught
        data = {
            "total_records": 0,
            "q1": 0,
            "q2": 0,
            "q3": {"gpa": 0, "gre": 0, "gre_v": 0, "gre_aw": 0},
            "q4": 0,
            "q5": 0,
            "q6": 0,
            "q7": 0,
            "q8": 0,
            "q9": {"original": 0, "llm": 0, "diff": 0},
            "q10": [],
            "q11": [],
        }

    status_info = {
        "status": "Operational. Tasks queued via RabbitMQ message broker.",
        "is_running": False,
        "busy": False,
    }
    return render_template("analysis.html", data=data, status_info=status_info)


@main_bp.route("/pull-data", methods=["POST"])
@main_bp.route("/api/pull-data", methods=["POST"])
def pull_data():
    """
    Publish an asynchronous 'scrape_new_data' task to RabbitMQ tasks queue.
    Immediately returns HTTP 202 (Accepted) with queued status banner.
    Returns HTTP 503 on message broker publishing failure.
    """
    payload = {"source": "gradcafe_scraper"}
    try:
        publish_task(kind="scrape_new_data", payload=payload)
        return jsonify({
            "ok": True,
            "status": "queued",
            "kind": "scrape_new_data",
            "message": "Task queued: scrape_new_data. Worker is processing in background.",
            "status_message": "Task queued to RabbitMQ: scrape_new_data",
        }), 202
    except Exception as err:  # pylint: disable=broad-exception-caught
        return jsonify({
            "ok": False,
            "error": "Failed to publish scrape task to RabbitMQ broker",
            "details": str(err),
        }), 503


@main_bp.route("/update-analysis", methods=["GET", "POST"])
@main_bp.route("/api/update-analysis", methods=["GET", "POST"])
def update_analysis():
    """
    On POST: Enqueue asynchronous 'recompute_analytics' task via RabbitMQ returning HTTP 202.
    On GET: Re-query database and return latest analysis metrics as JSON.
    """
    if request.method == "POST":
        try:
            publish_task(kind="recompute_analytics", payload={})
            return jsonify({
                "ok": True,
                "status": "queued",
                "kind": "recompute_analytics",
                "message": "Task queued: recompute_analytics. Worker is updating analytics.",
                "status_message": "Task queued to RabbitMQ: recompute_analytics",
            }), 202
        except Exception as err:  # pylint: disable=broad-exception-caught
            return jsonify({
                "ok": False,
                "error": "Failed to publish recompute task to RabbitMQ broker",
                "details": str(err),
            }), 503

    # Handle GET request: return freshly computed metrics
    data = fetch_all_dashboard_data()
    return jsonify({
        "ok": True,
        "success": True,
        "busy": False,
        "status_message": "Analytics up to date.",
        "data": data,
    }), 200


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
    """Get current microservice broker and web service operational status."""
    return jsonify({
        "status": "operational",
        "service": "gradcafe_web",
        "broker": "rabbitmq",
        "worker_mode": "async",
    }), 200
