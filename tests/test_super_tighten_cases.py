from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "nuko-nova-unslop" / "scripts"))
import preservation_guard


def case_errors(candidate: str, case: dict) -> list[str]:
    errors = [f"missing meaning: {span}" for span in case["protected"] if span not in candidate]
    errors.extend(f"retained defect: {span}" for span in case["forbidden"] if span in candidate)
    if preservation_guard.compare(case["source"], candidate):
        errors.append("protected content drift")
    return errors


class SuperTightenCaseTests(unittest.TestCase):
    """Check synthetic reference edits, not model output or full STE conformance."""

    def test_reference_edits_preserve_source_and_remove_demonstrated_defects(self) -> None:
        cases = json.loads((ROOT / "tests" / "super-tighten-eval-cases.json").read_text())
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(case_errors(case["expected"], case), [])
                self.assertNotEqual(case_errors(case["invalid"], case), [])


if __name__ == "__main__":
    unittest.main()
