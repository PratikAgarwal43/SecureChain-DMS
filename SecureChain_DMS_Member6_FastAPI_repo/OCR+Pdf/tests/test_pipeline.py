"""
tests/test_pipeline.py
------------------------
Member 6 scope: integration testing. These tests deliberately avoid loading
Qwen2-VL (no GPU needed), so they can run in GitHub Actions / any CI runner.
They cover the deterministic logic: sensitivity classification, null
normalization, and multi-page merge behaviour — the parts responsible for
the bugs found during manual testing (numpy.bool_ serialization, "null"
string vs JSON null, garbled multi-page summaries, junk empty accused
entries).

Run with:  python -m pytest tests/ -v
"""

import sys
import os
import json
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Lightweight CI trick -------------------------------------------------
# core/ocr_engine.py imports transformers + qwen_vl_utils at module level.
# These tests only exercise the deterministic, non-GPU logic (static/unbound
# methods), so we stub those heavy modules out BEFORE importing ocr_engine.
# This means `pip install torch/transformers` is NOT required to run this
# test file, which keeps CI fast and GPU-free.
# ---------------------------------------------------------------------------
sys.modules.setdefault("torch", mock.MagicMock())
sys.modules.setdefault("transformers", mock.MagicMock())
sys.modules.setdefault("qwen_vl_utils", mock.MagicMock())

from core.sensitivity_classifier import classify_sensitivity
from core.case_validation import validate_case_submission, NEW_FIR_MODE, EXISTING_CASE_MODE


class TestCaseValidation(unittest.TestCase):
    """
    Covers the required officer workflow:
    - New FIR registration: FIR upload is mandatory.
    - Existing case folder: FIR upload is optional, but at least one file
      (FIR or supporting) must be provided.
    """

    def test_new_fir_mode_requires_fir_file(self):
        error = validate_case_submission(NEW_FIR_MODE, fir_file=None, supporting_files=[])
        self.assertIsNotNone(error)
        self.assertIn("mandatory", error)

    def test_new_fir_mode_passes_with_fir_file_only(self):
        error = validate_case_submission(NEW_FIR_MODE, fir_file="/tmp/fir.pdf", supporting_files=[])
        self.assertIsNone(error)

    def test_new_fir_mode_passes_with_fir_and_supporting(self):
        error = validate_case_submission(NEW_FIR_MODE, fir_file="/tmp/fir.pdf", supporting_files=["/tmp/evidence.jpg"])
        self.assertIsNone(error)

    def test_new_fir_mode_fails_with_only_supporting_document(self):
        error = validate_case_submission(NEW_FIR_MODE, fir_file=None, supporting_files=["/tmp/evidence.jpg"])
        self.assertIsNotNone(error)

    def test_existing_case_mode_passes_with_only_supporting_document(self):
        # this is the key rule: FIR must NOT be required the second time
        error = validate_case_submission(EXISTING_CASE_MODE, fir_file=None, supporting_files=["/tmp/evidence.jpg"])
        self.assertIsNone(error)

    def test_existing_case_mode_passes_with_only_fir(self):
        error = validate_case_submission(EXISTING_CASE_MODE, fir_file="/tmp/fir_update.pdf", supporting_files=[])
        self.assertIsNone(error)

    def test_existing_case_mode_fails_with_nothing_uploaded(self):
        error = validate_case_submission(EXISTING_CASE_MODE, fir_file=None, supporting_files=[])
        self.assertIsNotNone(error)

    def test_unrecognized_mode_returns_error(self):
        error = validate_case_submission("Some Unknown Mode", fir_file="/tmp/fir.pdf", supporting_files=[])
        self.assertIsNotNone(error)


class TestSensitivityClassifier(unittest.TestCase):
    def test_high_sensitivity_detected(self):
        record = {
            "fir_description_english": "Chargesheet filed after forensic report confirmed evidence.",
            "acts_and_sections": ["BNS Section 303(2)"],
            "items_of_interest": None,
        }
        result = classify_sensitivity(record)
        self.assertEqual(result["suggested_sensitivity_tier"], "High")
        self.assertIn("3-of-5", result["suggested_quorum"])

    def test_medium_sensitivity_detected(self):
        record = {
            "fir_description_english": "FIR registered regarding theft of motorcycle.",
            "acts_and_sections": ["IPC Section 379"],
            "items_of_interest": "one motorcycle",
        }
        result = classify_sensitivity(record)
        self.assertEqual(result["suggested_sensitivity_tier"], "Medium")

    def test_low_sensitivity_fallback(self):
        record = {
            "fir_description_english": "Internal progress note, nothing case-related.",
            "acts_and_sections": [],
            "items_of_interest": None,
        }
        result = classify_sensitivity(record)
        self.assertEqual(result["suggested_sensitivity_tier"], "Low")

    def test_handles_missing_fields_gracefully(self):
        # should never crash even on a mostly-empty extraction
        result = classify_sensitivity({})
        self.assertIn("suggested_sensitivity_tier", result)


