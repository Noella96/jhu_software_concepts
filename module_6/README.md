# Module 6: Deploy Anywhere Assignment (Decoupled Microservice Architecture)

**Johns Hopkins University — Software Concepts (EN.605.601)**  
**Author:** Noella Formin (`Noella96` / `Achaformin@gmail.com`)  
**Status:** Completed &bull; Pylint: 10.00/10 &bull; Pytest Coverage: 100.00% &bull; All 54 Tests Passing

---

## 1. Executive Summary

Module 6 decouples the monolithic SQL + Flask analytical application into an enterprise-grade 4-tier microservice architecture managed via Docker Compose:

1. **Web Service (`web`)**: Stateless Flask presentation service running on port `8080` (non-root `USER 1000`), serving responsive analytical dashboards and offloading long-running/write tasks asynchronously to RabbitMQ via HTTP 202 Accepted.
2. **Worker Service (`worker`)**: Autonomous background processing consumer (non-root `USER 1000`) enforcing strict backpressure (`basic_qos(prefetch_count=1)`), per-message PostgreSQL transactions, polite incremental scraping, and watermark tracking.
3. **Message Broker (`rabbitmq`)**: RabbitMQ 3 Management Alpine broker exposing AMQP messaging on port `5672` and Web UI on port `15672`, configured with durable direct exchange (`tasks`), durable queue (`tasks_q`), and persistent message delivery (`delivery_mode=2`).
4. **Database Tier (`db`)**: PostgreSQL 16 Alpine database with healthcheck monitoring, automated schema initialization via `src/db/init.sql`, and persistent data storage on Docker named volume `postgres_data`.

---

## 2. Architecture & Service Topology

```text
+-------------------+       HTTP :8080       +--------------------+
|    Browser /      | ---------------------> |    Flask Web App   |
|   HTTP Client     |                        |     (Port 8080)    |
+-------------------+                        +--------------------+
          ^                                            |
          | Read Analytics Results                     | Publish Task (delivery_mode=2)
          v                                            v
+-------------------+                        +--------------------+
|   PostgreSQL 16   | <--------------------- |  RabbitMQ Broker   |
|    (Port 5432)    |    DB Transaction      |  (Port 5672/15672) |
+-------------------+                        +--------------------+
          ^                                            |
          |                                            | Consume (QoS prefetch=1)
          +--------------------------------------------+
                              Worker
                      (ETL & Analytics Engine)
```

### Service Summary & Ports

| Service | Container Name | Image Tag | Exposed Port(s) | Role & Features |
| :--- | :--- | :--- | :--- | :--- |
| **`web`** | `gradcafe_web` | `noella96/module_6-web:v1` | `8080:8080` | Flask dashboard, async task publisher, non-root `USER 1000` |
| **`worker`** | `gradcafe_worker` | `noella96/module_6-worker:v1` | *Internal* | AMQP consumer, prefetch=1 backpressure, transactional DB writes |
| **`rabbitmq`** | `gradcafe_rabbitmq` | `rabbitmq:3-management-alpine` | `5672`, `15672` | AMQP broker, Management UI, healthcheck ping |
| **`db`** | `gradcafe_db` | `postgres:16-alpine` | `5432:5432` | Relational database, named volume `postgres_data`, healthcheck |

---

## 3. Quickstart & Local Execution

### Prerequisites
- Docker Engine 24+ & Docker Compose v2+
- Python 3.11+ / 3.12 (for local unit testing and docs)

### Starting the Stack
All images are built and executed locally from source without requiring any external Docker Hub login:

```bash
cd module_6
docker compose up --build
```

