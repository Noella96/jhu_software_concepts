"""
Packaging and setup configuration for Module 6 - Deploy Anywhere Assignment.
Johns Hopkins University - Software Concepts (EN.605.601)

Enables editable installations (pip install -e .) and standard packaging distribution
for the multi-service microservice stack (Web, Worker, Database, RabbitMQ).
"""
from setuptools import setup, find_packages

setup(
    name="gradcafe_microservices",
    version="1.0.0",
    description="Microservice Architecture Web & Worker Application for GradCafe Data Analytics",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    author="Noella Formin",
    author_email="Achaformin@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "Flask>=3.0.0",
        "psycopg[binary]>=3.1.0",
        "SQLAlchemy>=2.0.0",
        "pika>=1.3.2",
        "beautifulsoup4>=4.12.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=5.0.0",
            "pylint>=3.0.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: System :: Distributed Computing",
    ],
)
