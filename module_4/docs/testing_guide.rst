Testing Guide & Quality Assurance
==================================

Pytest Framework & Marker Strategy
----------------------------------
The test suite utilizes **Pytest** with custom markers to categorize unit and integration tests.
Markers are registered in ``pytest.ini``:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Marker
     - Description
   * - ``web``
     - Tests Flask routes, response status codes, Jinja2 rendering, and development server.
   * - ``buttons``
     - Tests interactive action buttons (``#pull-data-btn``, ``#update-analysis-btn``), busy states, and polling.
   * - ``analysis``
     - Tests analytical query calculations, "Answer:" labels, and two-decimal formatting.
   * - ``db``
     - Tests PostgreSQL table creation, bulk insertion, deduplication, and schema constraints.
   * - ``integration``
     - End-to-end integration tests verifying data flow from scraping to database to web view.

Running the Test Suite
----------------------
To run all tests with full coverage verification:

.. code-block:: bash

   cd module_4
   pytest -v

To filter by marker:

.. code-block:: bash

   pytest -v -m "web or buttons"
   pytest -v -m "analysis"
   pytest -v -m "db"
   pytest -v -m "integration"

100% Code Coverage Strategy
---------------------------
Coverage enforcement is configured directly in ``module_4/pytest.ini``:

.. code-block:: ini

   [pytest]
   addopts = -q --cov=src --cov-report=term-missing --cov-fail-under=100

Coverage Results Summary
------------------------
.. code-block:: text

   ================================ tests coverage ================================
   Name                         Stmts   Miss  Cover   Missing
   ----------------------------------------------------------
   src/__init__.py                  0      0   100%
   src/app/__init__.py             12      0   100%
   src/app/routes.py               54      0   100%
   src/app/scraper_service.py      85      0   100%
   src/clean.py                   135      0   100%
   src/load_data.py               114      0   100%
   src/models.py                   55      0   100%
   src/orm_queries.py              87      0   100%
   src/query_data.py              157      0   100%
   src/run.py                      10      0   100%
   src/scrape.py                   82      0   100%
   src/standardize.py              58      0   100%
   ----------------------------------------------------------
   TOTAL                          849      0   100%
   Required test coverage of 100% reached. Total coverage: 100.00%
   ======================== 23 passed, 6 warnings in 4.08s ========================

Continuous Integration (GitHub Actions)
---------------------------------------
Every commit pushed to GitHub triggers the automated CI pipeline defined in ``.github/workflows/tests.yml``.
The pipeline spins up an isolated PostgreSQL 16 service, installs requirements, initializes the dataset, and validates that all 23 tests pass with 100% coverage.
