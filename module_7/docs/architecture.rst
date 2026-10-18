Cloud Architecture & Infrastructure
===================================

The Module 7 architecture integrates AWS Managed Services with containerized microservices to achieve high availability, strict security isolation, and scalable analytical processing.

.. contents:: Sections
   :local:
   :depth: 2

Architecture Overview
---------------------

The cloud ecosystem is divided into two distinct tiers:

1. **Analytical Data Tier (AWS S3 & SageMaker)**:
   - Amazon S3 acts as the durable analytical data lake for raw and preprocessed admissions records.
   - Amazon SageMaker provides managed Jupyter compute (``ml.t2.medium``) to execute distributed analytical workflows and train future admissions predictive models.

2. **Web & Microservice Application Tier (AWS EC2)**:
   - An AWS EC2 virtual machine hosts the 4-tier microservice stack defined in Module 6.
   - Communication between the web frontend and backend worker is decoupled through RabbitMQ message queues.
   - PostgreSQL persistence is maintained via Docker named volumes mapped to host EBS storage.

Security Architecture
---------------------

The deployment enforces cloud defense-in-depth:

- **Root Account MFA**: Root credentials secured with virtual MFA authenticator applications.
- **Dedicated IAM Operator**: Day-to-day administrative and pipeline operations restricted to IAM user ``dailyWork-NF``.
- **Network Perimeter Isolation**:
  - Public EC2 ingress permits only SSH (port 22) and Web UI (port 8080).
  - Database (port 5432) and Broker Management (port 15672) are strictly bound to ``127.0.0.1``, unreachable over public Internet.
