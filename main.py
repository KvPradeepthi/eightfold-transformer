import json
import os
import sys

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
    config_path=None,
):
    print("[pipeline] Starting...")
    csv_records = parse_csv(csv_path)
    print(f"[pipeline] CSV: {len(csv_records)} candidate(s) loaded.")

    resume_record = parse_resume(resume_path)
    if resume_record and resume_record.get("full_name"):
        print(f"[pipeline] Resume: parsed for '{resume_record.get('full_name')}'.")
    else:
        print("[pipeline] Resume: parsed (no candidate data found or file missing).")

    merged = merge_all(csv_records, resume_record)
    print(f"[pipeline] Merged: {len(merged)} total profile(s).")

    validation = validate_all(merged)
    for v in validation:
        if v["valid"]:
            print(f"[validate] OK: Candidate {v['candidate_id']} is valid.")
        else:
            print(f"[validate] WARNING: Candidate {v['candidate_id']} failed validation: {v['errors']}")

    # Load configuration if provided
    config = None
    if config_path:
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                print(f"[pipeline] Loaded configuration from '{config_path}'.")
            else:
                print(f"[pipeline] WARNING: Config file not found at '{config_path}'. Running without projection (default).")
        except Exception as e:
            print(f"[pipeline] WARNING: Failed to load config from '{config_path}': {e}. Running without projection (default).")

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
    # 1. Run without config (outputs raw canonical records to output/candidates.json)
    print("=== Pipeline Run: Default (Canonical) ===")
    run(config_path=None)

    # 2. Run with config loaded from input/config.json (outputs projected records to output/candidates_custom.json)
    print("\n=== Pipeline Run: Projected (Custom Config) ===")
    run(output_path="output/candidates_custom.json", config_path="input/config.json")