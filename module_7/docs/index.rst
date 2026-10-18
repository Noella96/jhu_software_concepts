.. Grad Café Cloud Computing Platform documentation master file

Grad Café Cloud Computing Platform (Module 7)
==============================================

Welcome to the technical documentation for **Module 7: Cloud Computing Assignment** 
for **EN.605.601 Software Concepts** at **Johns Hopkins University**.

Author: **Noella Formin** (``Noella96`` / ``Achaformin@gmail.com``)

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   architecture
   s3_pipeline
   ec2_deployment
   api_reference

Overview & Objectives
---------------------

Module 7 transitions the distributed admissions analysis platform into commercial cloud infrastructure:

1. **Part 1: AWS Data Lake & Machine Learning Pipeline**:
   - Secure Identity & Access Management (scoped IAM user ``dailyWork-NF`` with MFA protection).
   - High-durability Amazon S3 object storage (``grad-cafe-nf``) holding admissions dataset.
   - Amazon SageMaker Jupyter Notebook instance (``ml.t2.medium``) ingesting S3 data via modular ``boto3`` pipeline into local analytical formats.

2. **Part 2: AWS EC2 Microservices Production Deployment**:
   - Resilient compute instance (``t3.micro`` / ``t2.micro`` running Linux).
   - Principle of Least Privilege Security Group (SSH 22 and Web 8080 restricted to authorized IP; internal database and message broker isolated on 127.0.0.1).
   - Multi-container Docker Compose deployment (Flask Web Dashboard, RabbitMQ Async Broker, Celery Worker, PostgreSQL 16).

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
