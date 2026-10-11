Operational Notes & Deployment
================================

Running Locally with Docker Compose
-----------------------------------
All services build and run locally without requiring any external Docker registry accounts:

.. code-block:: bash

    cd module_6
    docker compose up --build

Service Port Assignments
------------------------

* **Web UI Dashboard**: ``http://localhost:8080``
* **RabbitMQ Management Console**: ``http://localhost:15672`` (Credentials: ``guest`` / ``guest``)
* **RabbitMQ AMQP Broker**: ``amqp://localhost:5672``
* **PostgreSQL Database**: ``localhost:5432`` (Database: ``gradcafe_db``, User: ``gradcafe_user``)

Monitoring Container Logs
-------------------------
Inspect real-time service logs:

.. code-block:: bash

    docker compose logs -f web
    docker compose logs -f worker
    docker compose logs -f rabbitmq
    docker compose logs -f db

Stopping Services Cleanly
-------------------------
To stop all containers while preserving data:

.. code-block:: bash

    docker compose down

To stop and remove all volumes for a clean reset:

.. code-block:: bash

    docker compose down -v
