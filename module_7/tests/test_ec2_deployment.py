"""
Unit test suite verifying EC2 deployment configuration and runbook completeness.
Module 7 - Cloud Computing Assignment (Data Pipeline & Cloud Deployment)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import os
import pytest


@pytest.mark.ec2
def test_docker_compose_ec2_structure():
    """Verify docker-compose.ec2.yml service declarations and port security."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    compose_path = os.path.join(base_dir, "ec2", "docker-compose.ec2.yml")

    assert os.path.exists(compose_path), f"Missing {compose_path}"

    with open(compose_path, "r", encoding="utf-8") as f_in:
        content = f_in.read()

    # Verify all four required microservices are present
    assert "db:" in content
    assert "rabbitmq:" in content
    assert "web:" in content
    assert "worker:" in content

    # Verify database port is bound to localhost to prevent public exposure
    assert "127.0.0.1:5432:5432" in content

    # Verify RabbitMQ management port is bound to localhost
    assert "127.0.0.1:15672:15672" in content

    # Verify web port 8080 is exposed for HTTP ingress
    assert "8080:8080" in content

    # Verify named volume for database persistence
    assert "postgres_data_ec2:" in content


@pytest.mark.ec2
def test_ec2_deployment_runbook_content():
    """Verify EC2_DEPLOYMENT.md contains all required technical guidance."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runbook_path = os.path.join(base_dir, "ec2", "EC2_DEPLOYMENT.md")

    assert os.path.exists(runbook_path), f"Missing {runbook_path}"

    with open(runbook_path, "r", encoding="utf-8") as f_in:
        text = f_in.read()

    assert "t3.micro" in text
    assert "Ubuntu 22.04" in text
    assert "docker compose" in text
    assert "docker.io" in text
    assert "54.210.88.142" in text
    assert "Security Group" in text
    assert "15672" in text
    assert "Troubleshooting" in text
