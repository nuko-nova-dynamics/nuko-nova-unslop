from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "skills" / "nuko-nova-unslop" / "scripts" / "preservation_guard.py"
sys.path.insert(0, str(SCRIPT.parent))
import preservation_guard as MODULE


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

    def test_markdown_table_cell_edit_is_reported(self) -> None:
        source = "| Name | Status |\n| --- | --- |\n| Alpha | Ready |\n"
        rewrite = source.replace("Ready", "Paused")
        self.assertEqual(
            MODULE.compare(source, rewrite)["markdown_table"],
            {
                "missing": {"original table": 1},
                "added": {"rewrite table": 1},
            },
        )

    def test_markdown_table_without_outer_pipes_is_protected(self) -> None:
        source = "Name | Status\n--- | ---\nAlpha | Ready\n"
        rewrite = source.replace("Alpha", "Beta")
        self.assertIn("markdown_table", MODULE.compare(source, rewrite))

    def test_markdown_table_formatting_only_change_passes(self) -> None:
        source = "Name|Status\n-|---\nAlpha|Ready\n"
        rewrite = "| Name | Status |\n| ----- | ------- |\n| Alpha | Ready |\n"
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_markdown_table_alignment_change_is_reported(self) -> None:
        source = "Name | Status\n--- | ---\nAlpha | Ready\n"
        rewrite = "Name | Status\n:--- | ---:\nAlpha | Ready\n"
        self.assertIn("markdown_table", MODULE.compare(source, rewrite))

    def test_escaped_pipe_stays_inside_table_cell(self) -> None:
        source = "Name \\| alias | Status\n--- | ---\nAlpha \\| A | Ready\n"
        rewrite = source.replace("Alpha", "Beta")
        spans = MODULE.markdown_table_spans(source)
        self.assertEqual(len(spans), 1)
        self.assertIn("markdown_table", MODULE.compare(source, rewrite))

    def test_four_space_indented_pipe_text_is_not_a_table(self) -> None:
        text = "    Name | Status\n    --- | ---\n    Alpha | Ready\n"
        self.assertEqual(MODULE.markdown_table_spans(text), [])

    def test_bare_pipe_prose_is_not_a_table(self) -> None:
        source = "Use alpha | beta in the shell.\n"
        rewrite = "Use gamma | delta in the shell.\n"
        self.assertEqual(MODULE.markdown_table_spans(source), [])
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_malformed_table_shape_is_not_protected(self) -> None:
        text = "Name | Status\n--- | --- | ---\nAlpha | Ready\n"
        self.assertEqual(MODULE.markdown_table_spans(text), [])

    def test_table_values_are_redacted_from_generic_differences(self) -> None:
        source = '| Endpoint | Note |\n| --- | --- |\n| https://secret.example/v1.2.3 | "private value" |\n'
        rewrite = source.replace(
            'https://secret.example/v1.2.3 | "private value"',
            'https://other.example/v9.8.7 | "changed value"',
        )
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"markdown_table"})
        self.assertNotIn("secret.example", str(differences))
        self.assertNotIn("private value", str(differences))

    def test_table_syntax_inside_fence_is_only_fenced_code(self) -> None:
        source = "```text\nName | Status\n--- | ---\nAlpha | Ready\n```\n"
        rewrite = source.replace("Ready", "Paused")
        self.assertEqual(set(MODULE.compare(source, rewrite)), {"fenced_code"})

    def test_markdown_table_line_ending_change_passes(self) -> None:
        source = "Name | Status\r\n--- | ---\r\nAlpha | Ready\r\n"
        rewrite = "Name | Status\n--- | ---\nAlpha | Ready\n"
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_invalid_rewrite_table_does_not_leak_values(self) -> None:
        source = '| Endpoint | Note |\n| --- | --- |\n| https://secret.example/v1.2.3 | "private value" |\n'
        rewrite = 'Endpoint\nnot a delimiter\nhttps://other.example/v9.8.7 "changed value"\n'
        differences = MODULE.compare(source, rewrite)
        self.assertIn("markdown_table", differences)
        self.assertEqual(set(differences), {"markdown_table"})
        self.assertNotIn("secret.example", str(differences))
        self.assertNotIn("other.example", str(differences))
        self.assertNotIn("private value", str(differences))
        self.assertNotIn("changed value", str(differences))

    def test_newly_valid_table_does_not_leak_prior_values(self) -> None:
        source = 'Endpoint\nnot a delimiter\nhttps://secret.example/v1.2.3 "private value"\n'
        rewrite = '| Endpoint | Note |\n| --- | --- |\n| https://other.example/v9.8.7 | "changed value" |\n'
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"markdown_table"})
        self.assertNotIn("secret.example", str(differences))
        self.assertNotIn("other.example", str(differences))
        self.assertNotIn("private value", str(differences))
        self.assertNotIn("changed value", str(differences))

    def test_mixed_space_and_tab_indented_code_is_not_a_table(self) -> None:
        for indent in (" \t", "  \t", "   \t"):
            text = (
                f"{indent}Name | Status\n"
                f"{indent}--- | ---\n"
                f"{indent}Alpha | Ready\n"
            )
            self.assertEqual(MODULE.markdown_table_spans(text), [])

    def test_block_quote_table_cell_edit_is_reported(self) -> None:
        source = "> Name | Status\n> --- | ---\n> Alpha | Ready\n"
        rewrite = source.replace("Alpha", "Beta")
        self.assertEqual(set(MODULE.compare(source, rewrite)), {"markdown_table"})

    def test_list_table_formatting_only_change_passes(self) -> None:
        source = "- Name | Status\n  --- | ---\n  Alpha | Ready\n"
        rewrite = "- | Name | Status |\n  | ----- | ------- |\n  | Alpha | Ready |\n"
        self.assertEqual(MODULE.compare(source, rewrite), {})

    def test_nested_list_table_cell_edit_is_reported(self) -> None:
        source = (
            "- parent\n"
            "  - child\n"
            "    Name | Status\n"
            "    --- | ---\n"
            "    Alpha | Ready\n"
        )
        rewrite = source.replace("Alpha", "Beta")
        self.assertEqual(set(MODULE.compare(source, rewrite)), {"markdown_table"})

    def test_body_row_without_pipe_is_padded_and_protected(self) -> None:
        source = "Name | Status\n--- | ---\nhttps://secret.example/v1.2.3\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"markdown_table"})
        self.assertNotIn("secret.example", str(differences))

    def test_new_block_structure_ends_table(self) -> None:
        source = "Name | Status\n--- | ---\nAlpha | Ready\n> Quote | original\n"
        spans = MODULE.markdown_table_spans(source)
        self.assertEqual(len(spans), 1)
        self.assertNotIn("Quote", str(spans[0][2]))

    def test_extra_body_cells_remain_protected_source(self) -> None:
        source = "Name | Status\n--- | ---\nAlpha | Ready | ignored\n"
        rewrite = "Name | Status\n--- | ---\nAlpha | Ready\n"
        self.assertIn("markdown_table", MODULE.compare(source, rewrite))

    def test_extra_body_cell_value_change_is_reported(self) -> None:
        source = "Name | Status\n--- | ---\nAlpha | Ready | https://secret.example/v1.2.3\n"
        rewrite = source.replace("secret.example/v1.2.3", "other.example/v9.8.7")
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(set(differences), {"markdown_table"})
        self.assertNotIn("secret.example", str(differences))

    def test_list_indented_code_is_not_a_table(self) -> None:
        source = "-\n      Name | Status\n      --- | ---\n      Alpha | Ready\n"
        self.assertEqual(MODULE.markdown_table_spans(source), [])

    def test_raw_script_and_pre_blocks_are_not_markdown_tables(self) -> None:
        for tag in ("script", "pre"):
            text = (
                f"<{tag}>\n"
                "Name | Status\n"
                "--- | ---\n"
                "Alpha | Ready\n"
                f"</{tag}>\n"
            )
            self.assertEqual(MODULE.markdown_table_spans(text), [])

    def test_unrelated_drift_remains_visible_when_table_breaks(self) -> None:
        source = (
            "Name | Status\n"
            "--- | ---\n"
            "Alpha | Ready\n"
            "\n"
            "See https://outside.example/v1.0.0.\n"
        )
        rewrite = (
            "Name | Status\n"
            "not a delimiter\n"
            "Alpha | Ready\n"
            "\n"
            "See https://changed.example/v2.0.0.\n"
        )
        differences = MODULE.compare(source, rewrite)
        self.assertIn("markdown_table", differences)
        self.assertEqual(
            differences["url"],
            {
                "missing": {"https://outside.example/v1.0.0": 1},
                "added": {"https://changed.example/v2.0.0": 1},
            },
        )

    def test_duplicate_table_drift_has_no_false_ordinal(self) -> None:
        source = (
            "| Endpoint |\n| --- |\n| https://secret.example/v1.2.3 |\n\n"
            "| Endpoint |\n| --- |\n| https://secret.example/v1.2.3 |\n"
        )
        rewrite = (
            "Endpoint\n---\nhttps://secret.example/v1.2.3\n\n"
            "| Endpoint |\n| --- |\n| https://secret.example/v1.2.3 |\n"
        )
        differences = MODULE.compare(source, rewrite)
        self.assertEqual(
            differences["markdown_table"],
            {"missing": {"original table": 1}, "added": {}},
        )
        self.assertNotIn("secret.example", str(differences))

    def test_raw_html_and_comments_are_not_markdown_tables(self) -> None:
        for text in (
            "<div>\nName | Status\n--- | ---\nAlpha | Ready\n</div>\n",
            "<!--\nName | Status\n--- | ---\nAlpha | Ready\n-->\n",
        ):
            self.assertEqual(MODULE.markdown_table_spans(text), [])


if __name__ == "__main__":
    unittest.main()
