System Architecture
===================

Architectural Overview
----------------------
The system is divided into modular layers following clean architecture and separation of concerns:

.. code-block:: text

   +-------------------------------------------------------------------+
   |                     Presentation Layer (Web)                      |
   |   - Flask Blueprints & Routes (module_4/src/app/routes.py)        |
   |   - Jinja2 Template (module_4/src/app/templates/analysis.html)    |
   |   - Vanilla JS Dashboard Controller (dashboard.js)                |
   |   - Modern CSS Stylesheet (style.css)                             |
   +---------------------------------+---------------------------------+
                                     |
                                     v
   +-------------------------------------------------------------------+
   |                      Service & Logic Layer                        |
   |   - ScraperManager Service (src/app/scraper_service.py)           |
   |   - Polite Concurrent Scraper (src/scrape.py)                     |
   |   - HTML Cleaning & Extraction (src/clean.py)                     |
   |   - LLM & Canonical Standardization (src/standardize.py)          |
   +---------------------------------+---------------------------------+
                                     |
                                     v
   +-------------------------------------------------------------------+
   |                    Persistence & Data Access                      |
   |   - Raw SQL Analytical Queries (src/query_data.py)                |
   |   - SQLAlchemy ORM Queries & Models (src/models.py, orm_queries)  |
   |   - Bulk Ingestion & Schema Migrations (src/load_data.py)         |
   |   - PostgreSQL Database Engine (gradcafe_db)                      |
   +-------------------------------------------------------------------+

Directory Layout
----------------
.. code-block:: text

   module_4/
   ├── src/
   │   ├── app/
   │   │   ├── __init__.py           # Flask Application Factory
   │   │   ├── routes.py             # Route Blueprints (GET /, POST /pull-data, etc.)
   │   │   ├── scraper_service.py    # Thread-safe Scraper Background Manager
   │   │   ├── static/               # CSS, JS, and UI assets
   │   │   └── templates/            # Jinja2 HTML templates
   │   ├── clean.py                  # HTML parsing and record extraction
   │   ├── load_data.py              # PostgreSQL table creation & bulk upsert
   │   ├── models.py                 # SQLAlchemy Declarative Models
   │   ├── orm_queries.py            # SQLAlchemy analytical query suite
   │   ├── query_data.py             # Raw SQL psycopg query suite
   │   ├── run.py                    # WSGI Server Runner
   │   ├── scrape.py                 # Polite paginated scraper
   │   └── standardize.py            # Degree/Origin/Program normalizer
   ├── tests/
   │   ├── conftest.py               # Shared fixtures & mock databases
   │   ├── test_analysis_format.py   # Analysis rendering & formatting tests
   │   ├── test_buttons.py           # Button actions, spinners, & polling
   │   ├── test_db_insert.py         # DB upsert & schema tests
   │   ├── test_etl_modules.py       # Module unit & branch coverage tests
   │   ├── test_flask_page.py        # Web route & status code tests
   │   └── test_integration_end_to_end.py # E2E workflow integration tests
   ├── docs/                         # Sphinx documentation
   ├── pytest.ini                    # Pytest configuration & markers
   ├── requirements.txt              # Project dependencies
   └── coverage_summary.txt          # 100% test coverage verification log

Database Schema
---------------
The primary relational table is ``applicants`` in PostgreSQL:

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS applicants (
       p_id INTEGER PRIMARY KEY,
       program TEXT,
       comments TEXT,
       date_added DATE,
       url TEXT,
       status TEXT,
       term TEXT,
       us_or_international TEXT,
       gpa NUMERIC(4,2),
       gre NUMERIC(5,2),
       gre_v NUMERIC(5,2),
       gre_aw NUMERIC(4,2),
       degree TEXT,
       llm_generated_program TEXT,
       llm_generated_university TEXT
   );
