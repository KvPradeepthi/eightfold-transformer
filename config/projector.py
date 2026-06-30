def project(canonical, config):
    if not config:
        return canonical
    fields_spec = config.get("fields", [])
    include_confidence = config.get("include_confidence", True)
    include_provenance = config.get("include_provenance", True)
    on_missing = config.get("on_missing", "null")
    if not fields_spec:
        result = dict(canonical)
        if not include_confidence:
            result.pop("overall_confidence", None)
        if not include_provenance:
            result.pop("provenance", None)
        return result
    result = {}
    for field_def in fields_spec:
        path = field_def.get("path")
        from_path = field_def.get("from", path)
        required = field_def.get("required", False)
        value = _get_value(canonical, from_path)
        if value is None:
            if on_missing == "omit":
                continue
            elif on_missing == "error":
                if required:
                    raise ValueError(f"Required field '{path}' is missing.")
                result[path] = None
            else:
                result[path] = None
        else:
            result[path] = value
    if include_confidence:
        result["overall_confidence"] = canonical.get("overall_confidence")
    if include_provenance:
        result["provenance"] = canonical.get("provenance")
    return result


def _get_value(record, path):
    """
    Resolves dot/bracket paths into the record.
    e.g. "emails[0]" -> record["emails"][0]
         "skills[].name" -> [s["name"] for s in record["skills"]]
    """
    if not path:
        return None

    # Handle array-map pattern: "skills[].name"
    if "[]." in path:
        parts = path.split("[].")
        key = parts[0]
        subkey = parts[1]
        arr = record.get(key, [])
        if isinstance(arr, list):
            return [item.get(subkey) for item in arr if isinstance(item, dict)]
        return None

    # Handle index pattern: "emails[0]"
    import re
    m = re.match(r"(\w+)\[(\d+)\]$", path)
    if m:
        key, idx = m.group(1), int(m.group(2))
        arr = record.get(key, [])
        return arr[idx] if isinstance(arr, list) and len(arr) > idx else None

    # Simple key
    return record.get(path)


if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, ".")
    from parser.csv_parser import parse_csv
    from parser.resume_parser import parse_resume
    from merger.merge import merge_all

    candidates = merge_all(parse_csv("input/recruiter.csv"),
                           parse_resume("input/resume.pdf"))

    # Test with a custom config
    config = {
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

    print("=== DEFAULT OUTPUT (no config) ===")
    print(json.dumps(candidates[3], indent=2)[:500], "...\n")

    print("=== CUSTOM CONFIG OUTPUT ===")
    from config.projector import project
    print(json.dumps(project(candidates[3], config), indent=2))