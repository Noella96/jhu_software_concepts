"""
Packaging and setup configuration for Module 5 - Software Assurance & Secure SQL.
Johns Hopkins University - Software Concepts (EN.605.601)

Enables editable installations (pip install -e .) and standard packaging distribution.
"""
from setuptools import setup, find_packages

setup(
    name="gradcafe_analytics",
    version="1.0.0",
    description="Software Assurance & Secure SQL Web Application for GradCafe Data Analytics",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    author="Noella Formin",
    author_email="Achaformin@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=[
        "clean",
        "load_data",
        "models",
        "orm_queries",
        "query_data",
        "run",
        "scrape",
        "standardize",
    ],
    python_requires=">=3.10",
    install_requires=[
        "Flask>=3.0.0",
        "psycopg[binary]>=3.1.0",
        "SQLAlchemy>=2.0.0",
        "beautifulsoup4>=4.12.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=5.0.0",
            "pylint>=3.0.0",
            "pydeps>=1.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gradcafe-web=src.run:main",
            "gradcafe-scrape=src.scrape:main",
            "gradcafe-load=src.load_data:main",
            "gradcafe-query=src.query_data:main",
            "gradcafe-orm=src.orm_queries:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Database",
    ],
)
