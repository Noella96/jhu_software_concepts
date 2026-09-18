# Module 3: Database Queries, SQLAlchemy, and Dynamic Webpages

**Course:** EN.605.601 - Principles of Software Concepts (Johns Hopkins University)  
**Author:** Noella Formin (`Noella96` / `Achaformin@gmail.com`)  
**Repository:** `git@github.com:Noella96/jhu_software_concepts.git`

---

## Overview

Module 3 expands upon the web-scraped and standardized Grad Café admissions dataset from Module 2 by introducing relational database persistence, handwritten SQL data analysis, modern SQLAlchemy 2.0 ORM query representations, and an interactive Flask web application. 

### Key Features
1. **PostgreSQL Ingestion (`load_data.py`)**: Idempotent data loader using `psycopg` to ingest 30,500 records into the `applicants` relational table with type coercion, NULL handling, and primary key conflict resolution.
2. **Raw SQL Query Analysis (`query_data.py`)**: Executes handwritten SQL queries for Questions 1–9 plus two original analytical questions (Q10, Q11), strictly formatted to assignment precision requirements.
3. **SQLAlchemy 2.0 ORM (`models.py`, `orm_queries.py`)**: Declarative mapping of the `Applicant` model and execution of equivalent queries using pure ORM constructs without raw SQL bypass.
4. **Dynamic Flask Web Application (`app/`, `run.py`)**: Modern, responsive analytics dashboard displaying live query statistics with real-time **"Pull Data"** background scraping and **"Update Analysis"** database refresh controls.
5. **PDF Reports (`query_results.pdf`, `limitations.pdf`)**: Comprehensive PDF deliverables documenting query methodologies and analyzing statistical limitations (voluntary response bias, self-reporting discrepancies).

---

## Environment Setup & Installation

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 14+ (Local service or configured connection URL)

### 2. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r module_3/requirements.txt
```

### 3. Database Configuration
By default, the scripts connect to a local PostgreSQL instance (`dbname=gradcafe_db`, `host=localhost`, `port=5432`). Credentials can be customized via environment variables:

```bash
export POSTGRES_DB="gradcafe_db"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="your_password"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
# Or provide a full connection string:
# export DATABASE_URL="postgresql://user:password@localhost:5432/gradcafe_db"
```

Create the database:
```bash
createdb gradcafe_db
```

---

## Execution Guide

### 1. Load Data into PostgreSQL
Populate the `applicants` table with the 30,500 standardized records from `llm_extend_applicant_data.json`:
```bash
python module_3/load_data.py
```

### 2. Execute Raw SQL Queries
Run all 11 handwritten SQL analysis queries:
```bash
python module_3/query_data.py
```

### 3. Execute SQLAlchemy ORM Queries
Run the pure SQLAlchemy ORM queries (verifying parity with SQL results):
```bash
python module_3/orm_queries.py
```

### 4. Launch the Dynamic Flask Web Application
Start the development server (defaults to port 8080):
```bash
python module_3/run.py
```
Open [http://localhost:8080](http://localhost:8080) in your web browser to view the interactive dashboard.
- **Pull Data**: Triggers asynchronous background scraping of new Grad Café entries without blocking the UI.
- **Update Analysis**: Re-queries PostgreSQL via SQLAlchemy to display the latest metrics.

### 5. Generate PDF Reports & Deliverables
```bash
python module_3/generate_pdfs.py
python module_3/capture_screenshots.py
```

---

## Part 7: Comparison of SQL and SQLAlchemy ORM

For this comparison, we evaluate **Question 8**: Identifying Fall 2026 acceptances for PhD Computer Science applicants at Georgetown, MIT, Stanford, or Carnegie Mellon University.

### Raw SQL Query
```sql
SELECT COUNT(*) 
FROM applicants 
WHERE term ILIKE '%Fall 2026%'
  AND status ILIKE '%accept%'
  AND degree ILIKE '%phd%'
  AND program ILIKE '%Computer Science%'
  AND (
      program ILIKE '%Georgetown%' 
      OR program ILIKE '%Massachusetts Institute of Technology%'
      OR program ILIKE '%MIT%'
      OR program ILIKE '%Stanford%'
      OR program ILIKE '%Carnegie Mellon%'
  );
```

### SQLAlchemy 2.0 ORM Query
```python
uni_filters = or_(
    Applicant.program.ilike("%Georgetown%"),
    Applicant.program.ilike("%Massachusetts Institute of Technology%"),
    Applicant.program.ilike("%MIT%"),
    Applicant.program.ilike("%Stanford%"),
    Applicant.program.ilike("%Carnegie Mellon%")
)

stmt = select(func.count(Applicant.p_id)).where(
    and_(
        Applicant.term.ilike("%Fall 2026%"),
        Applicant.status.ilike("%accept%"),
        Applicant.degree.ilike("%phd%"),
        Applicant.program.ilike("%Computer Science%"),
        uni_filters
    )
)
result = session.scalar(stmt)
```

### 3–5 Sentence Comparison
A primary advantage of using an Object-Relational Mapper (ORM) like SQLAlchemy is its deep Python integration and database portability; object attributes and query constructs (`and_`, `or_`, `select`) provide compile-time Python type safety, prevent SQL injection vulnerabilities automatically, and allow the underlying database engine to be swapped without altering business logic. Conversely, raw SQL offers superior transparency, explicit performance tuning, and direct access to database-specific features (such as PostgreSQL's `FILTER (WHERE ...)` clause) without needing to translate mental logic through an intermediary abstraction layer. While the ORM excels in application architectures where models are frequently manipulated as object graphs, raw SQL is often faster and more concise for complex ad-hoc analytical aggregations.

---

## Project Structure & Deliverables

```
module_3/
├── app/                           # Dynamic Flask Dashboard Package
│   ├── __init__.py                # App factory
│   ├── routes.py                  # API endpoints and dashboard routes
│   ├── scraper_service.py         # Thread-safe background scraper manager
│   ├── templates/
│   │   └── analysis.html          # Dynamic analysis template
│   └── static/
│       ├── css/style.css          # Modern, responsive design system
│       └── js/dashboard.js        # Live polling and AJAX triggers
├── applicant_data.json            # Base 30,500 applicant records
├── llm_extend_applicant_data.json # Standardized dataset with canonical fields
├── scrape.py                      # Responsible Grad Café scraper
├── clean.py                       # Data parser and cleaner
├── standardize.py                 # LLM canonicalizer
├── load_data.py                   # PostgreSQL loader using psycopg
├── models.py                      # SQLAlchemy 2.0 declarative models & sessions
├── query_data.py                  # Raw SQL query analysis (Questions 1-11)
├── orm_queries.py                 # SQLAlchemy ORM queries (Questions 1,4,5,8,9,10)
├── generate_pdfs.py               # PDF generation script
├── query_results.pdf              # PDF analysis report (11 questions + SQL + explanations)
├── limitations.pdf                # PDF reflection on data limitations & self-reporting bias
├── capture_screenshots.py         # Automated deliverable screenshot generator
├── screenshot_sql.png             # Screenshot: Raw SQL console output
├── screenshot_orm.png             # Screenshot: SQLAlchemy ORM console output
├── screenshot_flask.png           # Screenshot: Live Flask analysis dashboard
├── run.py                         # Application launcher (http://0.0.0.0:8080)
├── requirements.txt               # Module 3 dependencies
├── github.txt                     # GitHub repository SSH URL
├── README.md                      # Comprehensive documentation
└── module_3.zip                   # Canvas submission archive
```
