from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "skills" / "nuko-nova-unslop" / "scripts" / "preservation_guard.py"
sys.path.insert(0, str(SCRIPT.parent))
import preservation_guard as MODULE


def case_errors(source: str, candidate: str, case: dict) -> list[str]:
    errors: list[str] = []
    if len(candidate.split()) / len(source.split()) > case["maximum_word_ratio"]:
        errors.append("compression ratio exceeded")
    if MODULE.compare(source, candidate):
        errors.append("protected surface token drift")
    errors.extend(
        f"missing protected: {protected}"
        for protected in case["protected"]
        if protected not in candidate
    )
    errors.extend(
        f"retained removable: {removed}"
        for removed in case["removed"]
        if removed in candidate
    )
    return errors


class TightenCaseTests(unittest.TestCase):
    def test_synthetic_cases_compress_without_protected_token_drift(self) -> None:
        cases = json.loads((ROOT / "tests" / "tighten-eval-cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 2)

        for case in cases:
            with self.subTest(case=case["name"]):
                source = (FIXTURES / case["source"]).read_text(encoding="utf-8")
                expected = (FIXTURES / case["expected"]).read_text(encoding="utf-8")

                self.assertEqual(case_errors(source, expected, case), [])
                for removed in case["removed"]:
                    self.assertIn(removed, source)

    def test_semantic_markers_reject_overcompression_missed_by_surface_guard(self) -> None:
        cases = json.loads((ROOT / "tests" / "tighten-eval-cases.json").read_text(encoding="utf-8"))
        case = next(case for case in cases if case["name"] == "remove-repetition-and-indirection")
        source = (FIXTURES / "tighten-heavy.md").read_text(encoding="utf-8")
        overcompressed = (FIXTURES / "tighten-heavy-overcompressed.md").read_text(encoding="utf-8")

        self.assertEqual(MODULE.compare(source, overcompressed), {})
        self.assertIn(
            "missing protected: The September 18 launch remains on schedule.",
            case_errors(source, overcompressed, case),
        )


if __name__ == "__main__":
    unittest.main()