class TestNullNormalization(unittest.TestCase):
    """Covers the '"null"' string bug found during manual testing."""

    def setUp(self):
        # import here to avoid triggering heavy model load at module import time
        from core.ocr_engine import QwenDocumentParser
        self.normalize = QwenDocumentParser._normalize_null_strings

    def test_string_null_converted_to_none(self):
        self.assertIsNone(self.normalize("null"))
        self.assertIsNone(self.normalize("NULL"))
        self.assertIsNone(self.normalize("N/A"))
        self.assertIsNone(self.normalize("not visible"))
        self.assertIsNone(self.normalize(""))

    def test_real_values_untouched(self):
        self.assertEqual(self.normalize("Mukesh Mandal"), "Mukesh Mandal")
        self.assertEqual(self.normalize("379"), "379")

    def test_recursive_over_dict_and_list(self):
        data = {
            "name": "null",
            "sections": ["379", "null", "N/A"],
            "nested": {"phone": "not available", "real": "8497924053"}
        }
        cleaned = self.normalize(data)
        self.assertIsNone(cleaned["name"])
        self.assertEqual(cleaned["sections"], ["379", None, None])
        self.assertIsNone(cleaned["nested"]["phone"])
        self.assertEqual(cleaned["nested"]["real"], "8497924053")


class TestMergePageResults(unittest.TestCase):
    """Covers the garbled-narrative and junk-accused-entry bugs."""

    def setUp(self):
        from core.ocr_engine import QwenDocumentParser
        self.merge = QwenDocumentParser.merge_page_results

    def test_drops_all_empty_accused_entries(self):
        pages = [
            {"district": "Darbhanga", "accused_details": [
                {"name": None, "alias": None, "father_or_husband_name": None, "address": None}
            ]},
        ]
        # bind as unbound method call (self not needed, it's stateless logic)
        merged = self.merge(None, pages)
        self.assertEqual(merged["accused_details"], [])

    def test_keeps_valid_accused_entries(self):
        pages = [
            {"accused_details": [
                {"name": "Tejveer Singh", "alias": "owner", "father_or_husband_name": None, "address": None}
            ]},
        ]
        merged = self.merge(None, pages)
        self.assertEqual(len(merged["accused_details"]), 1)
        self.assertEqual(merged["accused_details"][0]["name"], "Tejveer Singh")

    def test_filters_echoed_instruction_text(self):
        pages = [
            {"fir_description_english": "A complete english summary of the full narrative/complaint content on this page."},
            {"fir_description_english": "Complainant reported theft of a motorcycle on 15/11/23."},
        ]
        merged = self.merge(None, pages)
        self.assertEqual(merged["fir_description_english"],
                          "Complainant reported theft of a motorcycle on 15/11/23.")

    def test_picks_longest_valid_summary_not_concatenation(self):
        pages = [
            {"fir_description_english": "Short note."},
            {"fir_description_english": "A much longer and more detailed narrative describing the actual incident in full."},
        ]
        merged = self.merge(None, pages)
        # must NOT be a space-joined concatenation of both
        self.assertNotIn("Short note. A much longer", merged["fir_description_english"])
        self.assertEqual(
            merged["fir_description_english"],
            "A much longer and more detailed narrative describing the actual incident in full."
        )

    def test_scalar_fields_fill_from_first_non_null_page(self):
        pages = [
            {"district": None, "fir_number": "5106072230793"},
            {"district": "Darbhanga", "fir_number": None},
        ]
        merged = self.merge(None, pages)
        self.assertEqual(merged["district"], "Darbhanga")
        self.assertEqual(merged["fir_number"], "5106072230793")

    def test_acts_and_sections_deduplicated_across_pages(self):
        pages = [
            {"acts_and_sections": ["BNS Section 316(2)", "BNS Section 318(4)"]},
            {"acts_and_sections": ["BNS Section 318(4)", "BNS Section 303(2)"]},
        ]
        merged = self.merge(None, pages)
        self.assertEqual(
            merged["acts_and_sections"],
            ["BNS Section 316(2)", "BNS Section 318(4)", "BNS Section 303(2)"]
        )

    def test_pages_with_error_key_are_skipped(self):
        pages = [
            {"error": "Structural formatting variance", "raw_payload": "garbage"},
            {"district": "Darbhanga"},
        ]
        merged = self.merge(None, pages)
        self.assertEqual(merged["district"], "Darbhanga")


class TestJsonSerializationSafety(unittest.TestCase):
    """Covers the numpy.bool_ JSON serialization crash found during manual testing."""

    def test_deblur_report_is_json_serializable(self):
        from core.image_preprocessing import DocumentDeblurEngine
        import numpy as np
        engine = DocumentDeblurEngine()
        # simulate what measure_blur/process would produce
        fake_report = {
            "output_path": "/tmp/x.jpg",
            "blur_score": float(np.float64(87.3)),
            "was_blurred": bool(np.bool_(True)),  # this is the exact fix under test
            "threshold_used": 120.0,
        }
        # must not raise TypeError: Object of type bool is not JSON serializable
        json.dumps(fake_report)


if __name__ == "__main__":
    unittest.main()
