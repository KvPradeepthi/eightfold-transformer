"""
validator.py
Validates a canonical candidate record against the expected schema.
Returns a list of validation errors (empty list = valid).
Design: we validate the canonical record BEFORE projection, so we
always check the full schema regardless of what config is applied.
"""

import re

REQUIRED_FIELDS = ["candidate_id", "full_name", "emails", "phones"]
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
E164_PATTERN = re.compile(r"^\+\d{7,15}$")


def validate(record):
    errors = []

    if not isinstance(record, dict):
        return ["Record is not a dictionary."]

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")
        elif record[field] is None:
            errors.append(f"Required field is null: '{field}'")

    # Email validations
    emails = record.get("emails", [])
    if not isinstance(emails, list):
        errors.append("'emails' must be a list.")
    else:
        if not emails:
            errors.append("Candidate has no emails (emails list is empty).")
        for e in emails:
            if e and not EMAIL_PATTERN.match(e):
                errors.append(f"Email not in valid format: '{e}'")

    # Phone validations
    phones = record.get("phones", [])
    if not isinstance(phones, list):
        errors.append("'phones' must be a list.")
    else:
        if not phones:
            errors.append("Candidate has no phones (phones list is empty).")
        for p in phones:
            if p and not E164_PATTERN.match(p):
                errors.append(f"Phone not in E.164 format: '{p}'")

    # Skills validations
    skills = record.get("skills", [])
    if not isinstance(skills, list):
        errors.append("'skills' must be a list.")

    return errors


def validate_all(records):
    results = []
    for i, rec in enumerate(records):
        errs = validate(rec)
        results.append({
            "candidate_id": rec.get("candidate_id", f"index_{i}"),
            "valid": len(errs) == 0,
            "errors": errs
        })
    return results


if __name__ == "__main__":
    import json
    import sys
    sys.path.insert(0, ".")
    from parser.csv_parser import parse_csv
    from parser.resume_parser import parse_resume
    from merger.merge import merge_all

    merged = merge_all(
        parse_csv("input/recruiter.csv"),
        parse_resume("input/resume.pdf")
    )
    print(json.dumps(validate_all(merged), indent=2))