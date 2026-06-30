import uuid
from normalizer.phone import normalize_phone
from normalizer.skill import canonicalize_skills
CSV_CONFIDENCE = 0.9
RESUME_CONFIDENCE = 0.6
def _prov(field, source, method):
    return {"field": field, "source": source, "method": method}
def _pick(field, csv_val, resume_val, provenance, scores):
    if csv_val and resume_val:
        if str(csv_val).lower() == str(resume_val).lower():
            provenance.append(_prov(field, "csv+resume", "agreed"))
            scores.append(0.95)
            return csv_val
        else:
            provenance.append(_prov(field, "csv", "conflict:csv_preferred"))
            scores.append(0.5)
            return csv_val
    elif csv_val:
        provenance.append(_prov(field, "csv", "only_source"))
        scores.append(CSV_CONFIDENCE)
        return csv_val
    elif resume_val:
        provenance.append(_prov(field, "resume", "only_source"))
        scores.append(RESUME_CONFIDENCE)
        return resume_val
    else:
        provenance.append(_prov(field, "none", "missing"))
        return None
def _merge_lists(a, b, norm_fn=None):
    seen, out = set(), []
    for item in (a or []) + (b or []):
        v = norm_fn(item) if norm_fn else item
        if v and v not in seen:
            seen.add(v); out.append(v)
    return out
def merge(csv_rec, resume_rec):
    c, r = csv_rec or {}, resume_rec or {}
    prov, scores = [], []
    full_name = _pick("full_name", c.get("full_name"), r.get("full_name"), prov, scores)
    headline  = _pick("headline",  c.get("title"),     r.get("headline"),  prov, scores)
    emails = _merge_lists(c.get("emails",[]), r.get("emails",[]))
    phones = _merge_lists(c.get("phones",[]), r.get("phones",[]), normalize_phone)
    prov.append(_prov("emails","csv+resume","merged"))
    prov.append(_prov("phones","csv+resume","merged+normalized"))
    skills = [
        {"name": s, "confidence": RESUME_CONFIDENCE, "sources": ["resume"]}
        for s in canonicalize_skills(r.get("skills", []))
    ]
    prov.append(_prov("skills","resume","extracted+canonicalized"))

    experience = [{"summary": e, "source": "resume", "confidence": RESUME_CONFIDENCE}
                  for e in r.get("experience_raw", [])]
    education  = [{"raw": e, "source": "resume", "confidence": RESUME_CONFIDENCE}
                  for e in r.get("education_raw", [])]

    overall = round(sum(scores)/len(scores), 2) if scores else 0.0

    return {
        "candidate_id":       c.get("candidate_id") or str(uuid.uuid4()),
        "full_name":          full_name,
        "emails":             emails,
        "phones":             phones,
        "location":           {"city": None, "region": None, "country": None},
        "links":              {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "headline":           headline,
        "years_experience":   None,
        "skills":             skills,
        "experience":         experience,
        "education":          education,
        "provenance":         prov,
        "overall_confidence": overall,
    }

def merge_all(csv_records, resume_record):
    results, resume_matched = [], False
    resume_emails = set(e.lower() for e in (resume_record.get("emails") or []))

    for csv_rec in csv_records:
        csv_emails = set(e.lower() for e in (csv_rec.get("emails") or []))
        if csv_emails & resume_emails:
            results.append(merge(csv_rec, resume_record))
            resume_matched = True
        else:
            results.append(merge(csv_rec, {}))

    if not resume_matched and resume_record:
        results.append(merge({}, resume_record))
    return results

if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, ".")
    from parser.csv_parser import parse_csv
    from parser.resume_parser import parse_resume
    csv_records = parse_csv("input/recruiter.csv")
    resume_rec  = parse_resume("input/resume.pdf")
    print(json.dumps(merge_all(csv_records, resume_rec), indent=2))