# Multi-Source Candidate Data Transformer — Design Document

## Pipeline Workflow

```
            +-------------+       +---------------+
  Inputs -> | CSV Parser  | ----> | Raw CSV Dicts | --+
            +-------------+       +---------------+   |
                                                      v
            +-------------+       +---------------+  +-------+       +--------+       +-----------+       +--------+
            | PDF Parser  | ----> | Raw Res Dict  |->| Merge | ----> | Validate| ----> | Projector | ----> | Output |
            +-------------+       +---------------+  +-------+       +--------+       +-----------+       +--------+
                                                      ^ (Match key: Emails)
                                                      |
                                                   Normalizers
                                                   - Phone (E.164)
                                                   - Skill (Canonical Map)
```

## Canonical Schema

The merged canonical candidate record represents the complete candidate profile containing:
- `candidate_id`: String (UUID or CSV-provided ID)
- `full_name`: String (Name of candidate)
- `emails`: List of Strings
- `phones`: List of Strings (E.164 format)
- `location`: Dictionary with `city`, `region`, and `country`
- `links`: Dictionary with `linkedin`, `github`, `portfolio`, and `other` URLs
- `headline`: String (Headline / objective)
- `years_experience`: Number or Null
- `skills`: List of dictionaries containing `name`, `confidence`, and `sources`
- `experience`: List of dictionaries containing raw experience list items
- `education`: List of dictionaries containing raw education list items
- `provenance`: List of field provenance mappings indicating source and method
- `overall_confidence`: Number (representing overall profile reliability)

---

## Merge & Conflict Resolution Policy

### Matching Key
Candidates are matched and merged across sources using a case-insensitive email overlap (emails are the most unique matching key).

### Value Selection
- **Agreed Fields**: If both CSV and Resume provide the same field value (case-insensitive check), that value is selected with a confidence boost to `0.95`.
- **Conflicting Fields**: If values conflict, the structured source (CSV) is preferred. The confidence is dropped to `0.5` to flag the mismatch, and the conflict details are logged in the provenance metadata.
- **Single Source Fields**: If a value is only available in one source, it is kept with that source's default confidence level (CSV = `0.9`, Resume = `0.6`).

### Duplicate Handling
- **Duplicate Phones**: Normalised to standard E.164 and deduplicated.
- **Duplicate Skills**: Canonicalized using a curated lookup dictionary (e.g. `JS` to `JavaScript`, `py` to `Python`) and deduplicated.
- **Missing Resume**: If a resume is empty or missing, the pipeline gracefully ignores the resume source, prevents the creation of blank candidates, and falls back to CSV-only profiles.

---

## Confidence Calculation

Confidence scoring uses simple, explainable heuristics:
1. **CSV Source Confidence**: `0.9` (Structured recruiter input is considered highly reliable).
2. **Resume Source Confidence**: `0.6` (Unstructured heuristic parsing is prone to extraction errors).
3. **Agreed Fields**: Confidence boosted to `0.95`.
4. **Conflicting Fields**: Confidence dropped to `0.5` (representing uncertainty).
5. **Overall Confidence**: Computed as the arithmetic average of confidence scores across all populated fields.

---

## Runtime Configuration

The pipeline supports dynamic output projection via a configuration file located at `input/config.json`.
- **Field Selection & Renaming**: Fields can be selected and mapped from canonical paths (e.g., `emails[0]` mapped to `primary_email`).
- **Metadata Toggles**: Provenance and confidence information can be turned on/off.
- **Missing Values Policy**: Defines the action to take when a required field is missing: `"null"`, `"omit"`, or `"error"`.
- **Robustness**: Config loading is wrapped in try/except blocks. If missing or invalid, a warning is printed and the pipeline falls back to default settings without crashing.

---

## Assumptions & Descoped Items

- **Structured Experience & Education**: Designing a fully structured parser for education (separating institution, degree, field, end_year) and experience (separating company, title, start, end, summary) was **intentionally descoped** due to the internship assignment's time budget. Experience and education elements are kept as raw lists of descriptions mapped to the schema.
- **Default Phone Region**: Assumed to be India (`IN`) unless explicitly provided with a country code.
- **LinkedIn / GitHub Scrapers**: Scraping or making API calls was descoped to keep dependencies local and robust. Instead, simple regex patterns are utilized to extract LinkedIn and GitHub URLs from the resume text.
