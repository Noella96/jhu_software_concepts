Decoupled Microservice Architecture
===================================

Architecture Overview
---------------------
The system architecture decomposes responsibilities into four cooperating services:

.. code-block:: text

    +-------------------+       HTTP 202       +--------------------+
    |    Browser /      | -------------------> |    Flask Web App   |
    |   HTTP Client     |                      |     (Port 8080)    |
    +-------------------+                      +--------------------+
              ^                                          |
              | Read Results                             | Publish Task
              v                                          v
    +-------------------+                      +--------------------+
    |   PostgreSQL 16   | <------------------- |  RabbitMQ Broker   |
    |    (Port 5432)    |    DB Transaction    |  (Port 5672/15672) |
    +-------------------+                      +--------------------+
              ^                                          |
              |                                          | Consume (QoS=1)
              +------------------------------------------+
                                  Worker
                          (ETL & Analytics Engine)

Service Breakdown
-----------------

1. Web Service (``src/web/``)
   * Flask WSGI application serving analytical dashboard on port 8080.
   * Asynchronous task publishing module using ``pika`` with ``delivery_mode=2`` (persistent messages).
   * HTTP 202 Accepted response semantics returning unique task IDs.

2. Worker Service (``src/worker/``)
   * Autonomous consumer service connected via AMQP to the durable ``tasks_q`` queue.
   * Prefetch count throttled to 1 for backpressure.
   * Automated watermark advancing in ``ingestion_watermarks`` table.

3. Message Broker (``rabbitmq``)
   * Official RabbitMQ 3 Management Alpine image.
   * Exposes AMQP messaging on port 5672 and Web Management UI on port 15672.
   * Container healthchecked via ``rabbitmq-diagnostics ping -q``.

4. Database Tier (``db``)
   * PostgreSQL 16 Alpine with initialized schema via ``src/db/init.sql``.
   * Named volume ``postgres_data`` ensures state persistence across container restarts.
