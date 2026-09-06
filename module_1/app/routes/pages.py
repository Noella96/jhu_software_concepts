"""
Blueprint controller for sub-pages module.
Handles routing for About, Teaching, Publications, and Contact views.
"""
from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
@pages_bp.route("/about")
def about():
    """Render the Home/About page."""
    return render_template("about.html", active_page="about")


@pages_bp.route("/teaching")
def teaching():
    """Render the Teaching page."""
    return render_template("teaching.html", active_page="teaching")


@pages_bp.route("/publications")
def publications():
    """Render the Publications and Projects page."""
    return render_template("publications.html", active_page="publications")


@pages_bp.route("/contact")
def contact():
    """Render the Contact information page."""
    return render_template("contact.html", active_page="contact")
