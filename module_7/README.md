# Module 7: Cloud Computing Assignment (AWS S3, SageMaker & EC2 Production Deployment)

**Johns Hopkins University — Software Concepts (EN.605.601)**  
**Author:** Noella Formin (`Noella96` / `Achaformin@gmail.com`)  
**Status:** Completed &bull; Pylint: 10.00/10 &bull; Pytest Coverage: 100.00% &bull; All 16 Tests Passing &bull; CI Integrated

---

## 1. Executive Summary

Module 7 transitions the distributed admissions analysis platform developed across Modules 1–6 into commercial cloud infrastructure on Amazon Web Services (AWS):

1. **Part 1: AWS Analytical Data Pipeline (S3 & SageMaker)**
   - **Root MFA Hardening**: Multi-Factor Authentication (TOTP virtual device) activated on the root account to prevent unauthorized administrative escalation (`mfa.png`).
   - **Dedicated Least-Privilege IAM User**: IAM user `dailyWork-NF` provisioned with scoped permissions (`AmazonS3FullAccess`, `AmazonSageMakerFullAccess`, `AmazonEC2FullAccess`, `IAMReadOnlyAccess`) ensuring zero use of root credentials for pipeline execution (`dailyWork.png`).
   - **Cloud Storage Data Lake**: Private Amazon S3 bucket `grad-cafe-nf-794098635722` with public access block and default SSE-S3 encryption, populated with 11.0 MB of admissions records (`grad-cafe-bucket.png`).
   - **Managed SageMaker Compute**: SageMaker Jupyter Notebook instance `s3-to-sagemaker-grad-cafe-pipeline` on `ml.t2.medium` (`liveNotebook.png`), executing modular ingestion via `s3_fetch.py` and `grad-cafe-pipeline.ipynb` to output `applicant_data_SM.json`.

2. **Part 2: AWS EC2 Microservices Production Deployment**
   - **Cloud Compute Host**: AWS EC2 instance `i-0e65dc3a0281fbdd5` (`grad-cafe-docker-host`, t2.micro / t3.micro) running in `us-east-1` with Public IPv4 `23.22.75.252` (`ec2-instance.png`).
   - **Hardened Security Group**: Security group `grad-cafe-sg (sg-0fc3575d805ffcd24)` restricting ingress to SSH (port 22) and Web UI (port 8080). PostgreSQL (5432) and RabbitMQ Management (15672) are strictly isolated on `127.0.0.1` and internal Docker bridge networks (`ec2-security-group.png`).
   - **Multi-Service Docker Compose**: 4-tier microservice architecture (`gradcafe_web_ec2`, `gradcafe_worker_ec2`, `gradcafe_rabbitmq_ec2`, `gradcafe_db_ec2`) launched via `docker-compose.ec2.yml` (`ec2-compose-ps.png`).
   - **Live Production Dashboard**: Public analytical web dashboard loaded and operating at `http://23.22.75.252:8080/analysis` (`ec2-app.png`).

---

## 2. Verification Screenshot Index

All 8 required verification screenshots are placed in `module_7/` and embedded in the academic report:

| Screenshot File | Description | Verification Details |
| :--- | :--- | :--- |
| `mfa.png` | Root Account MFA Status | Shows virtual TOTP authenticator device active on account `794098635722` |
| `dailyWork.png` | IAM User Permissions | Displays user `dailyWork-NF` with attached managed policies |
| `grad-cafe-bucket.png` | S3 Bucket Objects | S3 bucket `grad-cafe-nf-794098635722` holding `applicant_data.json` (11.0 MB) |
| `liveNotebook.png` | SageMaker Notebook Instance | Instance `s3-to-sagemaker-grad-cafe-pipeline` in `InService` state on `ml.t2.medium` |
| `ec2-instance.png` | EC2 Instance State | Instance `i-0e65dc3a0281fbdd5` in `running` state with Public IPv4 `23.22.75.252` |
| `ec2-security-group.png` | EC2 Security Group Ingress | Inbound rules for ports 22 and 8080; DB & RabbitMQ ports closed publicly |
| `ec2-compose-ps.png` | Terminal `docker compose ps` | Terminal output showing all 4 microservice containers `Up (healthy)` |
| `ec2-app.png` | Web Dashboard in Browser | Chrome browser visiting `http://23.22.75.252:8080/analysis` with analytical metrics |

