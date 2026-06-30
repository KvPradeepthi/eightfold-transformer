SKILL_MAP = {
    "Python":           ["python", "py", "python3", "python 3"],
    "JavaScript":       ["javascript", "js", "javascript (es6+)", "es6"],
    "Java":             ["java"],
    "C++":              ["c++", "cpp"],
    "C":                ["c"],
    "React":            ["react", "react.js", "reactjs"],
    "Node.js":          ["node.js", "nodejs", "node"],
    "Express.js":       ["express.js", "express", "expressjs"],
    "HTML":             ["html", "html5"],
    "CSS":              ["css", "css3"],
    "SQL":              ["sql"],
    "MySQL":            ["mysql"],
    "MongoDB":          ["mongodb", "mongo"],
    "Git":              ["git"],
    "GitHub":           ["github"],
    "Docker":           ["docker"],
    "AWS":              ["aws", "amazon web services"],
    "REST APIs":        ["rest apis", "rest api", "restful api", "rest"],
    "Machine Learning": ["machine learning", "ml"],
    "Scikit-learn":     ["scikit-learn", "sklearn"],
    "Pandas":           ["pandas"],
    "NumPy":            ["numpy"],
    "Matplotlib":       ["matplotlib"],
    "OOP":              ["oop", "object-oriented programming",
                         "object-oriented design"],
    "DSA":              ["data structures & algorithms", "dsa",
                         "data structures and algorithms"],
    "DBMS":             ["dbms", "database management"],
    "Postman":          ["postman"],
    "Power BI":         ["power bi"],
    "JWT":              ["jwt", "jwt authentication"],
    "OCI":              ["oci", "oracle cloud infrastructure"],
    "Agile":            ["agile", "agile development"],
}

# Build reverse lookup: raw_lowercase -> canonical
_REVERSE = {
    raw.lower(): canonical
    for canonical, raws in SKILL_MAP.items()
    for raw in raws
}


def canonicalize_skill(raw_skill):
    """
    Returns canonical skill name, or title-cased version of input if unknown.
    Never returns None -- always returns something (or drops truly empty input).
    """
    if not raw_skill or not raw_skill.strip():
        return None
    cleaned = raw_skill.strip()
    return _REVERSE.get(cleaned.lower(), cleaned.title())


def canonicalize_skills(raw_skills_list):
    """
    Takes a list of raw skill strings, returns deduplicated canonical list.
    Filters out None and very short strings (single chars, empty).
    """
    seen = set()
    result = []
    for raw in raw_skills_list:
        canonical = canonicalize_skill(raw)
        if canonical and len(canonical) > 1 and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


if __name__ == "__main__":
    test_skills = ["python", "js", "React.js", "nodejs", "JWT Authentication",
                   "DBMS", "Unknown Framework", "c++", ""]
    print(canonicalize_skills(test_skills))