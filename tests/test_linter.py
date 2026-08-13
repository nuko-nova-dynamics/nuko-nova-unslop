from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "skills" / "nuko-nova-unslop" / "scripts" / "unslop_lint.py"
SPEC = importlib.util.spec_from_file_location("unslop_lint", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LinterTests(unittest.TestCase):
    def test_eval_matrix(self) -> None:
        cases = json.loads((ROOT / "tests" / "eval-cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                text = (FIXTURES / case["file"]).read_text(encoding="utf-8")
                ids = {finding.rule_id for finding in MODULE.lint_text(text, case["profile"])}
                self.assertTrue(set(case["required_rules"]) <= ids, ids)
                self.assertFalse(set(case["forbidden_rules"]) & ids, ids)

    def test_code_and_link_targets_are_exempt(self) -> None:
        text = "Use `delve` as the enum name. See [documentation](https://example.com/testament)."
        ids = {finding.rule_id for finding in MODULE.lint_text(text, "strict")}
        self.assertNotIn("watched-vocabulary", ids)

    def test_output_has_no_ai_score(self) -> None:
        findings = MODULE.lint_text("Certainly! I hope this helps.", "balanced")
        rendered = MODULE.render_text("draft.md", findings).lower()
        self.assertNotIn("ai score", rendered)
        self.assertNotIn("probability", rendered)


if __name__ == "__main__":
    unittest.main()
