import re
import pdfplumber

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[\s-]?)?(\d{3,5}[\s-]?){2,3}\d{2,4}")
LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_\-\+]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_\-\+]+", re.IGNORECASE)

SECTION_HEADERS = {
    "skills":      ["SKILLS", "TECHNICAL SKILLS", "SKILL SET",
                    "SKILLS & TECHNOLOGIES", "CORE COMPETENCIES"],
    "experience":  ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT HISTORY",
                    "INTERNSHIP EXPERIENCE", "INTERNSHIPS"],
    "education":   ["EDUCATION", "ACADEMIC BACKGROUND", "EDUCATIONAL DETAILS"],
    "projects":    ["PROJECTS", "PROJECT EXPERIENCE", "KEY PROJECTS"],
    "summary":     ["PROFESSIONAL SUMMARY", "SUMMARY", "OBJECTIVE",
                    "CAREER OBJECTIVE"],
    "ignore":      ["COMPETITIVE PROGRAMMING", "CERTIFICATIONS",
                    "ACHIEVEMENTS", "AWARDS", "LANGUAGES", "HOBBIES",
                    "REFERENCES"],
}

_HEADER_LOOKUP = {
    variant.upper(): canonical
    for canonical, variants in SECTION_HEADERS.items()
    for variant in variants
}


def _find_email(text):
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def _find_phone(text):
    match = PHONE_PATTERN.search(text)
    if not match:
        return None
    raw = match.group(0).strip()
    if sum(c.isdigit() for c in raw) < 10:
        return None
    return raw


def _find_linkedin(text):
    match = LINKEDIN_PATTERN.search(text)
    return match.group(0).strip() if match else None


def _find_github(text):
    match = GITHUB_PATTERN.search(text)
    return match.group(0).strip() if match else None


def _find_name(lines):
    for line in lines:
        if not line:
            continue
        if EMAIL_PATTERN.search(line):
            continue
        if sum(c.isdigit() for c in line) > 4:
            continue
        if line.upper() in _HEADER_LOOKUP:
            continue
        return line
    return None


def _split_into_sections(text):
    sections = {"_preamble": []}
    current_section = "_preamble"

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        canonical = _HEADER_LOOKUP.get(stripped.upper())
        if canonical:
            current_section = canonical
            sections.setdefault(current_section, [])
        else:
            if current_section == "ignore":
                continue
            sections.setdefault(current_section, [])
            sections[current_section].append(stripped)

    return sections


def _extract_skills(section_lines):
    if not section_lines:
        return []
    skills = []
    
    # Regex pattern to match known category labels ending with a colon
    CATEGORY_PATTERN = re.compile(
        r"\b(?:Backend|Frontend|Languages|Databases|Version\s+Control|Deployment|Testing|"
        r"Cloud\s+&\s+AI(?:\s+Platforms)?|Machine\s+Learning|Core\s+CS|Professional\s+Skills|"
        r"Skills\s+(?:&\s+Technologies)?|Other)\s*:",
        re.IGNORECASE
    )

    for line in section_lines:
        # Replace category labels with a comma to act as a separator
        cleaned_line = CATEGORY_PATTERN.sub(",", line)

        # Split on comma, semicolon, pipe, bullet characters, tabs
        parts = re.split(r"[,|;•·\t]", cleaned_line)
        for p in parts:
            p = p.strip()
            if p and len(p) < 40:
                skills.append(p)
    return skills


def _extract_experience(section_lines):
    DATE_HINT = re.compile(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|"
        r"\d{4}|Present|Current)",
        re.IGNORECASE
    )
    entries = []
    current_entry = []

    for line in section_lines:
        if DATE_HINT.search(line) and current_entry:
            entries.append(" ".join(current_entry))
            current_entry = [line]
        else:
            current_entry.append(line)

    if current_entry:
        entries.append(" ".join(current_entry))

    return entries if entries else section_lines


def parse_resume(filepath):
    empty_result = {
        "source": "resume",
        "candidate_id": None,
        "full_name": None,
        "emails": [],
        "phones": [],
        "linkedin": None,
        "github": None,
        "headline": None,
        "skills": [],
        "education_raw": [],
        "experience_raw": [],
    }

    try:
        with pdfplumber.open(filepath) as pdf:
            full_text = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full_text.append(t)
            text = "\n".join(full_text)

            # 1. Read hyperlink annotations for LinkedIn and GitHub URLs
            linkedin = None
            github = None
            for page in pdf.pages:
                if hasattr(page, "hyperlinks") and page.hyperlinks:
                    for link in page.hyperlinks:
                        uri = link.get("uri")
                        if uri:
                            if not linkedin:
                                l_match = LINKEDIN_PATTERN.search(uri)
                                if l_match:
                                    linkedin = l_match.group(0).strip()
                            if not github:
                                g_match = GITHUB_PATTERN.search(uri)
                                if g_match:
                                    github = g_match.group(0).strip()
    except FileNotFoundError:
        print(f"[resume_parser] WARNING: file not found at '{filepath}'. "
              f"Skipping resume source.")
        return empty_result
    except Exception as e:
        print(f"[resume_parser] WARNING: failed to read '{filepath}': {e}. "
              f"Skipping resume source.")
        return empty_result

    if not text.strip():
        print(f"[resume_parser] WARNING: no extractable text in '{filepath}' "
              f"(possibly a scanned/image-only PDF). Skipping.")
        return empty_result

    # 2. Fallback to visible text if links not found in hyperlinks annotations
    if not linkedin:
        linkedin = _find_linkedin(text)
    if not github:
        github = _find_github(text)

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    name  = _find_name(lines)
    email = _find_email(text)
    phone = _find_phone(text)

    sections = _split_into_sections(text)

    skills     = _extract_skills(sections.get("skills", []))
    experience = _extract_experience(sections.get("experience", []))
    education  = sections.get("education", [])

    summary_lines = sections.get("summary", [])
    headline = summary_lines[0] if summary_lines else None

    return {
        "source": "resume",
        "candidate_id": None,
        "full_name": name,
        "emails": [email] if email else [],
        "phones": [phone] if phone else [],
        "linkedin": linkedin,
        "github": github,
        "headline": headline,
        "skills": skills,
        "education_raw": education,
        "experience_raw": experience,
    }


if __name__ == "__main__":
    import json
    result = parse_resume("input/resume.pdf")
    print(json.dumps(result, indent=2))