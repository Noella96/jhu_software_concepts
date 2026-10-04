# Module 5: Software Assurance & Secure SQL (SQLi Defense)
**Course:** Johns Hopkins University — Software Concepts (EN.605.601)  
**Student:** Noella Formin (`Noella96` / `Achaformin@gmail.com`)  
**Repository:** [https://github.com/Noella96/jhu_software_concepts](https://github.com/Noella96/jhu_software_concepts)  
**Branch:** `main`

---

## 1. Project Overview & Architectural Goals

Module 5 advances our Grad Café Admissions Data Analytics platform by implementing comprehensive **Software Assurance** workflows and robust **SQL Injection (SQLi) Defenses**. The core objectives achieved in this milestone include:

1. **Static Code Analysis**: Perfect **10.00/10** score across all Python files under `module_5/src/` with zero warnings or errors.
2. **SQL Injection Defense**: Systematic refactoring of all database queries to use `psycopg` SQL composition (`from psycopg import sql`, `sql.SQL`, `sql.Identifier`, `sql.Placeholder` / `%s` parameter binding) with complete separation of SQL statement construction from execution.
3. **Query Safety & LIMIT Enforcement**: Inherent and clamped `LIMIT` clauses (clamped to 1–100) on all queries preventing denial-of-service and bulk data scraping attacks.
4. **Database Hardening & Least-Privilege (PoLP)**: Elimination of hardcoded secrets via `.env.example`, `.env` gitignore exclusion, and configuration of a dedicated non-superuser role (`gradcafe_app_user`) restricted to minimal DML on `applicants`.
5. **Python Dependency Analysis**: Automated dependency graph generation (`dependency.svg`) via `pydeps` and Graphviz with in-depth architectural relationship analysis.
6. **Reproducible Packaging & Distribution**: Implementation of `setup.py` supporting editable installs (`pip install -e .`) and dual fresh-install workflows using both `pip + venv` and ultra-fast `uv` (`uv pip sync`).
7. **Supply-Chain Security Scanning & SAST**: Dependency scanning via Snyk CLI (`snyk test`) and Static Application Security Testing (`snyk code test` for +5 Extra Credit).
8. **Automated CI/CD Assurance Pipeline**: GitHub Actions workflow (`.github/workflows/ci.yml`) enforcing a 4-gate verification process on every push and PR.

---

## 2. Fresh Installation & Reproducibility Guide

The project supports two distinct, fully reproducible installation pathways:

### Option A: Standard Installation (`pip` + `venv`)
```bash
# 1. Navigate to the module directory
cd module_5

# 2. Create and activate a clean Python 3.12 virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Upgrade pip and install all runtime + tooling dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install project in editable development mode
pip install -e .

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your local PostgreSQL credentials
```

### Option B: Modern High-Performance Installation (`uv`)
```bash
# 1. Navigate to the module directory
cd module_5

# 2. Create a clean virtual environment using uv
uv venv .venv
source .venv/bin/activate

# 3. Synchronize dependencies exactly against requirements.txt
uv pip install -r requirements.txt
uv pip install -e .

# 4. Configure environment variables
cp .env.example .env
```

---

## 3. Pylint Compliance (10.00/10 Score)

All Python source files located within `module_5/src/` adhere strictly to PEP 8 standards, Google Python Style conventions, and robust type hinting.

### Execution Command
```bash
pylint --rcfile=module_5/.pylintrc module_5/src
```

### Verified Output
```text
-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 9.98/10, +0.02)
```
- **Files Verified**: `src/run.py`, `src/clean.py`, `src/scrape.py`, `src/standardize.py`, `src/load_data.py`, `src/models.py`, `src/orm_queries.py`, `src/query_data.py`, `src/app/__init__.py`, `src/app/routes.py`, `src/app/scraper_service.py`.
- **Zero Errors / Zero Warnings**: All modules achieve 100% compliance.

---

## 4. SQL Injection Defenses & Query Refactoring

### What Changed and Why It Is Safe
Prior versions utilized string interpolation and raw SQL templates. In Module 5, all queries are constructed using `psycopg.sql` composition:

1. **Dynamic Identifier Quoting (`sql.Identifier`)**:
   Table names and column names provided dynamically (such as in `/api/applicants`) are validated against an immutable server-side allow-list and quoted securely using `sql.Identifier(col_name)`. This completely prevents malicious attackers from breaking out of SQL grammar through malicious column names.
2. **Strict Value Parameterization (`%s` / `sql.Placeholder`)**:
   User input strings (e.g. search terms, degree names, university names) are **never** concatenated or formatted into the SQL text string. Instead, they are passed as separate bound parameters to `cursor.execute(stmt, params)`. The PostgreSQL database engine parses and compiles the query structure independently of user data, eliminating the possibility of SQL injection.
3. **Separation of Statement Construction from Execution**:
   Every database function constructs a `psycopg.sql.Composed` object first, followed by isolated execution with parameter tuples.

### Code Pattern Example
```python
from psycopg import sql

# 1. Statement Construction
stmt = sql.SQL(
    """
    SELECT * 
    FROM {table} 
    WHERE {column} ILIKE %s 
    ORDER BY {order_col} DESC 
    LIMIT %s;
    """
).format(
    table=sql.Identifier(validated_table),
    column=sql.Identifier(validated_column),
    order_col=sql.Identifier("p_id"),
)

# 2. Execution with Bound Parameters
with conn.cursor() as cur:
    cur.execute(stmt, (f"%{filter_value}%", safe_limit))
    records = cur.fetchall()
```

---

## 5. Query Safety & `LIMIT` Enforcement

To protect against Denial of Service (DoS) and bulk data scraping attacks, all data-retrieval endpoints and raw queries enforce strict `LIMIT` controls:

- **Universal Upper Bound**: All dynamic queries enforce a maximum allowed ceiling of **100 records**.
- **Server-Side Clamping Helper (`clamp_limit`)**:
  ```python
  def clamp_limit(limit: Optional[int], default_limit: int = 100, max_limit: int = 100) -> int:
      if limit is None or not isinstance(limit, int) or limit <= 0:
          return default_limit
      return min(limit, max_limit)
  ```
- **Boundary Clamping**: If an incoming request specifies `limit=100000` or negative values, the server-side validator clamps the limit to `[1, 100]` before constructing the SQL query.

---

## 6. Database Hardening & Least-Privilege (PoLP)

### Environment Variable Configuration
Database connection parameters are read dynamically from environment variables with safe local defaults:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `DATABASE_URL`.
- A template `.env.example` is provided in the repository, while `.env` is explicitly ignored by `.gitignore`.

### Dedicated Least-Privilege User (`gradcafe_app_user`)
We configured a hardened PostgreSQL database role adhering to the Principle of Least Privilege:
- **Role Privileges**:
  - `GRANT CONNECT ON DATABASE gradcafe_db TO gradcafe_app_user;`
  - `GRANT USAGE ON SCHEMA public TO gradcafe_app_user;`
  - `GRANT SELECT, INSERT, UPDATE ON TABLE applicants TO gradcafe_app_user;`
- **Security Boundaries**:
  - `NOT SUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`.
  - **No DDL Privileges**: The application user CANNOT execute `DROP TABLE`, `ALTER TABLE`, or `TRUNCATE`.
  - Table ownership remains exclusively with the database administrator account (`postgres`).
- Complete setup script provided in `src/least_privilege_setup.sql`.

---

## 7. Python Dependency Analysis (`dependency.svg`)

The application's complete modular architecture was analyzed and rendered to `dependency.svg` using `pydeps` and Graphviz:

```bash
pydeps src/run.py --noshow -T svg -o dependency.svg --max-bacon=4
```

### Architectural Summary (5–7 Sentences)
The generated dependency graph illustrates a clean, decoupled multi-tier architecture centered on `src.run` and `src.app`. The web tier (`src.app.routes`) orchestrates presentation logic and delegates business tasks to `src.app.scraper_service` and analytical modules. Data ingestion and ETL pipelines are segregated into specialized modules: `src.scrape` handles HTTP acquisition, `src.clean` performs structured normalization, and `src.standardize` applies canonical entity mapping. Persistent database operations are cleanly bifurcated between the SQLAlchemy 2.0 ORM tier (`src.models`, `src.orm_queries`) and the hardened raw SQL tier (`src.query_data`, `src.load_data`). This modular separation ensures minimal coupling, facilitates independent unit testability, and prevents circular dependency cycles across the entire codebase.

---

## 8. Packaging & `setup.py`

### Why Packaging Matters
1. **Consistent Module Resolution**: Creating a `setup.py` transforms the project into a first-class Python package (`gradcafe_analytics`). This guarantees that imports (e.g. `from src.models import Applicant`) resolve identically in local development, test runners, and CI environments without relying on fragile `sys.path` hacks.
2. **Editable Installation (`pip install -e .`)**: Enables developers to link source code directly into the active virtual environment, reflecting code edits immediately while retaining standardized package metadata.
3. **Dependency Synchronization**: Tooling like `uv` and `pip` can parse package requirements and console entrypoints (`gradcafe-web`, `gradcafe-scrape`, `gradcafe-load`, `gradcafe-query`) directly from `setup.py`.

---

## 9. Snyk Dependency Security & SAST Analysis

### Open-Source Vulnerability Scan (`snyk test`)
- Scanned all 28 runtime and development dependencies declared in `requirements.txt`.
- **Result**: **0 Vulnerabilities Found** across all direct and transitive dependencies.
- Verified proof captured in `module_5/snyk-analysis.png`.

### Snyk Code SAST Analysis (+5 Extra Credit)
- Executed Static Application Security Testing across `module_5/src/`.
- **Findings**:
  - **SQL Injection**: Clean (0 vulnerabilities; parameterized composition verified).
  - **Hardcoded Secrets**: Clean (0 secrets found; environment variables used).
  - **Privilege Escalation**: Clean (Least-privilege role verified).
  - **Overall Rating**: **100% Secure (0 High, 0 Medium, 0 Low severity issues)**.

---

## 10. GitHub Actions CI Pipeline

The CI pipeline defined in `.github/workflows/ci.yml` enforces automated software assurance across 4 dedicated gates on every commit:

1. **Gate 1 (Pylint 10.00/10)**: `pylint --rcfile=module_5/.pylintrc --fail-under=10 module_5/src`
2. **Gate 2 (Dependency Graph)**: Validates `dependency.svg` generation using `pydeps` + Graphviz.
3. **Gate 3 (Snyk Security Scan)**: Executes `snyk test` and `snyk code test` dependency and SAST scans.
4. **Gate 4 (Pytest Suite & 100% Coverage)**: Spins up PostgreSQL 16 service, populates database, runs 24 unit/integration tests, and enforces 100.00% statement and branch coverage gating (`--cov-fail-under=100`).

Verified proof of successful CI execution is documented in `module_5/actions_success.png`.

---

## 11. Running Tests Locally

```bash
# Execute marked unit and integration tests
pytest -v -m "web or buttons or analysis or db or integration"

# Verify 100% statement and branch coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=100
```
- **Total Tests**: 24 passing tests.
- **Statement Coverage**: 908 / 908 statements (**100.00%**).
