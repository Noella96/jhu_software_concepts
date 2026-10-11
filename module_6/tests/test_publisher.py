"""
Unit Tests for RabbitMQ Task Publisher.
Module 6 - Deploy Anywhere Assignment (Decoupled Microservice Architecture)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from src.web.publisher import (
    EXCHANGE_NAME,
    QUEUE_NAME,
    ROUTING_KEY,
    _open_channel,
    get_rabbitmq_url,
    publish_task,
)


@pytest.mark.publisher
def test_get_rabbitmq_url_default(monkeypatch):
    """Test get_rabbitmq_url returns fallback localhost AMQP URL when env is unset."""
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    url = get_rabbitmq_url()
    assert "amqp://" in url
    assert "localhost:5672" in url


@pytest.mark.publisher
def test_get_rabbitmq_url_from_env(monkeypatch):
    """Test get_rabbitmq_url retrieves custom RABBITMQ_URL when configured."""
    custom = "amqp://testuser:testpass@custom-rmq:5672/testvhost"
    monkeypatch.setenv("RABBITMQ_URL", custom)
    assert get_rabbitmq_url() == custom


@pytest.mark.publisher
def test_open_channel_declares_durable_entities():
    """Test _open_channel idempotently declares durable exchange and queue with binding."""
    with patch("pika.BlockingConnection") as mock_conn_cls, \
         patch("pika.URLParameters") as mock_params_cls:
        mock_conn = MagicMock()
        mock_channel = MagicMock()
        mock_conn.channel.return_value = mock_channel
        mock_conn_cls.return_value = mock_conn

        conn, channel = _open_channel("amqp://guest:guest@localhost:5672/%2f")

        assert conn == mock_conn
        assert channel == mock_channel
        mock_params_cls.assert_called_once_with("amqp://guest:guest@localhost:5672/%2f")
        mock_channel.exchange_declare.assert_called_once_with(
            exchange=EXCHANGE_NAME, exchange_type="direct", durable=True
        )
        mock_channel.queue_declare.assert_called_once_with(
            queue=QUEUE_NAME, durable=True
        )
        mock_channel.queue_bind.assert_called_once_with(
            exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY
        )


@pytest.mark.publisher
def test_publish_task_success():
    """Test publish_task packages compact JSON with persistent delivery_mode=2."""
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_conn.channel.return_value = mock_channel

    with patch("src.web.publisher._open_channel", return_value=(mock_conn, mock_channel)):
        publish_task(
            kind="scrape_new_data",
            payload={"source": "unit_test", "since": "2026-01-01"},
            headers={"X-Test": "True"},
        )

        assert mock_channel.basic_publish.call_count == 1
        call_kwargs = mock_channel.basic_publish.call_args.kwargs

        assert call_kwargs["exchange"] == EXCHANGE_NAME
        assert call_kwargs["routing_key"] == ROUTING_KEY
        assert call_kwargs["mandatory"] is False

        # Verify persistent delivery mode
        props = call_kwargs["properties"]
        assert props.delivery_mode == 2
        assert props.headers == {"X-Test": "True"}

        # Verify compact JSON content
        body = json.loads(call_kwargs["body"].decode("utf-8"))
        assert body["kind"] == "scrape_new_data"
        assert body["payload"] == {"source": "unit_test", "since": "2026-01-01"}
        assert "ts" in body

        # Verify connection close in finally block
        mock_conn.close.assert_called_once()


@pytest.mark.publisher
def test_publish_task_propagates_exception():
    """Test publish_task does not swallow exceptions so Flask can return 503."""
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_channel.basic_publish.side_effect = RuntimeError("AMQP connection refused")

    with patch("src.web.publisher._open_channel", return_value=(mock_conn, mock_channel)):
        with pytest.raises(RuntimeError, match="AMQP connection refused"):
            publish_task(kind="recompute_analytics")

        # Connection must still be closed in finally block
        mock_conn.close.assert_called_once()
