Project Overview
================

Course & Author Information
---------------------------
* **Course**: EN.605.601 - Principles of Enterprise Web Development / Software Concepts
* **Institution**: Johns Hopkins University (Whiting School of Engineering)
* **Author**: Noella Formin
* **GitHub Repository**: `Noella96/jhu_software_concepts <https://github.com/Noella96/jhu_software_concepts>`_
* **Module**: Module 4 - Pytest & Sphinx

Educational Objectives
----------------------
Module 4 focuses on industry-standard quality assurance, test-driven development, continuous integration, and technical documentation:

1. **Source Reorganization**:
   Consolidating all analytical, scraper, database, and web application logic under a clean package root (``module_4/src/``) with isolated test suites under ``module_4/tests/``.

2. **Marked Pytest Test Suite**:
   Building marked unit and integration tests (``@pytest.mark.web``, ``@pytest.mark.buttons``, ``@pytest.mark.analysis``, ``@pytest.mark.db``, ``@pytest.mark.integration``) covering the entire application lifecycle.

3. **100% Code Coverage**:
   Achieving 100% statement and branch coverage via ``pytest-cov``, strictly verified by ``--cov-fail-under=100`` in CI/CD.

4. **Continuous Integration**:
   Automating test execution and coverage verification on push/pull-request using GitHub Actions with a PostgreSQL 16 containerized service.

5. **Sphinx Documentation**:
   Generating complete technical documentation using Sphinx with ``sphinx_rtd_theme`` and automatic docstring extraction via ``sphinx.ext.autodoc``.

Key Features
------------
* **Flask Web Dashboard**: Responsive user interface displaying all 11 core analytical questions with distinct "Answer:" labels and formatted metric values.
* **Interactive Controls**: Asynchronous action buttons (``#pull-data-btn`` and ``#update-analysis-btn``) with client-side polling, live spinner feedback, and 409 Conflict concurrency gating.
* **Dual Database Access**: High-performance raw SQL queries via ``psycopg`` alongside object-relational mapping via ``SQLAlchemy``.
* **Polite Web Scraping**: Thread-pooled web scraper respecting robots.txt compliance and backoff intervals.
