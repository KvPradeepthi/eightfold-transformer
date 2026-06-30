import phonenumbers
def normalize_phone(raw_phone, default_region="IN"):
    if not raw_phone:
        return None
    try:
        parsed = phonenumbers.parse(raw_phone, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        return None
    except Exception:
        return None
if __name__ == "__main__":
    tests = ["9876543210", "98765 43211", "+91 93902 40204", "not-a-phone", ""]
    for t in tests:
        print(f"{t!r:25} -> {normalize_phone(t)}")