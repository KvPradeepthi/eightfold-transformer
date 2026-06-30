"""
validator.py
Validates a canonical candidate record against the expected schema.
Returns a list of validation errors (empty list = valid).
Design: we validate the canonical record BEFORE projection, so we
always check the full schema regardless of what config is applied.
"""

REQUIRED_FIELDS = ["candidate_id", "full_name", "emails", "phones"]


def validate(record):
    errors = []

    if not isinstance(record, dict):
        return ["Record is not a dictionary."]

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")
        elif record[field] is None:
            errors.append(f"Required field is null: '{field}'")

    emails = record.get("emails", [])
    if not isinstance(emails, list):
        errors.append("'emails' must be a list.")

    phones = record.get("phones", [])
    if not isinstance(phones, list):
        errors.append("'phones' must be a list.")

    # Validate E.164 phone format
    import re
    e164 = re.compile(r"^\+\d{7,15}$")
    for p in phones:
        if p and not e164.match(p):
            errors.append(f"Phone not in E.164 format: '{p}'")

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
    import json, sys
    sys.path.insert(0, ".")
    from parser.csv_parser import parse_csv
    from parser.resume_parser import parse_resume
    from merger.merge import merge_all

    merged = merge_all(parse_csv("input/recruiter.csv"),
                       parse_resume("input/resume.pdf"))
    print(json.dumps(validate_all(merged), indent=2))