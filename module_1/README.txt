========================================================================
 Johns Hopkins University - Software Concepts (EN.605.601)
 Module 1: Personal Developer Website
 Author: Noella Formin (Noella96)
 Email: Achaformin@gmail.com
========================================================================

PROJECT OVERVIEW:
-----------------
This project is a multi-page personal developer and academic portfolio
website constructed using Python and the Flask micro web framework.
It adheres to the modular blueprint design pattern, utilizing Jinja2
HTML template inheritance and custom CSS styling for layout, navigation,
and responsiveness.

PAGES INCLUDED:
---------------
1. About / Homepage (/) (/about):
   - Personal biography and academic background.
   - Profile picture in a two-column responsive layout.
2. Teaching (/teaching):
   - Coursework and academic focus areas.
3. Publications & Projects (/publications):
   - Module 1 project details and link to GitHub repository.
   - Research areas and publication summaries.
4. Contact (/contact):
   - Email: Achaformin@gmail.com
   - Phone: +1 (339) 228-9258
   - LinkedIn profile link.

SYSTEM REQUIREMENTS:
--------------------
- Python 3.10 or higher
- pip package manager

SETUP & INSTALLATION:
---------------------
1. Navigate to the repository root directory:
   $ cd jhu_software_concepts

2. (Optional but recommended) Create and activate a Python virtual environment:
   $ python3 -m venv .venv
   $ source .venv/bin/activate    # On Windows: .venv\Scripts\activate

3. Install required dependencies:
   $ pip install -r module_1/requirements.txt

HOW TO RUN THE APPLICATION:
---------------------------
Run the application using the standard entry point command:

   $ python module_1/run.py

The Flask server will start and bind to host 0.0.0.0 on port 8080.

ACCESSING THE WEBSITE:
----------------------
Open your web browser and navigate to:
   http://localhost:8080
   or
   http://127.0.0.1:8080

DIRECTORY STRUCTURE:
--------------------
module_1/
├── app/
│   ├── __init__.py           # Application Factory & Blueprint Registration
│   ├── routes/
│   │   ├── __init__.py
│   │   └── pages.py          # Sub-pages Blueprint (About, Teaching, Publications, Contact)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # Custom CSS Stylesheet
│   │   └── images/
│   │       └── profile.jpeg  # Profile Picture Asset
│   └── templates/
│       ├── base.html         # Base Template with Header & Active Navbar
│       ├── about.html        # About Page Template (2-Column Layout)
│       ├── teaching.html     # Teaching Page Template
│       ├── publications.html # Publications & Projects Page Template
│       └── contact.html      # Contact Page Template
├── run.py                    # Main Server Executable (Port 8080)
├── requirements.txt          # Python Dependencies
├── README.txt                # Instructions & Project Documentation
└── screenshots.pdf           # Screenshots of Running Tabs Submission Deliverable