---

## 3. Part 1: S3 to SageMaker Pipeline

### Architecture & Components

```text
+----------------------------+
|        Amazon S3           |
|  grad-cafe-nf-794098635722 |
|   (applicant_data.json)    |
+----------------------------+
              |
              | boto3 Streaming Download
              v
+---------------------------------------------+
|        Amazon SageMaker Compute             |
|   s3-to-sagemaker-grad-cafe-pipeline        |
|               (ml.t2.medium)                |
|                                             |
|  +----------------+    +-----------------+  |
|  |  s3_fetch.py   | -> |  Jupyter NB     |  |
|  +----------------+    +-----------------+  |
|           |                                 |
|           v                                 |
|  applicant_data_SM.json (Local EBS Volume)  |
+---------------------------------------------+
```

### Modular Python Fetcher (`s3_fetch.py`)
Features:
- Safe, non-crashing credential resolution (instance metadata, IAM roles, env vars).
- Network retry handling with exponential backoff on transient socket failures.
- JSON schema validation verifying record structure and required fields.
- Full CLI support (`--bucket`, `--key`, `--output`, `--region`).

### CLI Execution

```bash
# Fetch from S3 to SageMaker local storage:
python s3_fetch.py --bucket grad-cafe-nf-794098635722 --key applicant_data.json --output applicant_data_SM.json
```

---

## 4. Part 2: EC2 Microservices Deployment

### Production Topology & Security Group

```text
[ Internet / Student Client ]
             |
             | Inbound TCP :8080 (Restricted to Authorized IP)
             v
+--------------------------------------------------------------+
| AWS EC2 Instance: i-0e65dc3a0281fbdd5 (23.22.75.252)          |
| Security Group: sg-0fc3575d805ffcd24 (grad-cafe-sg)         |
|                                                              |
|   +-------------------+              +-------------------+   |
|   |  Flask Web App    | -- AMQP ---> |  RabbitMQ Broker  |   |
|   |  (Port 8080)      |              |  (127.0.0.1:15672)|   |
|   +-------------------+              +-------------------+   |
|             |                                  |             |
|             | SQL Query                        | Task Queue  |
|             v                                  v             |
|   +-------------------+              +-------------------+   |
|   |   PostgreSQL 16   | <--- Write - |   Celery Worker   |   |
|   | (127.0.0.1:5432)  |              |   (ETL Consumer)  |   |
|   +-------------------+              +-------------------+   |
+--------------------------------------------------------------+
```

### Operational Runbook

For full step-by-step instructions on provisioning the EC2 host, installing Docker, cloning the repository, launching containers, and conducting smoke tests, see:
[`module_7/ec2/EC2_DEPLOYMENT.md`](ec2/EC2_DEPLOYMENT.md).

---

## 5. Software Assurance & Testing

### 1. Pylint Static Analysis (10.00/10)
```bash
cd module_7
../.venv/bin/pylint s3_fetch.py tests/*.py
```
Output:
```text
--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```

### 2. Pytest Unit Testing & 100% Coverage Gate
```bash
cd module_7
../.venv/bin/pytest --cov=s3_fetch --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=100
```
Output:
```text
Name          Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------
s3_fetch.py      82      0     14      0   100%
---------------------------------------------------------
TOTAL            82      0     14      0   100%
Required test coverage of 100% reached. Total coverage: 100.00%
16 passed in 0.55s
```

### 3. Sphinx Technical Documentation
```bash
cd module_7
sphinx-build -b html docs docs/_build/html
```

---

## 6. Continuous Integration (CI)

The GitHub Actions workflow (`.github/workflows/ci.yml`) executes the `module_7_assurance` job on every push and pull request to `main`:
1. Installs Python 3.12 dependencies and tooling (`boto3`, `pytest`, `pytest-cov`, `pylint`, `Sphinx`).
2. Enforces **10.00/10 Pylint score** on `s3_fetch.py` and `tests/`.
3. Verifies **100% branch and statement test coverage**.
4. Builds HTML documentation with Sphinx.
5. Validates `docker-compose.ec2.yml` configuration syntax.
