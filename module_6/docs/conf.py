# Configuration file for the Sphinx documentation builder.
# Module 6 - Johns Hopkins University: Software Concepts (EN.605.601)
# Deploy Anywhere Assignment (Decoupled Microservice Architecture)

import os
import sys

# Add module_6 paths for autodoc
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../src/web"))
sys.path.insert(0, os.path.abspath("../src/worker"))
sys.path.insert(0, os.path.abspath("../src/db"))

# -- Project information -----------------------------------------------------
project = "Grad Café Decoupled Microservice Platform"
copyright = "2026, Noella Formin"
author = "Noella Formin"
release = "6.0.0"
version = "6.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
add_module_names = False

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = "Grad Café Microservices Platform Documentation"
html_show_sourcelink = True

html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
}
