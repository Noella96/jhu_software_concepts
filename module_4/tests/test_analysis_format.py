"""
Analysis Output Formatting and Precision Unit Tests.
Module 4 - Johns Hopkins University Software Concepts (EN.605.601)
"""
from __future__ import annotations

import re
import pytest
from bs4 import BeautifulSoup


@pytest.mark.analysis
def test_analysis_answer_labels_present(client):
    """
    Test that the analysis page consistently includes 'Answer:' labels for rendered questions.
    """
    response = client.get("/analysis")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Assert multiple 'Answer:' labels exist across analysis cards and metrics
    answer_matches = re.findall(r"Answer:", html)
    assert len(answer_matches) >= 5, f"Expected multiple 'Answer:' labels on page, found {len(answer_matches)}"


@pytest.mark.analysis
def test_all_percentages_formatted_to_two_decimals(client):
    """
    Test that every percentage rendered on the page is formatted with exactly two decimal places.
    """
    response = client.get("/analysis")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text()

    # Find all percentages in text, e.g., '52.25%', '46.22%', '48.89%'
    percentage_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", page_text)
    assert len(percentage_matches) > 0, "Expected percentages on analysis page"

    for pct in percentage_matches:
        # Assert decimal part exists and is exactly 2 digits
        assert "." in pct, f"Percentage '{pct}%' is missing decimals"
        decimal_part = pct.split(".")[1]
        assert len(decimal_part) == 2, f"Percentage '{pct}%' must have exactly 2 decimal places"


@pytest.mark.analysis
def test_academic_averages_two_decimal_precision(client):
    """
    Test that average GPA and GRE metrics in the data table are formatted to two decimal places.
    """
    response = client.get("/analysis")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")

    # Inspect score values
    score_cells = soup.find_all(class_=re.compile(r"score-highlight|cohort-value"))
    assert len(score_cells) > 0

    for cell in score_cells:
        txt = cell.get_text(strip=True)
        # Extract numbers like '3.70', '162.47', '5.00'
        nums = re.findall(r"\b\d+\.\d+\b", txt)
        for num in nums:
            dec = num.split(".")[1]
            assert len(dec) == 2, f"Expected 2 decimal places for numeric score '{num}'"