### Accessing Running Services
- **Web Analytics Dashboard:** [http://localhost:8080](http://localhost:8080)
- **RabbitMQ Management UI:** [http://localhost:15672](http://localhost:15672) (Username: `guest` / Password: `guest`)
- **PostgreSQL Database:** `localhost:5432` (Database: `gradcafe_db`, User: `gradcafe_user`, Pass: `gradcafe_secure_pass_2026`)

### Operational Lifecycle Commands
```bash
# View live container logs
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f rabbitmq
docker compose logs -f db

# Stop all services (preserving volume data)
docker compose down

# Stop all services and purge volumes (clean slate)
docker compose down -v
```

---

## 4. Asynchronous Task Processing & Queue Semantics

### Task Publishing (Web Tier)
When a user clicks "Scrape New Data" or "Recompute Analytics" in the web UI, or issues a POST request:
- `POST /api/tasks/scrape` &rarr; payload `{"kind": "scrape_new_data", "payload": {"source": "web_ui"}}`
- `POST /api/tasks/recompute` &rarr; payload `{"kind": "recompute_analytics", "payload": {}}`

The endpoint publishes the task with `delivery_mode=2` (persistent message) to the durable `tasks` exchange and returns immediately with:
```json
{
  "status": "queued",
  "task_id": "9a0a03bb-cb3d-4c37-a16f-1d371d371d37",
  "task_name": "scrape_new_data",
  "message": "Task queued successfully for asynchronous execution."
}
```
HTTP status code: **202 Accepted**.

### Worker Consumption & Backpressure (Worker Tier)
- **Backpressure:** Worker calls `channel.basic_qos(prefetch_count=1)`. RabbitMQ will never push more than 1 unacknowledged message to the worker.
- **Transactional DB Isolation:** Each message is executed inside `with conn.transaction():`.
- **Guaranteed Acknowledgment:** The message is acknowledged via `basic_ack()` **only after** the database transaction commits successfully.
- **Error Handling:** If an unhandled exception occurs, the database transaction automatically rolls back and the worker executes `basic_nack(requeue=False)` to prevent infinite retry loops.

---

## 5. Database Schema & Idempotent Ingestion

Schema initialization is automatic via `src/db/init.sql`. The database includes:
1. `applicants`: Main table with 15 analytical columns and B-Tree indexes.
2. `ingestion_watermarks`: Tracks high-water marks for idempotent loading:
```sql
CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source VARCHAR(100) PRIMARY KEY,
    last_seen BIGINT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
All inserts utilize PostgreSQL safe SQL composition (`psycopg.sql`) with:
```sql
ON CONFLICT (p_id) DO UPDATE SET ...
```
guaranteeing idempotency across repeated tasks or container restarts.

---

## 6. Software Quality & Testing Verification

### Pytest Unit Testing Suite (100.00% Coverage)
All 54 unit tests pass with zero failures:
```bash
cd module_6
pytest -v --cov=src --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=100
```

| Module | Statements | Missed | Coverage |
| :--- | :---: | :---: | :---: |
| `src/db/load_data.py` | 136 | 0 | 100% |
| `src/web/app/routes.py` | 79 | 0 | 100% |
| `src/web/models.py` | 52 | 0 | 100% |
| `src/web/orm_queries.py` | 91 | 0 | 100% |
| `src/web/publisher.py` | 26 | 0 | 100% |
| `src/web/query_data.py` | 197 | 0 | 100% |
| `src/web/run.py` | 8 | 0 | 100% |
| `src/worker/consumer.py` | 145 | 0 | 100% |
| `src/worker/etl/clean.py` | 132 | 0 | 100% |
| `src/worker/etl/incremental_scraper.py` | 75 | 0 | 100% |
| `src/worker/etl/query_data.py` | 197 | 0 | 100% |
| `src/worker/etl/standardize.py` | 55 | 0 | 100% |
| **TOTAL** | **1,207** | **0** | **100.00%** |

### Pylint Static Code Analysis (10.00 / 10.00)
Every module in `src/` and `tests/` achieves a perfect Pylint rating:
```bash
cd module_6
pylint --rcfile=.pylintrc src/ tests/
# Output: Your code has been rated at 10.00/10
```

### Sphinx Technical Documentation
Build HTML documentation locally:
```bash
cd module_6
sphinx-build -b html docs docs/_build/html
```

---

## 7. Assignment Deliverables
- `module_6/docker-compose.yml`: 4-tier microservice configuration
- `module_6/src/web/Dockerfile` & `module_6/src/worker/Dockerfile`: Non-root (`USER 1000`) images
- `module_6/module_6_report.pdf`: Academic submission report with architecture diagrams and test evidence
- `module_6/coverage_summary.txt`: Verified 100.00% test coverage report
- `module_6/docs/`: Sphinx documentation suite
- `module_6.zip`: Standalone submission package for Canvas
