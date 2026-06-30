

from dateutil import parser as dateparser
import re
def normalize_date(raw_date):
    if not raw_date:
        return None
    raw = raw_date.strip()
    if raw.lower() in ("present", "current", "now"):
        return None
    if re.fullmatch(r"\d{4}", raw):
        return f"{raw}-01"
    try:
        dt = dateparser.parse(raw, default=None)
        if dt:
            return dt.strftime("%Y-%m")
    except Exception:
        pass
    return None
if __name__ == "__main__":
    tests = ["Jan 2022", "January 2022", "2022-01-15", "2021",
             "Present", "May 2025", "06/2023", "garbage"]
    for t in tests:
        print(f"{t!r:20} -> {normalize_date(t)}")