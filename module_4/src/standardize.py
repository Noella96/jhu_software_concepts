"""
Local LLM Standardization Pipeline for Graduate Applicant Data.
Module 2 - Johns Hopkins University Software Concepts (EN.605.601)

Performs entity standardization, abbreviation expansion, and canonical normalization
for University and Program names, generating llm_extend_applicant_data.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


CANONICAL_UNIVERSITIES: Dict[str, str] = {
    "mcgill": "McGill University",
    "mcg": "McGill University",
    "johns hopkins": "Johns Hopkins University",
    "jhu": "Johns Hopkins University",
    "british columbia": "University of British Columbia",
    "ubc": "University of British Columbia",
    "old dominion": "Old Dominion University",
    "odu": "Old Dominion University",
    "southern illinois university edwardsville": "Southern Illinois University Edwardsville",
    "siue": "Southern Illinois University Edwardsville",
    "carnegie mellon": "Carnegie Mellon University",
    "cmu": "Carnegie Mellon University",
    "stanford": "Stanford University",
    "mit": "Massachusetts Institute of Technology",
    "berkeley": "University of California, Berkeley",
    "uc berkeley": "University of California, Berkeley",
    "washington": "University of Washington",
    "uw": "University of Washington",
    "columbia": "Columbia University",
    "nyu": "New York University",
    "michigan": "University of Michigan",
    "umich": "University of Michigan",
    "georgia tech": "Georgia Institute of Technology",
    "gatech": "Georgia Institute of Technology",
    "ut austin": "University of Texas at Austin",
    "uiuc": "University of Illinois Urbana-Champaign",
    "illinois": "University of Illinois Urbana-Champaign",
    "cornell": "Cornell University",
    "harvard": "Harvard University",
    "princeton": "Princeton University",
    "yale": "Yale University",
    "ucla": "University of California, Los Angeles",
    "ucsd": "University of California, San Diego",
    "upenn": "University of Pennsylvania",
    "penn": "University of Pennsylvania",
    "northwestern": "Northwestern University",
    "purdue": "Purdue University",
    "wisconsin": "University of Wisconsin-Madison",
    "maryland": "University of Maryland",
    "umd": "University of Maryland",
    "duke": "Duke University",
    "chicago": "University of Chicago",
    "uchicago": "University of Chicago",
    "brown": "Brown University",
    "rice": "Rice University",
    "vanderbilt": "Vanderbilt University",
    "usc": "University of Southern California",
    "virginia": "University of Virginia",
    "uva": "University of Virginia",
    "toronto": "University of Toronto",
    "waterloo": "University of Waterloo",
    "oxford": "University of Oxford",
    "cambridge": "University of Cambridge",
}


def standardize_program_and_university(raw_program_str: str) -> Tuple[str, str]:
    """
    Parse and standardize program name and university name from raw string.
    """
    if not raw_program_str:
        return "General Program", "Unknown University"

    parts = [p.strip() for p in raw_program_str.split(",") if p.strip()]
    
    if len(parts) >= 2:
        raw_prog = parts[0]
        raw_uni = parts[1]
    elif len(parts) == 1:
        raw_prog = parts[0]
        raw_uni = "Unknown University"
    else:
        return "General Program", "Unknown University"

    # Standardize university name using canonical mapping
    clean_uni = raw_uni
    raw_uni_lower = raw_uni.lower()
    for key, canon_name in CANONICAL_UNIVERSITIES.items():
        if key in raw_uni_lower:
            clean_uni = canon_name
            break

    clean_prog = raw_prog.strip()
    return clean_prog, clean_uni


def standardize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Standardize a list of in-memory applicant record dictionaries with canonical fields.
    """
    standardized: List[Dict[str, Any]] = []
    for entry in records:
        record_copy = dict(entry)
        raw_program = record_copy.get("program", "")
        std_prog, std_uni = standardize_program_and_university(raw_program)
        record_copy["llm-generated-program"] = std_prog
        record_copy["llm_generated_program"] = std_prog
        record_copy["llm-generated-university"] = std_uni
        record_copy["llm_generated_university"] = std_uni
        standardized.append(record_copy)
    return standardized


def standardize_dataset(
    input_source: Any = "module_4/src/applicant_data.json",
    output_filepath: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load applicant data from file or list, standardize canonical names, and optionally save to output file.
    """
    if isinstance(input_source, list):
        records = input_source
    elif isinstance(input_source, str) and os.path.exists(input_source):
        with open(input_source, "r", encoding="utf-8") as f:
            records = json.load(f)
    else:
        records = []

    standardized = standardize_records(records)

    if output_filepath:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(standardized, f, indent=2, ensure_ascii=False)

    return standardized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standardize applicant data")
    parser.add_argument("--input", default="module_4/src/applicant_data.json", help="Input applicant data JSON")
    parser.add_argument("--output", default="module_4/src/llm_extend_applicant_data.json", help="Output standardized JSON")
    args = parser.parse_args()

    standardize_dataset(input_source=args.input, output_filepath=args.output)

