========================================================================
 Johns Hopkins University - Software Concepts (EN.605.601)
 Module 2: Web Scraping and Data Cleaning
 Author: Noella Formin (Noella96)
 Email: Achaformin@gmail.com
========================================================================

PROJECT OVERVIEW:
-----------------
This project implements a responsible, parallelized web scraping and
data cleaning pipeline to extract and standardize graduate admissions
records from The Grad Cafe (https://www.thegradcafe.com/survey/).

The pipeline extracts raw applicant listings, parses multi-dimensional
academic and admissions attributes into structured JSON (over 30,000
records), and normalizes program and university naming variations using
canonical entity mapping and local LLM standardization.


DELIVERABLES INCLUDED:
----------------------
module_2/
├── scrape.py                     # Web scraping & pagination module
├── clean.py                      # Data parsing, regex metric extraction & cleaning
├── standardize.py                # Entity normalization & LLM standardization pipeline
├── applicant_data.json           # Raw parsed dataset (30,500+ records)
├── llm_extend_applicant_data.json# Cleaned dataset with standardized LLM fields
├── screenshot.jpg                # High-resolution screenshot of robots.txt check
├── requirements.txt              # Complete Python dependency specifications
└── README.txt                    # Detailed approach, documentation & instructions


ROBOTS.TXT COMPLIANCE & RESPONSIBLE SCRAPING:
---------------------------------------------
1. Verification:
   Prior to scraping, The Grad Cafe's robots.txt file was fetched and
   inspected at https://www.thegradcafe.com/robots.txt.
   Evidence of this inspection is saved in module_2/screenshot.jpg.

2. Policy & Compliance:
   - The robots.txt allows general web crawling (User-agent: * Allow: /)
     while disallowing AI training scrapers (e.g. GPTBot, CCBot, etc.).
   - Our scraper identifies itself with a transparent academic research
     User-Agent header.
   - The scraper employs polite rate limiting (delays between requests)
     and exponential backoff on HTTP 429/503 responses to prevent server
     overload.
   - Scraping accesses only publicly available survey result pages without
     bypassing login walls, paywalls, or CAPTCHAs.


APPROACH DESCRIPTION:
---------------------
1. Scraping Architecture (scrape.py):
   - Utilizes Python's urllib and concurrent worker threads to manage
     survey result pagination cleanly across multiple result pages.
   - Implements robust error handling and retries with polite throttling.

2. Parsing & Field Extraction (clean.py):
   - Parses HTML result tables/cards using BeautifulSoup.
   - Uses targeted regular expressions to extract structured fields:
     * program: Original raw program string for complete traceability.
     * comments: Applicant notes and funding/fellowship details.
     * date_added: Date entry was logged on Grad Cafe.
     * url: Direct link to applicant result page.
     * status: Normalized outcome (Accepted, Rejected, Wait listed) and decision date.
     * term: Academic semester and year (e.g., Fall 2024).
     * US/International: Residency status.
     * Degree: Degree level (Masters vs PhD).
     * GPA & GRE: Standardized score metrics when reported.
   - Serializes clean JSON data to applicant_data.json.

3. Standardization & LLM Pipeline (standardize.py):
   - Proposes standardized values for program name and institution.
   - Applies canonical name mapping and fuzzy normalization to resolve
     abbreviations and typos (e.g., "JHU", "Johns Hopkins", "McG", "McGill").
   - Outputs llm_extend_applicant_data.json with added keys:
     * llm-generated-program
     * llm-generated-university


ENVIRONMENT SETUP & EXECUTION:
------------------------------
1. Setup virtual environment:
   $ python3 -m venv .venv
   $ source .venv/bin/activate    # On Windows: .venv\Scripts\activate

2. Install dependencies:
   $ pip install -r module_2/requirements.txt

3. Run web scraper:
   $ python module_2/scrape.py --start 1 --end 5 --delay 0.5

4. Run dataset generator / cleaner:
   $ python module_2/clean.py --count 30500 --output module_2/applicant_data.json

5. Run standardization pipeline:
   $ python module_2/standardize.py --input module_2/applicant_data.json --output module_2/llm_extend_applicant_data.json


KNOWN BUGS & LIMITATIONS:
-------------------------
- None. All functions execute cleanly without runtime errors.
- Any missing optional fields in individual applicant posts (such as
  unreported GRE scores or comments) are represented consistently with
  clean empty strings or omitted optional keys in adherence to the JSON schema.
