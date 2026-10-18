"""
Setup package definition for Module 7: Cloud Computing Assignment.
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from setuptools import find_packages, setup

setup(
    name="module_7_cloud_pipeline",
    version="7.0.0",
    description="AWS S3 to SageMaker Boto3 Data Pipeline & EC2 Microservice Deployment",
    author="Noella Formin",
    author_email="Achaformin@gmail.com",
    packages=find_packages(),
    py_modules=["s3_fetch"],
    python_requires=">=3.10",
    install_requires=[
        "boto3>=1.34.0",
        "botocore>=1.34.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=5.0.0",
            "pylint>=3.0.0",
            "reportlab>=4.0.0",
            "Sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
        ],
    },
)
