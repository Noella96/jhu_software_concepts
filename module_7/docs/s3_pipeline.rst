S3 to SageMaker Data Pipeline
==============================

The S3-to-SageMaker ingestion pipeline is implemented in ``s3_fetch.py`` and orchestrated via the Jupyter notebook ``grad-cafe-pipeline.ipynb``.

Pipeline Workflow
-----------------

1. **Credential & Environment Resolution**:
   - Resolves AWS credentials transparently from SageMaker instance metadata, IAM execution roles, environment variables (``AWS_ACCESS_KEY_ID``), or local AWS CLI profiles.
2. **Object Ingestion**:
   - Downloads ``applicant_data.json`` from the target S3 bucket (``grad-cafe-nf``) using resilient streaming buffers.
3. **Data Validation & Cleaning**:
   - Validates JSON structure, verifies mandatory fields (university, status, term), and strips malformed characters.
4. **Local SageMaker Persistence**:
   - Saves clean analytical data locally as ``applicant_data_SM.json`` on the SageMaker instance EBS storage for fast local notebook exploration.

CLI Usage
---------

The pipeline can be executed directly from the terminal or automated workflows:

.. code-block:: bash

   python s3_fetch.py --bucket grad-cafe-nf --key applicant_data.json --output applicant_data_SM.json
