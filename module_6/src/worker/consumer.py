"""
RabbitMQ Worker Consumer and Task Processing Engine.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)

Features:
- Long-running AMQP consumer with backpressure (basic_qos prefetch_count=1).
- Durable exchange ('tasks') and durable queue ('tasks_q') declarations.
- Per-message PostgreSQL transactions committing only on success.
- Idempotent incremental scraper handler ('handle_scrape_new_data') with watermark advancing.
- Analytics recomputation handler ('handle_recompute_analytics').
- Guaranteed message acknowledgment (basic_ack) on commit, basic_nack(requeue=False) on error.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Callable, Dict, Optional, Tuple

import pika
import psycopg
from psycopg import sql

try:
    from src.worker.etl.clean import clean_data, generate_applicant_dataset
    from src.worker.etl.incremental_scraper import scrape_data
    from src.worker.etl.query_data import execute_all_queries
    from src.worker.etl.standardize import standardize_dataset
except ImportError:  # pragma: no cover
    from etl.clean import clean_data, generate_applicant_dataset
    from etl.incremental_scraper import scrape_data
    from etl.query_data import execute_all_queries
    from etl.standardize import standardize_dataset

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [worker] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gradcafe_worker")

EXCHANGE_NAME = "tasks"
QUEUE_NAME = "tasks_q"
ROUTING_KEY = "tasks"


def get_db_connection(custom_url: Optional[str] = None) -> psycopg.Connection:
    """Establish a connection to the PostgreSQL database."""
    db_url = custom_url or os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg.connect(db_url)

    dbname = os.environ.get("DB_NAME", os.environ.get("POSTGRES_DB", "gradcafe_db"))
    user = os.environ.get(
        "DB_USER",
        os.environ.get("POSTGRES_USER", os.environ.get("USER", "postgres")),
    )
    password = os.environ.get("DB_PASSWORD", os.environ.get("POSTGRES_PASSWORD", ""))
    host = os.environ.get("DB_HOST", os.environ.get("POSTGRES_HOST", "localhost"))
    port = int(os.environ.get("DB_PORT", os.environ.get("POSTGRES_PORT", "5432")))

    return psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def get_watermark(conn: psycopg.Connection, source: str = "gradcafe_scraper") -> Optional[str]:
    """Retrieve last seen watermark for incremental scraping."""
    stmt = sql.SQL(
        "SELECT last_seen FROM {table} WHERE source = %s;"
    ).format(table=sql.Identifier("ingestion_watermarks"))

    with conn.cursor() as cur:
        cur.execute(stmt, (source,))
        row = cur.fetchone()
        if row and row[0] is not None:
            return str(row[0])
    return None


def update_watermark(conn: psycopg.Connection, source: str, last_seen: str) -> None:
    """Update high watermark in ingestion_watermarks table."""
    stmt = sql.SQL(
        """
        INSERT INTO {table} (source, last_seen, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (source) DO UPDATE SET
            last_seen = EXCLUDED.last_seen,
            updated_at = now();
        """
    ).format(table=sql.Identifier("ingestion_watermarks"))

    with conn.cursor() as cur:
        cur.execute(stmt, (source, last_seen))


def insert_applicant_records(
    conn: psycopg.Connection, records: list[dict[str, Any]]
) -> int:
    """
    Batch insert applicant records into PostgreSQL using parameterized SQL and idempotency.
    """
    if not records:
        return 0

    stmt = sql.SQL(
        """
        INSERT INTO {table} (
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
    ).format(table=sql.Identifier("applicants"))

    with conn.cursor() as cur:
        cur.executemany(stmt, records)

    return len(records)


def handle_scrape_new_data(
    conn: psycopg.Connection,
    payload: Dict[str, Any],
    scraper_fn: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    """
    Handle 'scrape_new_data' task kind:
    - Reads watermark (or uses payload['since'] if provided).
    - Fetches fresh admissions results.
    - Cleans and standardizes new records.
    - Idempotently inserts records into database.
    - Advances watermark to maximum seen date/id after commit.
    """
    source = payload.get("source", "gradcafe_scraper")
    watermark = payload.get("since") or get_watermark(conn, source)
    logger.info("Executing scrape_new_data task (source=%s, watermark=%s)", source, watermark)

    records: list[dict[str, Any]] = []
    if scraper_fn:
        records = scraper_fn(watermark)
    else:
        # Default scraper flow: pull latest page
        try:
            raw_pages = scrape_data(start_page=1, end_page=2, delay=0.1, max_workers=2)
            parsed = []
            for _, html in raw_pages:
                if html:
                    parsed.extend(clean_data(html))
            dataset = generate_applicant_dataset(parsed)
            records = standardize_dataset(dataset)
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.warning("Network scrape produced notice: %s. Using local seed data.", err)
            data_file = os.path.join(os.path.dirname(__file__), "..", "data", "applicant_data.json")
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as file:
                    records = json.load(file)[:50]

    inserted = insert_applicant_records(conn, records)

    # Determine latest watermark from batch
    max_seen = watermark or "2026-03-31"
    for rec in records:
        date_str = str(rec.get("date_added", ""))
        if date_str and date_str > max_seen:
            max_seen = date_str

    update_watermark(conn, source, max_seen)
    logger.info(
        "scrape_new_data finished: inserted=%d, new_watermark=%s",
        inserted,
        max_seen,
    )
    return {"inserted": inserted, "watermark": max_seen}


def handle_recompute_analytics(
    conn: psycopg.Connection, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle 'recompute_analytics' task kind:
    - Recomputes analytical summary metrics or materialized queries.
    - Commits on success within per-message transaction.
    """
    logger.info("Executing recompute_analytics task (payload=%s)", payload)
    results = execute_all_queries(conn)
    total_metrics = len(results)
    logger.info(
        "recompute_analytics completed successfully: %d metrics recalculated", total_metrics
    )
    return {"recomputed_metrics": total_metrics, "status": "completed"}


TASK_HANDLERS: Dict[str, Callable[[psycopg.Connection, Dict[str, Any]], Dict[str, Any]]] = {
    "scrape_new_data": handle_scrape_new_data,
    "recompute_analytics": handle_recompute_analytics,
}


def process_message(
    ch: Any,
    method: Any,
    properties: Any,
    body: bytes,
    db_conn: Optional[psycopg.Connection] = None,
) -> bool:
    """
    Parse JSON message, execute routed task within a dedicated DB transaction,
    and acknowledge (basic_ack) on success or reject (basic_nack) on error.
    """
    del properties
    delivery_tag = method.delivery_tag

    try:
        data = json.loads(body.decode("utf-8"))
    except Exception as parse_err:  # pylint: disable=broad-exception-caught
        logger.error("Malformed JSON received. Rejecting without requeue: %s", parse_err)
        ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
        return False

    kind = data.get("kind")
    payload = data.get("payload", {})
    if kind not in ("scrape_new_data", "recompute_analytics"):
        logger.error("Unknown task kind '%s'. Rejecting without requeue.", kind)
        ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
        return False

    conn = db_conn or get_db_connection()
    should_close = db_conn is None

    try:
        # Open DB transaction per message
        with conn.transaction():
            logger.info("Processing task '%s' within DB transaction...", kind)
            if kind == "scrape_new_data":
                handle_scrape_new_data(conn, payload)
            elif kind == "recompute_analytics":
                handle_recompute_analytics(conn, payload)

        # Acknowledge only after commit
        ch.basic_ack(delivery_tag=delivery_tag)
        logger.info(
            "Task '%s' successfully processed and acknowledged (tag=%s)", kind, delivery_tag
        )
        return True
    except Exception as task_err:  # pylint: disable=broad-exception-caught
        logger.error("Error executing task '%s': %s. Rolling back and nacking.", kind, task_err)
        try:
            conn.rollback()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
        return False
    finally:
        if should_close:
            conn.close()


def setup_consumer(
    rabbitmq_url: Optional[str] = None,
) -> Tuple[pika.BlockingConnection, Any]:
    """
    Initialize durable exchange, queue, and channel with prefetch_count=1 backpressure.
    """
    url = rabbitmq_url or os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2f")
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Declare durable direct exchange and durable queue
    ch.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)

    # Set backpressure: process one task at a time
    ch.basic_qos(prefetch_count=1)
    return conn, ch


def run_worker() -> None:
    """Launch the long-running worker consumer loop."""
    logger.info("[*] Starting GradCafé Worker Consumer...")
    conn, ch = setup_consumer()

    def on_message(channel, method, properties, body):
        process_message(channel, method, properties, body)

    ch.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)
    logger.info("[*] Worker waiting for messages on queue '%s'. To exit press CTRL+C", QUEUE_NAME)

    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        logger.info("[!] Stopping worker consumer...")
        ch.stop_consuming()
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        run_worker()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Fatal error in worker: %s", exc)
        sys.exit(1)
