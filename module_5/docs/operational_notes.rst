Operational Notes & Deployment
==============================

Environment Configuration
-------------------------
The application accepts configuration parameters via environment variables with safe local defaults:

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Variable
     - Default
     - Description
   * - ``DATABASE_URL``
     - ``postgresql://localhost:5432/gradcafe_db``
     - Full PostgreSQL connection URI.
   * - ``POSTGRES_DB``
     - ``gradcafe_db``
     - Target database name.
   * - ``POSTGRES_USER``
     - Current OS User / ``postgres``
     - Database username.
   * - ``POSTGRES_PASSWORD``
     - Empty / None
     - Database authentication password.
   * - ``POSTGRES_HOST``
     - ``localhost``
     - Database server host.
   * - ``POSTGRES_PORT``
     - ``5432``
     - Database connection port.
   * - ``PORT``
     - ``8080``
     - HTTP port for the web dashboard server.

Running the Application Locally
-------------------------------

1. **Initialize Database**:

.. code-block:: bash

   cd module_4
   python src/load_data.py

2. **Start the Web Dashboard**:

.. code-block:: bash

   python src/run.py

3. **Access Dashboard**:
   Open browser at ``http://localhost:8080``.

CLI Tools
---------

* **Scraper**:

.. code-block:: bash

   python src/scrape.py --start 1 --end 5 --delay 0.5 --workers 4

* **Cleaner & Generator**:

.. code-block:: bash

   python src/clean.py --count 1000 --output src/applicant_data.json

* **Standardizer**:

.. code-block:: bash

   python src/standardize.py --input src/applicant_data.json --output src/llm_extend_applicant_data.json

* **Raw SQL Queries**:

.. code-block:: bash

   python src/query_data.py

* **SQLAlchemy ORM Queries**:

.. code-block:: bash

   python src/orm_queries.py

Troubleshooting & Performance
-----------------------------
* **PostgreSQL Connection Failures**:
  Verify PostgreSQL 16 is running on port 5432 and the database ``gradcafe_db`` exists.
* **Concurrent Scrape Limits**:
  Respect polite scraping rate limits. Do not exceed 4 worker threads or decrease delay below 0.5s when scraping live Grad Café pages.
