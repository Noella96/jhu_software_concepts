Testing Guide & Assurance Verification
=======================================

Test Suite Structure
--------------------
The unit testing suite is located in ``module_6/tests/`` and covers every service:

* ``test_publisher.py``: Tests RabbitMQ connection establishment, channel opening, exchange declaration, payload publishing with persistent delivery mode, and error handling.
* ``test_consumer.py``: Tests queue creation, message parsing, task routing, QoS throttling, transaction commit/rollback, and acknowledgment/rejection flows.
* ``test_flask_routes.py``: Tests web routes (``/``, ``/analysis``, ``/api/tasks/scrape``, ``/api/tasks/recompute``, ``/api/applicants``), status responses, and error handlers.
* ``test_db_load.py``: Tests database schema creation, table initialization, and watermark ingestion.
* ``test_etl_pipeline.py``: Tests incremental scraper, polite delay handling, HTML cleaning, degree/origin extraction, and canonical name standardization.
* ``test_coverage_booster.py``: Tests edge cases, fallback paths, and entrypoint blocks.

Running Unit Tests & Coverage
-----------------------------
To run all tests and verify 100% coverage:

.. code-block:: bash

    cd module_6
    pytest -v --cov=src --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=100

Running Pylint Verification
---------------------------
To verify 10.00/10 static code quality:

.. code-block:: bash

    cd module_6
    pylint --rcfile=.pylintrc src/ tests/
