"""
csv_parser.py
Parses the recruiter CSV export into a list of raw candidate dictionaries.

Design choice: we use the built-in `csv` module (not pandas) here on purpose.
Pandas is great for analysis, but for row-by-row dict parsing of a small file,
the stdlib csv.DictReader is simpler, has zero extra dependency overhead, and
maps 1:1 to "one row = one dict" which is exactly what we want. (pandas is
still used elsewhere in the project, e.g. if we extract tables from resumes.)

This module does NOT normalize anything (no phone/date formatting). It just
faithfully extracts what's in the CSV, preserving raw values. Normalization
is a separate concern (separation of concerns = each module has ONE job).
"""

import csv


def parse_csv(filepath):
    """
    Reads a recruiter CSV and returns a list of dicts, one per candidate row.

    Each dict has this raw (unnormalized) shape:
    {
        "source": "csv",
        "candidate_id": str,
        "full_name": str,
        "emails": [str] or [],      # list, even though CSV only has one column
        "phones": [str] or [],
        "current_company": str or None,
        "title": str or None,
    }

    Why emails/phones as lists even though CSV has one column each?
    Because our CANONICAL schema (the final merged output) defines emails
    and phones as arrays (a candidate can have multiple emails/phones once
    merged across sources). Making the parser emit lists from the start
    means downstream code (merge, normalize) doesn't need two different
    shapes for "list of one" vs "single value" sources.

    Robustness: if the file is missing or malformed, we don't crash the
    whole pipeline -- we print a warning and return an empty list, so other
    sources can still be processed. (Per the assignment: "a missing or
    garbage source must not crash the run.")
    """
    rows = []

    try:
        with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # .strip() defends against stray whitespace in cells.
                # .get(..., "") handles a column being entirely absent from
                # the CSV header (not just empty for one row).
                candidate_id = (row.get("candidate_id") or "").strip()
                name = (row.get("name") or "").strip()
                email = (row.get("email") or "").strip()
                phone = (row.get("phone") or "").strip()
                company = (row.get("current_company") or "").strip()
                title = (row.get("title") or "").strip()

                record = {
                    "source": "csv",
                    "candidate_id": candidate_id if candidate_id else None,
                    "full_name": name if name else None,
                    "emails": [email] if email else [],
                    "phones": [phone] if phone else [],
                    "current_company": company if company else None,
                    "title": title if title else None,
                }
                rows.append(record)

    except FileNotFoundError:
        print(f"[csv_parser] WARNING: file not found at '{filepath}'. "
              f"Skipping CSV source.")
        return []
    except Exception as e:
        print(f"[csv_parser] WARNING: failed to parse '{filepath}': {e}. "
              f"Skipping CSV source.")
        return []
    return rows
if __name__ == "__main__":
    import json
    results = parse_csv("input/recruiter.csv")
    print(json.dumps(results, indent=2))