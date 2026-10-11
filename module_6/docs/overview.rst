System Overview & Requirements
==============================

Assignment Context
------------------
The Module 6 *"Deploy Anywhere Assignment"* requires transforming a monolithic analytical application into a distributed, enterprise-grade microservice architecture orchestrated via Docker Compose.

Core Objectives
---------------
1. **Containerization**:
   Build lightweight Docker images for each distinct tier using non-root execution (`USER 1000`) for rigorous container security.
2. **Decoupled Architecture**:
   Decouple user-facing web requests from long-running extract-transform-load (ETL) and analytics computation using an asynchronous message broker (RabbitMQ).
3. **Queue-Backed Backpressure**:
   Implement worker consumer loop with ``basic_qos(prefetch_count=1)`` to ensure deterministic, single-task worker load balancing.
4. **Data Integrity & Idempotency**:
   Enforce per-message PostgreSQL transactions, committing only on task success and rolling back with message rejection on errors.
5. **Software Assurance**:
   Achieve strict software engineering standards with a **10.00/10 Pylint score** and **100.00% Pytest unit test coverage**.
