# Multi-Source Candidate Data Transformer

## Project Overview
This project implements a Multi-Source Candidate Data Transformer designed to solve the problem of ingesting candidate information from multiple diverse channels simultaneously (e.g. structured Recruiter CSV files and unstructured Resume PDF files) and parsing, normalizing, and merging them into a single canonical candidate profile.

This project is submitted for the **Eightfold Software Engineering Internship assignment**.

---

## Features
- **Multi-Source Ingestion**: Ingests structured data from Recruiter CSV files and unstructured text from Resume PDF files.
- **Normalizations**: Normalizes phone numbers to the E.164 format and maps/canonicalizes skills using a curated lookup dictionary.
- **Link & Profile Extraction**: Extracts name, email, phone numbers, and LinkedIn/GitHub URLs using robust text pattern matchers.
- **Candidate Merging**: Matches candidates using case-insensitive email overlaps, deduplicates phone numbers and skill entries, and handles missing resume files gracefully.
- **Provenance Tracking**: Maintains metadata logging the source and method used for each canonical field value.
- **Confidence Scoring**: Assigns weights to sources (CSV = 0.9, Resume = 0.6) and adjusts field-level confidence based on agreement (boosted to 0.95) or conflicts (dropped to 0.5).
- **Runtime Projection Layer**: Reshapes the output based on custom JSON configurations, supporting field selection, remapping, on-missing policies, and metadata toggles.
- **Error Handling**: Wrapped in robust try/except blocks to ensure the pipeline degrades gracefully and never crashes.
- **Unit Test Suite**: Includes tests validating key edge cases.

---

## Project Architecture
The pipeline operates as a linear flow:
1. **Parse**: Extract text content and fields from the CSV and Resume sources.
2. **Normalize**: Clean and standardize fields (E.164 phone formats, skill canonicalization).
3. **Merge**: Match candidates by email, select values based on confidence, deduplicate elements, and track provenance.
4. **Validate**: Perform structural schema checks before projection, alerting on empty values or incorrect formats.
5. **Project**: Reshape the output record based on runtime configuration loaded from `input/config.json`.
6. **Output**: Write the canonical outputs to `output/candidates.json` and the projected outputs to `output/candidates_custom.json`.

---

## Folder Structure
```
eightfold-transformer/
├── config/
│   ├── __init__.py
│   └── projector.py          # Reshapes canonical profiles using configuration rules
├── input/
│   ├── config.json           # Runtime projection configuration
│   └── recruiter.csv         # Recruiter CSV export input
├── merger/
│   ├── __init__.py
│   └── merge.py              # Candidate merging, deduping, and confidence logic
├── normalizer/
│   ├── __init__.py
│   ├── date.py               # Date parser/normalizer
│   ├── phone.py              # E.164 phone format normalizer
│   └── skill.py              # Curriculum-based skill canonicalizer
├── output/
│   ├── candidates.json       # Generated canonical candidates JSON output
│   └── candidates_custom.json# Generated custom projected JSON output
├── parser/
│   ├── __init__.py
│   ├── csv_parser.py         # Recruiter CSV parser
│   └── resume_parser.py      # PDF text and metadata extractor
├── tests/
│   └── test_transformer.py   # Suite of 5 unit test cases
├── .gitignore
├── DESIGN.md                 # System design document
├── main.py                   # App entrypoint and pipeline execution script
├── README.md                 # General instructions and project info
├── requirements.txt          # Package dependencies
└── validator.py              # Record validation and warnings checks
```

---

## Installation & Dependencies
The project requires Python 3.11+. Install dependencies using:
```bash
pip install -r requirements.txt
```
Key dependencies:
- `pdfplumber`: Text extraction from PDF documents.
- `phonenumbers`: Verification and normalization of phone numbers to E.164.
- `python-dateutil`: Robust date parsing.

---

## How to Run
To run the full pipeline:
```bash
python main.py
```
This runs two passes:
1. **Pass 1**: Merges inputs and generates the raw canonical output in `output/candidates.json`.
2. **Pass 2**: Applies the schema projection configuration loaded from `input/config.json` and generates the projected output in `output/candidates_custom.json`.

To run the unit tests:
```bash
python -m unittest tests/test_transformer.py
```

---

## How Runtime Configuration Works
The projection configuration is loaded at runtime from `input/config.json`. It maps the internal canonical candidate record structure to the desired client schema.
- `fields`: A list defining the output properties, where:
  - `path`: The target key name in the output.
  - `from`: The canonical path to select (e.g. index selection `emails[0]`, array maps like `skills[].name`).
  - `required`: If true, makes the field mandatory.
- `include_confidence`: Toggle (`true`/`false`) overall candidate confidence score in output.
- `include_provenance`: Toggle (`true`/`false`) provenance metadata in output.
- `on_missing`: Actions to take when a value is missing (`"null"` sets it to null, `"omit"` drops the field from output, `"error"` throws an error).

If the configuration file is missing or contains invalid JSON, the app displays a warning, bypasses the projection step, and outputs the full canonical records without crashing.

---

## Sample Input & Output

### 1. Sample Recruiter CSV Input (`input/recruiter.csv`)
```csv
candidate_id,name,email,phone,current_company,title
1,John Smith,john.smith@gmail.com,9876543210,Google,SDE
```

### 2. Sample Runtime Config (`input/config.json`)
```json
{
  "fields": [
    { "path": "full_name", "required": true },
    { "path": "primary_email", "from": "emails[0]", "required": true },
    { "path": "phone", "from": "phones[0]" },
    { "path": "skills", "from": "skills[].name" }
  ],
  "include_confidence": true,
  "include_provenance": false,
  "on_missing": "null"
}
```

### 3. Sample Projected JSON Output (`output/candidates_custom.json`)
```json
[
  {
    "full_name": "John Smith",
    "primary_email": "john.smith@gmail.com",
    "phone": "+919876543210",
    "skills": [],
    "overall_confidence": 0.9
  }
]
```

---

## Design Decisions

### Provenance Tracking
Every value mapped to the canonical profile records its origins under the `provenance` field. Provenance fields store the `field` name, `source` (e.g. `csv`, `resume`, `csv+resume`), and the resolution `method` (`only_source`, `agreed`, `conflict:csv_preferred`, `merged`).

### Confidence Scoring
Confidence values are simple, explainable scores:
- Structured CSV records are assumed correct and assigned a confidence of `0.9`.
- Heuristically parsed resumes are assigned a lower default confidence of `0.6`.
- Overlapping fields where both sources agree are boosted to `0.95`.
- Overlapping fields that conflict take the CSV value, and drop to `0.5`.
- The overall profile confidence is the average score of the populated fields.

---

## Assumptions & Limitations
- **Experience/Education Structuring**: Deep structural parsing of experience and education (separating institution, degree, field, company, start/end dates) was **intentionally descoped** due to the internship assignment's time budget. Experience and education are kept as raw lists of summaries with source metadata.
- **Default Region**: Phone numbers without country codes default to the India (`IN`) region.
- **Scanned Resumes**: Resumes consisting solely of image scans do not contain extractable text and will be skipped gracefully with a logged warning.

---

## Future Improvements
- **OCR Integration**: Integrate Tesseract OCR for scanned PDF resume text extraction.
- **AI/ML Skills Classifier**: Use LLMs or semantic NLP embeddings to classify and map custom skills to a canonical list instead of relying entirely on keyword maps.
- **Structured Experience Parser**: Implement deep NLP sequence tagging (e.g., using SpaCy) to fully break down experience and education fields.
