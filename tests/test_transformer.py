import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from normalizer.phone import normalize_phone
from normalizer.skill import canonicalize_skills
from merger.merge import merge, merge_all
from validator import validate


class TestCandidateTransformer(unittest.TestCase):

    def test_missing_email(self):
        # A candidate record with empty emails list
        record = {
            "candidate_id": "test_id",
            "full_name": "Test Name",
            "emails": [],
            "phones": ["+919876543210"],
            "skills": []
        }
        errors = validate(record)
        self.assertTrue(any("no emails" in err.lower() or "missing" in err.lower() for err in errors))

    def test_invalid_phone_normalization(self):
        # Invalid phone should normalize to None and not crash
        self.assertIsNone(normalize_phone("invalid-phone-123"))
        self.assertIsNone(normalize_phone(""))
        # Valid phone should normalize to E.164
        self.assertEqual(normalize_phone("9876543210"), "+919876543210")

    def test_duplicate_phone_merge(self):
        csv_rec = {
            "candidate_id": "1",
            "full_name": "Test Name",
            "emails": ["test@test.com"],
            "phones": ["9876543210"],
        }
        resume_rec = {
            "full_name": "Test Name",
            "emails": ["test@test.com"],
            "phones": ["+91 98765 43210"],  # equivalent to 9876543210 after normalization
            "skills": []
        }
        merged = merge(csv_rec, resume_rec)
        # Deduplicated to a single phone number
        self.assertEqual(len(merged["phones"]), 1)
        self.assertEqual(merged["phones"][0], "+919876543210")

    def test_duplicate_skill_merge(self):
        # Overlapping/duplicate skills should be canonicalized and deduplicated
        raw_skills = ["python", "Python3", "JS", "JavaScript", "unknown-framework"]
        canonical_skills = canonicalize_skills(raw_skills)
        # "python" & "Python3" canonicalize to "Python" (deduplicated)
        # "JS" & "JavaScript" canonicalize to "JavaScript" (deduplicated)
        # "unknown-framework" title cases to "Unknown-Framework"
        self.assertIn("Python", canonical_skills)
        self.assertIn("JavaScript", canonical_skills)
        self.assertIn("Unknown-Framework", canonical_skills)
        self.assertEqual(len(canonical_skills), 3)

    def test_missing_empty_resume(self):
        csv_records = [
            {
                "candidate_id": "1",
                "full_name": "John Smith",
                "emails": ["john@gmail.com"],
                "phones": ["9876543210"],
            }
        ]
        # Empty/missing resume (represented by empty dict or None)
        results = merge_all(csv_records, {})
        # Should return exactly 1 candidate (no empty/merged candidates added)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["full_name"], "John Smith")

        # Represented by empty result with all None fields
        empty_resume = {
            "source": "resume",
            "candidate_id": None,
            "full_name": None,
            "emails": [],
            "phones": [],
            "skills": []
        }
        results_empty_res = merge_all(csv_records, empty_resume)
        self.assertEqual(len(results_empty_res), 1)
        self.assertEqual(results_empty_res[0]["full_name"], "John Smith")


if __name__ == "__main__":
    unittest.main()
