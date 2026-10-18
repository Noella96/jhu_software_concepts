# EC2 Cloud Deployment Runbook: Module 6 Microservice Architecture

**Course:** Johns Hopkins University — Software Concepts (EN.605.601)  
**Module:** Module 7 — Cloud Computing Assignment  
**Author:** Noella Formin (`Noella96` / `Achaformin@gmail.com`)  
**Target Environment:** AWS EC2 (`t3.micro`, Ubuntu 22.04 LTS)

---

## 1. Overview & Cloud Architecture

This runbook documents the deployment of the decoupled 4-tier microservice system onto an Amazon Elastic Compute Cloud (EC2) virtual server using Docker Compose.

```text
[ Client Browser ] 
        │
        ▼ HTTP :8080 (Restricted Inbound)
[ EC2 Host: Ubuntu 22.04 LTS ]
 ┌─────────────────────────────────────────────────────────────┐
 │ Docker Network (bridge)                                     │
 │                                                             │
 │   ┌─────────────┐       AMQP :5672        ┌─────────────┐   │
 │   │  Flask Web  │ ──────────────────────► │  RabbitMQ   │   │
 │   │ (Port 8080) │                         │   Broker    │   │
 │   └─────────────┘                         └─────────────┘   │
 │          │                                       │          │
 │          │ SQL                                   │ Consume  │
 │          ▼                                       ▼          │
 │   ┌─────────────┐   Transactional Writes  ┌─────────────┐   │
 │   │ PostgreSQL  │ ◄────────────────────── │   Worker    │   │
 │   │  (DB: 5432) │                         │  Consumer   │   │
 │   └─────────────┘                         └─────────────┘   │
 │          │                                                  │
 │          ▼                                                  │
 │   [ Named Volume: postgres_data_ec2 ]                       │
 └─────────────────────────────────────────────────────────────┘
```

---

## 2. EC2 Provisioning & Security Group Hardening

### Instance Specifications
- **AMI:** Ubuntu Server 22.04 LTS (HVM), SSD Volume Type (64-bit x86)
- **Instance Type:** `t3.micro` (1 vCPU, 1 GiB RAM — eligible for AWS Free Tier)
- **Key Pair:** `jhu-software-concepts-key.pem`
- **Storage:** 10 GiB gp3 root EBS volume

### Security Group Inbound Rules (Defense-in-Depth)
Strict least-privilege networking was enforced to protect sensitive database and broker interfaces:

| Type | Port Range | Protocol | Source | Purpose |
| :--- | :---: | :---: | :---: | :--- |
| **SSH** | `22` | TCP | `73.180.45.22/32` (My IP) | Secure remote administration via private key |
| **Custom TCP** | `8080` | TCP | `73.180.45.22/32` (My IP) | Web application analytics dashboard |
| **PostgreSQL** | `5432` | TCP | **NONE (Closed)** | Database interface blocked from public internet |
| **RabbitMQ UI**| `15672`| TCP | **NONE (Closed)** | Management console accessible only via SSH tunnel |

---

## 3. SSH Connection & Host Configuration

### Connect to the EC2 Instance
```bash
# Set appropriate permissions for the SSH private key
chmod 400 ~/.ssh/jhu-software-concepts-key.pem

# Connect to the remote Ubuntu host
ssh -i ~/.ssh/jhu-software-concepts-key.pem ubuntu@54.210.88.142
```

---

## 4. Installing Docker Engine & Docker Compose Plugin

Execute the following commands on the remote EC2 instance:

```bash
# 1. Update system package repository
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker Engine and the Docker Compose plugin
sudo apt-get install -y docker.io docker-compose-plugin

# 3. Add the ubuntu user to the docker group for non-root management
sudo usermod -aG docker $USER

# 4. Activate group membership without logging out
newgrp docker

# 5. Verify installed tooling versions
docker --version
# Expected: Docker version 24.0.7 or higher

docker compose version
# Expected: Docker Compose version v2.21.0 or higher
```

---

## 5. Deploying the Microservice Stack

### Step 1: Clone Repository & Transfer Project Files
```bash
# Clone the private repository onto the instance
git clone https://github.com/Noella96/jhu_software_concepts.git
cd jhu_software_concepts/module_7/ec2
```

### Step 2: Configure Environment Variables
Create the local `.env` configuration on the instance (never committed to git):
```bash
cat << 'EOF' > .env
POSTGRES_DB=gradcafe_db
POSTGRES_USER=gradcafe_user
POSTGRES_PASSWORD=gradcafe_secure_pass_2026
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
SECRET_KEY=gradcafe_ec2_production_secret_key_2026
PORT=8080
EOF
```

### Step 3: Launch Multi-Service Stack
```bash
# Build and launch all 4 services in detached mode
docker compose -f docker-compose.ec2.yml --env-file .env up -d
```

---

## 6. Verification & Operational Health Checks

### Check Container Status
```bash
docker compose -f docker-compose.ec2.yml ps
```
**Expected Output:**
```text
NAME                     IMAGE                      STATUS                   PORTS
gradcafe_db_ec2          postgres:16-alpine         Up (healthy)             127.0.0.1:5432->5432/tcp
gradcafe_rabbitmq_ec2    rabbitmq:3-management      Up (healthy)             5672/tcp, 127.0.0.1:15672->15672/tcp
gradcafe_web_ec2         noella96/module_6-web:v1   Up                       0.0.0.0:8080->8080/tcp
gradcafe_worker_ec2      noella96/module_6-worker:v1 Up                       
```

### Verify Service Logs
```bash
# Inspect web service logs
docker compose -f docker-compose.ec2.yml logs web

# Inspect worker consumption logs
docker compose -f docker-compose.ec2.yml logs worker
```

### Test Live Web Application
Open a web browser and navigate to:
```text
http://54.210.88.142:8080
```
1. Verify that the analytics dashboard loads with all 11 SQL and ORM queries populated.
2. Click **Scrape New Data** &rarr; Verify immediate HTTP 202 Accepted response.
3. Click **Recompute Analytics** &rarr; Verify worker picks up the task from RabbitMQ and updates database metrics.

### Secure Access to RabbitMQ Management UI via SSH Tunnel
Because port 15672 is not exposed publicly, establish an encrypted SSH local port forward:
```bash
ssh -i ~/.ssh/jhu-software-concepts-key.pem -L 15672:localhost:15672 ubuntu@54.210.88.142
```
Access the management console locally at `http://localhost:15672` (Credentials: `guest` / `guest`).

---

## 7. Operational Teardown & Cost Management

To prevent ongoing AWS charges after evaluation:

```bash
# 1. Stop all containers and preserve database volume
docker compose -f docker-compose.ec2.yml down

# 2. Exit SSH session
exit

# 3. Stop the EC2 instance via AWS Management Console or AWS CLI
aws ec2 stop-instances --instance-ids i-0a8b9c7d6e5f41234
```
> **Notice:** Do not terminate the instance; keep it stopped so it can be resumed for Module 8.

---

## 8. Troubleshooting Notes

| Issue | Root Cause | Resolution |
| :--- | :--- | :--- |
| **`permission denied` running docker** | User not in `docker` group | Run `sudo usermod -aG docker $USER` and `newgrp docker`. |
| **Web service cannot reach DB** | Postgres container still initializing | Healthchecks ensure `depends_on: { condition: service_healthy }` holds start until ready. |
| **Browser cannot connect on port 8080** | Security Group missing inbound rule | Add inbound TCP rule on port `8080` for your current public IP. |
| **RabbitMQ connection refused** | AMQP broker startup delay | Verify RabbitMQ healthcheck with `docker compose ps` before starting consumers. |
