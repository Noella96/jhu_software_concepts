.. Grad Café Microservices Platform documentation master file

Grad Café Decoupled Microservice Platform
=========================================

.. image:: https://img.shields.io/badge/Coverage-100%25-brightgreen.svg
   :alt: 100% Test Coverage
.. image:: https://img.shields.io/badge/Pylint-10.00%2F10-brightgreen.svg
   :alt: 10.00/10 Pylint Score
.. image:: https://img.shields.io/badge/Docker%20Compose-v2%204--Tier-blue.svg
   :alt: Docker Compose 4-Tier
.. image:: https://img.shields.io/badge/Course-JHU%20EN.605.601-informational.svg
   :alt: Johns Hopkins University EN.605.601

Welcome to the technical architecture and engineering reference for the **Grad Café Decoupled Microservice Platform**.
This system was engineered for **Johns Hopkins University: Software Concepts (EN.605.601)**, Module 6 (*"Deploy Anywhere Assignment"*).

Architectural Highlights
------------------------
The monolithic SQL application from Module 5 has been completely decoupled into a modern, distributed 4-tier microservice architecture:

* **Web Service (Flask :8080)**: Non-root container exposing interactive analytics dashboard, asynchronous task offloading, and real-time query endpoints.
* **Worker Service (RabbitMQ Consumer)**: Long-running processing engine enforcing ``basic_qos(prefetch_count=1)`` backpressure, transactional DB isolation, and idempotent handlers.
* **Message Broker (RabbitMQ :5672 / :15672)**: AMQP 0-9-1 broker configured with durable exchanges, queues, and persistent message delivery.
* **Database (PostgreSQL 16 :5432)**: Relational database with automated schema initialization, healthchecks, and transactional persistence across named Docker volumes.

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents

   overview
   architecture
   microservices
   api_reference
   testing_guide
   operational_notes

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
