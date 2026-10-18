EC2 Microservices Deployment
============================

The EC2 deployment hosts the full containerized admissions analytics architecture originally developed in Module 6.

Microservice Stack
------------------

- **Web Service (Flask)**:
  Exposes the analytical dashboard and REST API on port 8080.
- **Worker Service (Celery)**:
  Executes background scraping, dataset ingestion, and asynchronous analytical recalculations.
- **Message Broker (RabbitMQ)**:
  Facilitates task queueing between web frontends and asynchronous workers.
- **Database (PostgreSQL 16)**:
  Maintains relational schemas, ACID transactions, and analytical indexes.

Deployment Procedure
--------------------

Refer to ``module_7/ec2/EC2_DEPLOYMENT.md`` for detailed operations:

.. code-block:: bash

   # 1. SSH into the instance
   ssh -i ~/.ssh/my-key.pem ubuntu@<EC2-PUBLIC-IP>

   # 2. Launch the services
   cd module_7/ec2
   docker compose -f docker-compose.ec2.yml up -d

   # 3. Verify health
   docker compose -f docker-compose.ec2.yml ps
