"""
RabbitMQ Publisher Module for Async Task Offloading.
Module 6 - Deploy Anywhere Assignment
Johns Hopkins University - Software Concepts (EN.605.601)

Features:
- Connects via RABBITMQ_URL environment variable with safe local fallback.
- Declares durable direct exchange 'tasks' and durable queue 'tasks_q' bound to 'tasks'.
- Publishes persistent messages (delivery_mode=2) with compact JSON payloads.
- Closes connection in a finally block.
- Propagates exceptions without swallowing, allowing HTTP 503 error responses.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Optional, Tuple

import pika

EXCHANGE_NAME = "tasks"
QUEUE_NAME = "tasks_q"
ROUTING_KEY = "tasks"


def get_rabbitmq_url() -> str:
    """Retrieve RabbitMQ connection URL from environment with fallback."""
    return os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2f")


def _open_channel(
    rabbitmq_url: Optional[str] = None,
) -> Tuple[pika.BlockingConnection, Any]:
    """
    Open connection and channel to RabbitMQ broker and idempotently declare durable entities.
    """
    url = rabbitmq_url or get_rabbitmq_url()
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Durable exchange & queue; bind idempotently
    ch.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)

    return conn, ch


def publish_task(
    kind: str,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    rabbitmq_url: Optional[str] = None,
) -> None:
    """
    Publish an asynchronous task to RabbitMQ with persistent delivery.

    Builds a compact JSON message:
    {"kind": kind, "ts": ISO_UTC, "payload": payload or {}}
    Publishes with delivery_mode=2 (persistent).
    Closes the connection in a finally block.
    Raises on error so callers can return HTTP 503.
    """
    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    conn, ch = _open_channel(rabbitmq_url)
    try:
        ch.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2, headers=headers or {}),
            mandatory=False,
        )
    finally:
        conn.close()
