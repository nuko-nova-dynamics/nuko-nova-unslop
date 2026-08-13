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


def rule_ids(text: str, profile: str) -> set[str]:
    return {finding.rule_id for finding in MODULE.lint_text(text, profile)}


class LinterTests(unittest.TestCase):
    def test_eval_matrix(self) -> None:
        cases = json.loads((ROOT / "tests" / "eval-cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                text = (FIXTURES / case["file"]).read_text(encoding="utf-8")
                findings = MODULE.lint_text(text, case["profile"])
                ids = {finding.rule_id for finding in findings}
                self.assertTrue(set(case["required_rules"]) <= ids, ids)
                self.assertFalse(set(case["forbidden_rules"]) & ids, ids)
                if "max_findings" in case:
                    self.assertLessEqual(len(findings), case["max_findings"], findings)

    def test_code_and_link_targets_are_exempt(self) -> None:
        text = "Use `delve` as the enum name. See [documentation](https://example.com/testament)."
        ids = rule_ids(text, "strict")
        self.assertNotIn("watched-vocabulary", ids)

    def test_output_has_no_ai_score(self) -> None:
        findings = MODULE.lint_text("Certainly! I hope this helps.", "balanced")
        rendered = MODULE.render_text("draft.md", findings).lower()
        self.assertNotIn("ai score", rendered)
        self.assertNotIn("probability", rendered)

    def test_sentence_initial_chatbot_openers_match(self) -> None:
        self.assertIn("chatbot-artifact", rule_ids("Certainly, the report is attached.", "balanced"))
        self.assertIn("chatbot-artifact", rule_ids("Of course! The rollout is on track.", "balanced"))

    def test_mid_sentence_of_course_is_not_flagged(self) -> None:
        self.assertNotIn("chatbot-artifact", rule_ids("She was, of course, right about the cache.", "balanced"))

    def test_human_email_closer_is_not_flagged(self) -> None:
        self.assertNotIn("chatbot-artifact", rule_ids("Let me know if Thursday still works for the handoff.", "balanced"))
        self.assertIn("chatbot-artifact", rule_ids("Let me know if you would like me to expand this section.", "balanced"))

    def test_curly_apostrophes_match_phrase_rules(self) -> None:
        self.assertIn("collaborative-cta", rule_ids("Let’s build something together.", "nuko-nova"))
        self.assertIn("negative-reframe", rule_ids("It’s not just a dashboard; it’s a platform.", "balanced"))

    def test_cutoff_disclaimer_is_flagged(self) -> None:
        self.assertIn("cutoff-disclaimer", rule_ids("As of my last knowledge update, the API had no retry limit.", "balanced"))

    def test_hedging_filler_is_flagged(self) -> None:
        self.assertIn("hedging-filler", rule_ids("It's worth noting that the deadline moved to Friday.", "balanced"))

    def test_interpretive_connector_is_profile_scoped(self) -> None:
        text = "This underscores the need for faster reviews."
        self.assertIn("interpretive-label", rule_ids(text, "strict"))
        self.assertNotIn("interpretive-label", rule_ids(text, "balanced"))
        self.assertNotIn("interpretive-label", rule_ids("This signals the scheduler to stop the worker.", "strict"))

    def test_via_negativa_covers_house_nouns(self) -> None:
        self.assertIn("via-negativa", rule_ids("No prep. No fuss. No fees.", "nuko-nova"))

    def test_en_dash_ranges_are_never_dash_findings(self) -> None:
        self.assertNotIn("dash-cluster", rule_ids("Sales grew 12% across 2019–2024 in every region.", "strict"))

    def test_structural_dashes_remain_contextual_in_balanced_profile(self) -> None:
        text = "- **Speed** — the build finishes in four seconds.\n## [3.21.0] — 2026-07-30\n"
        self.assertNotIn("dash-cluster", rule_ids(text, "balanced"))
        self.assertIn("dash-cluster", rule_ids(text, "strict"))

    def test_quoted_dashes_and_patterns_are_exempt(self) -> None:
        text = 'The contract says, “No prep — no fees.” Keep that language exact.'
        self.assertNotIn("dash-cluster", rule_ids(text, "nuko-nova"))
        self.assertNotIn("via-negativa", rule_ids(text, "nuko-nova"))

    def test_spaced_double_hyphen_is_not_a_dash_workaround(self) -> None:
        text = "The launch slipped -- the vendor missed the deadline."
        self.assertIn("dash-substitute", rule_ids(text, "strict"))
        self.assertNotIn("dash-substitute", rule_ids("Run npm install --save-dev today.", "strict"))

    def test_single_prose_em_dash_flagged_in_house_profile(self) -> None:
        text = "The launch slipped a week — the vendor missed the deadline."
        self.assertIn("dash-cluster", rule_ids(text, "nuko-nova"))
        self.assertIn("dash-cluster", rule_ids(text, "strict"))
        self.assertNotIn("dash-cluster", rule_ids(text, "balanced"))

    def test_checklists_are_not_staccato(self) -> None:
        self.assertNotIn("staccato-drama", rule_ids("- Run tests.\n- Fix lint.\n- Ship it.\n", "balanced"))
        self.assertIn("staccato-drama", rule_ids("Fast. Simple. Powerful.", "balanced"))


if __name__ == "__main__":
    unittest.main()
