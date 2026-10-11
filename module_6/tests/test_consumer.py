"""
Unit Tests for RabbitMQ Worker Consumer and Task Processing Engine.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from src.worker.consumer import (
    EXCHANGE_NAME,
    QUEUE_NAME,
    ROUTING_KEY,
    get_db_connection,
    get_watermark,
    handle_recompute_analytics,
    handle_scrape_new_data,
    insert_applicant_records,
    process_message,
    setup_consumer,
    update_watermark,
)


@pytest.mark.worker
def test_get_db_connection_custom_url():
    """Test get_db_connection uses custom URL when provided."""
    with patch("psycopg.connect") as mock_connect:
        get_db_connection("postgresql://user:pass@localhost:5432/testdb")
        mock_connect.assert_called_once_with("postgresql://user:pass@localhost:5432/testdb")


@pytest.mark.worker
def test_get_db_connection_env_vars(monkeypatch):
    """Test get_db_connection constructs connection from environment variables."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_NAME", "custom_db")
    monkeypatch.setenv("DB_USER", "custom_user")
    monkeypatch.setenv("DB_PASSWORD", "custom_pass")
    monkeypatch.setenv("DB_HOST", "custom_host")
    monkeypatch.setenv("DB_PORT", "5433")

    with patch("psycopg.connect") as mock_connect:
        get_db_connection()
        mock_connect.assert_called_once_with(
            dbname="custom_db",
            user="custom_user",
            password="custom_pass",
            host="custom_host",
            port=5433,
        )


@pytest.mark.worker
def test_get_watermark_present():
    """Test get_watermark returns last_seen string when entry exists in database."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = ("2026-03-31",)

    watermark = get_watermark(mock_conn, "gradcafe_scraper")
    assert watermark == "2026-03-31"


@pytest.mark.worker
def test_get_watermark_absent():
    """Test get_watermark returns None when no watermark record is found."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = None

    watermark = get_watermark(mock_conn, "nonexistent")
    assert watermark is None


@pytest.mark.worker
def test_update_watermark():
    """Test update_watermark executes parameterized UPSERT on ingestion_watermarks."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    update_watermark(mock_conn, "gradcafe_scraper", "2026-04-01")
    assert mock_cur.execute.call_count == 1
    args = mock_cur.execute.call_args[0]
    assert ("gradcafe_scraper", "2026-04-01") in args


@pytest.mark.worker
def test_insert_applicant_records_empty():
    """Test insert_applicant_records safely handles empty record list."""
    mock_conn = MagicMock()
    count = insert_applicant_records(mock_conn, [])
    assert count == 0


@pytest.mark.worker
def test_insert_applicant_records(sample_records):
    """Test insert_applicant_records executes batch executemany statement."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    inserted = insert_applicant_records(mock_conn, sample_records)
    assert inserted == len(sample_records)
    mock_cur.executemany.assert_called_once()


@pytest.mark.worker
def test_handle_scrape_new_data_with_custom_scraper(sample_records):
    """Test handle_scrape_new_data with injected scraper function and watermark advance."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = ("2026-02-01",)

    def custom_scraper(since):
        del since
        return sample_records

    result = handle_scrape_new_data(
        mock_conn,
        payload={"source": "test_src"},
        scraper_fn=custom_scraper,
    )
    assert result["inserted"] == len(sample_records)
    assert result["watermark"] >= "2026-02-01"


@pytest.mark.worker
def test_handle_recompute_analytics():
    """Test handle_recompute_analytics executes analytical query suite."""
    mock_conn = MagicMock()
    with patch("src.worker.consumer.execute_all_queries", return_value={"q1": 10, "q2": 20}):
        result = handle_recompute_analytics(mock_conn, payload={})
        assert result["recomputed_metrics"] == 2
        assert result["status"] == "completed"


@pytest.mark.worker
def test_process_message_malformed_json():
    """Test process_message rejects malformed non-JSON payloads without requeuing."""
    mock_ch = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 101

    result = process_message(mock_ch, mock_method, None, b"not valid json")
    assert result is False
    mock_ch.basic_nack.assert_called_once_with(delivery_tag=101, requeue=False)
    mock_ch.basic_ack.assert_not_called()


@pytest.mark.worker
def test_process_message_unknown_kind():
    """Test process_message rejects unknown task kinds without requeuing."""
    mock_ch = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 102
    body = json.dumps({"kind": "unsupported_task"}).encode("utf-8")

    result = process_message(mock_ch, mock_method, None, body)
    assert result is False
    mock_ch.basic_nack.assert_called_once_with(delivery_tag=102, requeue=False)
    mock_ch.basic_ack.assert_not_called()


@pytest.mark.worker
def test_process_message_success():
    """Test process_message executes task within DB transaction and acknowledges."""
    mock_ch = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 103
    mock_conn = MagicMock()

    body = json.dumps({"kind": "recompute_analytics", "payload": {}}).encode("utf-8")

    with patch("src.worker.consumer.handle_recompute_analytics", return_value={"ok": True}):
        result = process_message(mock_ch, mock_method, None, body, db_conn=mock_conn)
        assert result is True
        mock_ch.basic_ack.assert_called_once_with(delivery_tag=103)
        mock_ch.basic_nack.assert_not_called()


@pytest.mark.worker
def test_process_message_handler_error():
    """Test process_message rolls back transaction and nacks on handler failure."""
    mock_ch = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 104
    mock_conn = MagicMock()

    body = json.dumps({"kind": "recompute_analytics", "payload": {}}).encode("utf-8")

    with patch(
        "src.worker.consumer.handle_recompute_analytics", side_effect=ValueError("DB Error")
    ):
        result = process_message(mock_ch, mock_method, None, body, db_conn=mock_conn)
        assert result is False
        mock_conn.rollback.assert_called_once()
        mock_ch.basic_nack.assert_called_once_with(delivery_tag=104, requeue=False)
        mock_ch.basic_ack.assert_not_called()


@pytest.mark.worker
def test_setup_consumer():
    """Test setup_consumer configures durable exchange/queue and prefetch_count=1."""
    with patch("pika.BlockingConnection") as mock_conn_cls:
        mock_conn = MagicMock()
        mock_ch = MagicMock()
        mock_conn.channel.return_value = mock_ch
        mock_conn_cls.return_value = mock_conn

        conn, channel = setup_consumer("amqp://guest:guest@localhost:5672/%2f")
        assert conn == mock_conn
        assert channel == mock_ch

        mock_ch.exchange_declare.assert_called_once_with(
            exchange=EXCHANGE_NAME, exchange_type="direct", durable=True
        )
        mock_ch.queue_declare.assert_called_once_with(
            queue=QUEUE_NAME, durable=True
        )
        mock_ch.queue_bind.assert_called_once_with(
            exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY
        )
        mock_ch.basic_qos.assert_called_once_with(prefetch_count=1)
