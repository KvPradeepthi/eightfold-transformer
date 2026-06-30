import json, os, sys
sys.path.insert(0, ".")

from parser.csv_parser import parse_csv
from parser.resume_parser import parse_resume
from merger.merge import merge_all
from validator import validate_all
from config.projector import project


def run(
    csv_path="input/recruiter.csv",
    resume_path="input/resume.pdf",
    output_path="output/candidates.json",
    config=None,
):
    print("[pipeline] Starting...")
    csv_records = parse_csv(csv_path)
    print(f"[pipeline] CSV: {len(csv_records)} candidate(s) loaded.")

    resume_record = parse_resume(resume_path)
    print(f"[pipeline] Resume: parsed for '{resume_record.get('full_name')}'.")

    merged = merge_all(csv_records, resume_record)
    print(f"[pipeline] Merged: {len(merged)} total profile(s).")

    validation = validate_all(merged)
    for v in validation:
        status = "✓" if v["valid"] else "✗"
        print(f"[validate] {status} {v['candidate_id']} {v['errors'] if v['errors'] else ''}")

    if config:
        output = [project(rec, config) for rec in merged]
    else:
        output = merged

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[pipeline] Output written to '{output_path}'.")
    return output


if __name__ == "__main__":
    # Default run
    run()

    # Custom config run
    custom_config = {
        "fields": [
            {"path": "full_name", "required": True},
            {"path": "primary_email", "from": "emails[0]"},
            {"path": "phone", "from": "phones[0]"},
            {"path": "skills", "from": "skills[].name"},
        ],
        "include_confidence": True,
        "include_provenance": False,
        "on_missing": "null"
    }
    run(output_path="output/candidates_custom.json", config=custom_config)