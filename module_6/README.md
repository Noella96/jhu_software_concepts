# Module 6: Deploy Anywhere Assignment

**Johns Hopkins University — Software Concepts (EN.605.601)**  
**Author:** Noella Formin (`Achaformin@gmail.com`)

---

## 1. Executive Overview

Module 6 refactors the SQL + Flask analytics application into a decoupled 4-tier microservice architecture orchestrating:
1. **Web Service (`web`)**: Stateless Flask presentation tier running on port `8080`, handling client HTTP traffic and offloading long-running/data-modifying tasks via asynchronous RabbitMQ publishing.
2. **Worker Service (`worker`)**: Dedicated background consumer implementing backpressure (`prefetch_count=1`), per-message PostgreSQL transactions, incremental scraping via watermark tracking, and analytics recomputation.
3. **Database Service (`db`)**: PostgreSQL 16 relational database with health check monitoring and durable storage mapped to a Docker named volume.
4. **Message Broker (`rabbitmq`)**: RabbitMQ 3 AMQP broker with Management UI (`15672`), durable exchanges (`tasks`), durable queues (`tasks_q`), and persistent message delivery (`delivery_mode=2`).

---

## 2. Architecture & Service Topology

```text
[ Client Browser ]
        |
        v HTTP :8080
[ Flask Web Service ] ----(Publish Task)----> [ RabbitMQ Broker (AMQP :5672) ]
        |                                                   |
        | SQL (Read-Only)                                   | (Consume, prefetch=1)
        v                                                   v
[ PostgreSQL 16 DB ] <----(Transaction Writes)----- [ Worker Consumer ]
```

---

## 3. Quickstart & Local Execution

### Prerequisites
- Docker Engine 24+ & Docker Compose v2+
- Python 3.11+ (for local test execution)

### Starting the Stack
```bash
# From module_6 directory
docker compose up --build
```

### Accessing Services
- **Web Analytics Dashboard:** `http://localhost:8080`
- **RabbitMQ Management Dashboard:** `http://localhost:15672` (Username: `guest`, Password: `guest`)
- **PostgreSQL Database:** `localhost:5432` (`gradcafe_db`)
