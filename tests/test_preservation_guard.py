from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "skills" / "nuko-nova-unslop" / "scripts" / "preservation_guard.py"
SPEC = importlib.util.spec_from_file_location("preservation_guard", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PreservationTests(unittest.TestCase):
    def test_safe_rewrite_preserves_surface_tokens(self) -> None:
        source = (FIXTURES / "protected-source.md").read_text(encoding="utf-8")
        rewrite = (FIXTURES / "protected-safe.md").read_text(encoding="utf-8")
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_drift_is_reported(self) -> None:
        source = (FIXTURES / "protected-source.md").read_text(encoding="utf-8")
        rewrite = (FIXTURES / "protected-drift.md").read_text(encoding="utf-8")
        differences = MODULE.compare(source, rewrite)
        self.assertIn("version", differences)
        self.assertIn("date", differences)
        self.assertIn("flag", differences)
        self.assertIn("number", differences)
        self.assertIn("quote", differences)

    def test_sentence_final_number_drift_is_reported(self) -> None:
        differences = MODULE.compare("Invalid files exit with code 2.", "Invalid files exit with code 3.")
        self.assertIn("number", differences)
        self.assertEqual(differences["number"]["missing"], {"2": 1})
        self.assertEqual(differences["number"]["added"], {"3": 1})

    def test_en_dash_range_corruption_is_reported(self) -> None:
        differences = MODULE.compare("Sales grew across 2019–2024.", "Sales grew across 2019-2024.")
        self.assertIn("range", differences)
        self.assertEqual(differences["range"]["missing"], {"2019–2024": 1})
        self.assertEqual(differences["range"]["added"], {"2019-2024": 1})

    def test_preserved_range_passes(self) -> None:
        self.assertEqual(
            MODULE.compare(
                "Sales grew across 2019–2024.",
                "Sales, to everyone's relief, grew across 2019–2024.",
            ),
            {},
        )

    def test_claim_scope_drift_is_reported(self) -> None:
        differences = MODULE.compare(
            "Only the first migration ran; both workers updated the cache simultaneously.",
            "The migration ran; the workers updated the cache.",
        )
        self.assertEqual(
            differences["claim_scope"]["missing"],
            {"only": 1, "first": 1, "both": 1, "simultaneously": 1},
        )
        self.assertEqual(differences["claim_scope"]["added"], {})

    def test_preserved_claim_scope_passes_case_changes(self) -> None:
        self.assertEqual(
            MODULE.compare(
                "Only the first migration ran; both workers finished at once.",
                "The first migration was the only one to run; at once, both workers finished.",
            ),
            {},
        )

    def test_nested_fence_edit_is_reported(self) -> None:
        source = (
            "Before.\n"
            "````markdown\n"
            "```python\n"
            "print('original')\n"
            "```\n"
            "````\n"
            "After.\n"
        )
        rewrite = source.replace("print('original')", "print('changed')")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(
            differences["fenced_code"],
            {
                "missing": {"block #1 original": 1},
                "added": {"block #1 rewrite": 1},
            },
        )

    def test_different_marker_does_not_close_fence(self) -> None:
        source = "```markdown\n~~~text\nprotected content\n~~~\n```\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_indented_fence_closes_before_editable_prose(self) -> None:
        source = "   ~~~python\nprint('fixed')\n   ~~~\nOriginal prose.\n"
        rewrite = "   ~~~python\nprint('fixed')\n   ~~~\nRewritten prose.\n"
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_unclosed_fence_edit_is_reported(self) -> None:
        source = "```text\nprotected content\n"
        rewrite = "```text\nchanged content\n"
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_fenced_code_line_ending_change_passes(self) -> None:
        source = "```text\r\nprotected content\r\n```\r\n"
        rewrite = "```text\nprotected content\n```\n"
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_block_quote_fence_edit_is_reported(self) -> None:
        source = "> ```text\n> protected content\n> ```\nOutside prose.\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_list_item_fence_edit_is_reported(self) -> None:
        source = "1. item\n\n   ```text\n   protected content\n   ```\nOutside prose.\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_list_marker_fence_edit_is_reported(self) -> None:
        source = "- ```text\n  protected content\n  ```\nOutside prose.\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_fenced_code_values_are_redacted_from_generic_differences(self) -> None:
        source = '```text\nhttps://secret.example/v1.2.3 "private value"\n```\n'
        rewrite = '```text\nhttps://other.example/v9.8.7 "changed value"\n```\n'
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))
        self.assertNotIn("private value", str(differences))

    def test_backtick_in_info_string_is_not_a_fence_opener(self) -> None:
        source = "```bad`info\nOriginal prose.\n"
        rewrite = "```bad`info\nRewritten prose.\n"
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_quote_marker_inside_top_level_fence_is_code(self) -> None:
        source = "```text\n> ```\nprotected content\n```\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_deeper_quote_marker_inside_quoted_fence_is_code(self) -> None:
        source = "> ```text\n> > ```\n> protected content\n> ```\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_quote_marker_inside_list_fence_is_code(self) -> None:
        source = "- ```text\n  > ```\n  protected content\n  ```\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_list_containing_block_quote_fence_edit_is_reported(self) -> None:
        source = "- > ```text\n  > protected content\n  > ```\nOutside prose.\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_list_containing_block_quote_values_are_redacted(self) -> None:
        source = "- > ```text\n  > https://secret.example/v1.2.3\n  > ```\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_fence_after_nested_list_returns_to_parent_container(self) -> None:
        source = (
            "1. parent\n"
            "   - child\n"
            "     child prose\n"
            "\n"
            "   ```text\n"
            "   protected content\n"
            "   ```\n"
            "Outside prose.\n"
        )
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_tab_indented_list_fence_values_are_redacted(self) -> None:
        source = "- ```text\n\thttps://secret.example/v1.2.3\n\t```\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_tab_after_list_marker_opens_fence(self) -> None:
        source = "-\t```text\n\tprotected content\n\t```\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_ordered_list_extra_spacing_fence_values_are_redacted(self) -> None:
        source = "1.  item\n    ```text\n    https://secret.example/v1.2.3\n    ```\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_empty_list_item_can_contain_fence(self) -> None:
        source = "-\n  ```text\n  protected content\n  ```\n"
        rewrite = source.replace("protected content", "changed content")
        self.assertIn("fenced_code", MODULE.compare(source, rewrite))

    def test_quoted_tab_spaced_list_fence_values_are_redacted(self) -> None:
        source = "> -\t```text\n>   https://secret.example/v1.2.3\n>   ```\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_tab_indented_list_marker_inside_quote_is_protected(self) -> None:
        source = "> \t- ```text\n>     https://secret.example/v1.2.3\n>     ```\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_nested_quote_spacing_can_change_inside_list_fence(self) -> None:
        source = ">>- \t```text\n>>      https://secret.example/v1.2.3\n>>      ```\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_quote_space_can_belong_to_following_list_indentation(self) -> None:
        source = (
            " > -  > ```text\n"
            ">    > https://secret.example/v1.2.3\n"
            ">    > ```\n"
        )
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_quote_tab_overhang_is_preserved_for_list_indentation(self) -> None:
        source = (
            " > -  > ```text\n"
            ">\t >\thttps://secret.example/v1.2.3\n"
            ">    >```\n"
        )
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_nested_quote_spacing_can_change_inside_fence(self) -> None:
        source = (
            "> > ```text\n"
            ">     > https://secret.example/v1.2.3\n"
            "> > ```\n"
        )
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))

    def test_nested_quote_tab_overhang_can_change_inside_fence(self) -> None:
        source = (
            "> > ```text\n"
            ">\t   > https://secret.example/v1.2.3\n"
            "> > ```\n"
        )
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"fenced_code"})
        self.assertNotIn("secret.example", str(differences))


if __name__ == "__main__":
    unittest.main()
