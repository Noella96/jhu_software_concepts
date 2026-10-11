Microservices & Asynchronous Messaging
======================================

Message Flow & Task Lifecycle
-----------------------------
When a client requests an intensive data scrape or analytical recomputation:

1. **Task Offload**:
   The client posts to ``/api/tasks/scrape`` or ``/api/tasks/recompute``.
2. **Immediate Acknowledgment**:
   The web service publishes a JSON-encoded task payload to the RabbitMQ ``tasks`` exchange with routing key ``task.scrape`` or ``task.recompute``.
   The HTTP request returns immediately with status ``202 Accepted`` and a payload containing ``{"task_id": "...", "status": "queued"}``.
3. **Queue Ingestion**:
   RabbitMQ persists the message to the durable ``tasks_q`` queue.
4. **Worker Consumption**:
   The worker receives the message under ``basic_qos(prefetch_count=1)``.
5. **Transactional Execution**:
   The worker initiates an isolated database transaction, runs the handler, advances ingestion watermarks, and commits the transaction upon completion.
6. **Message Acknowledgment**:
   The worker calls ``basic_ack`` after the database transaction commits. If an error occurs, the worker rolls back the transaction and issues ``basic_nack(requeue=False)``.

Idempotent Ingestion Watermarks
-------------------------------
To prevent duplicate processing, the system maintains high-water marks in the PostgreSQL ``ingestion_watermarks`` table:

.. code-block:: sql

    CREATE TABLE IF NOT EXISTS ingestion_watermarks (
        source VARCHAR(100) PRIMARY KEY,
        last_seen BIGINT NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
