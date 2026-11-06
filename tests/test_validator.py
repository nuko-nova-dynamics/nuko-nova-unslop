from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Callable


SOURCE = Path(__file__).resolve().parents[1]


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(root / "tests" / "validate_bundle.py")],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def manifest_version(root: Path) -> str:
    return json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]


def edit_lock(root: Path, change: Callable[[dict], None]) -> None:
    path = root / "upstreams.lock.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def drop_source_map_row(root: Path, repository: str) -> None:
    path = root / "docs" / "source-map.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if f"(https://github.com/{repository})" not in line]
    assert len(kept) == len(lines) - 1, repository
    path.write_text("".join(kept), encoding="utf-8")


class ValidatorMutationTests(unittest.TestCase):
    def run_mutated(self, mutate: Callable[[Path], None]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="nuko-nova-unslop-validator-") as temp:
            root = Path(temp) / "plugin"
            shutil.copytree(
                SOURCE,
                root,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".wrangler",
                    "__pycache__",
                    "coverage",
                    "dist",
                    "node_modules",
                ),
            )
            mutate(root)
            return run_validator(root)

    def assert_rejected(
        self,
        mutate: Callable[[Path], None],
        expected: str,
    ) -> None:
        result = self.run_mutated(mutate)
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, combined)
        self.assertIn(expected, combined)

    def assert_accepted(self, mutate: Callable[[Path], None]) -> None:
        result = self.run_mutated(mutate)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_baseline_passes(self) -> None:
        result = run_validator(SOURCE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / ".claude-plugin" / "plugin.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["version"] = "9.9.9"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        self.assert_rejected(mutate, "client manifests disagree on version")

    def test_inline_hooks_are_rejected_in_either_manifest(self) -> None:
        for client in (".codex-plugin", ".claude-plugin"):
            with self.subTest(client=client):
                def mutate(root: Path) -> None:
                    path = root / client / "plugin.json"
                    data = json.loads(path.read_text(encoding="utf-8"))
                    data["hooks"] = {"Stop": [{"hooks": [{"type": "command", "command": "exit 0"}]}]}
                    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

                self.assert_rejected(mutate, "lifecycle hooks must not be declared")

    def test_matching_missing_manifest_metadata_is_rejected(self) -> None:
        for field in ("author", "homepage", "repository"):
            with self.subTest(field=field):
                def mutate(root: Path) -> None:
                    for client in (".codex-plugin", ".claude-plugin"):
                        path = root / client / "plugin.json"
                        data = json.loads(path.read_text(encoding="utf-8"))
                        del data[field]
                        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

                self.assert_rejected(mutate, f"invalid manifest {field}")

    def test_matching_invalid_manifest_metadata_is_rejected(self) -> None:
        for field, value in (("author", {"name": ""}), ("homepage", []), ("repository", " ")):
            with self.subTest(field=field):
                def mutate(root: Path) -> None:
                    for client in (".codex-plugin", ".claude-plugin"):
                        path = root / client / "plugin.json"
                        data = json.loads(path.read_text(encoding="utf-8"))
                        data[field] = value
                        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

                self.assert_rejected(mutate, f"invalid manifest {field}")

    def test_manifest_json_must_be_an_object(self) -> None:
        def mutate(root: Path) -> None:
            (root / ".codex-plugin" / "plugin.json").write_text("[]\n", encoding="utf-8")

        self.assert_rejected(mutate, "expected a JSON object")

    def test_bad_source_pin_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "upstreams.lock.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["sources"][0]["reviewed_sha"] = "main"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        self.assert_rejected(mutate, "invalid reviewed SHA")

    def test_missing_reference_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "skills" / "nuko-nova-unslop" / "references" / "editorial-contract.md").unlink()

        self.assert_rejected(mutate, "reference set mismatch")

    def test_missing_shared_markdown_module_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "skills" / "nuko-nova-unslop" / "scripts" / "markdown_source.py").unlink()

        self.assert_rejected(mutate, "script set mismatch")

    def test_missing_short_alias_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            shutil.rmtree(root / "skills" / "unslop")

        self.assert_rejected(mutate, "alias skill")

    def test_missing_standalone_super_tighten_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            shutil.rmtree(root / "skills" / "super-tighten")

        self.assert_rejected(mutate, "standalone super-tighten skill is missing")

    def test_super_tighten_cannot_regress_to_a_router(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "super-tighten" / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nRead [the full writing workflow](../nuko-nova-unslop/SKILL.md).\n",
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "must not depend on another local resource")

    def test_super_tighten_invocation_metadata_cannot_point_to_tighten(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "super-tighten" / "agents" / "openai.yaml"
            path.write_text(
                path.read_text(encoding="utf-8").replace("Use $super-tighten", "Use $tighten"),
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "default prompt must name its own invocation")

    def test_alias_behavior_duplication_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "unslop" / "SKILL.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n## Non-negotiable contract\n", encoding="utf-8")

        self.assert_rejected(mutate, "must not duplicate canonical behavior")

    def test_implicit_invocation_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "nuko-nova-unslop" / "agents" / "openai.yaml"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("allow_implicit_invocation: true", "allow_implicit_invocation: false"), encoding="utf-8")

        self.assert_rejected(mutate, "OpenAI implicit invocation must remain enabled")

    def test_alias_implicit_invocation_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "unslop" / "agents" / "openai.yaml"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("allow_implicit_invocation: false", "allow_implicit_invocation: true"), encoding="utf-8")

        self.assert_rejected(mutate, "alias OpenAI invocation must remain explicit")

    def test_missing_tighten_command_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            shutil.rmtree(root / "skills" / "tighten")

        self.assert_rejected(mutate, "tighten command skill is missing")

    def test_tighten_route_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "tighten" / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("../nuko-nova-unslop/SKILL.md", "../unslop/SKILL.md"),
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "tighten command must route to the canonical skill")

    def test_tighten_implicit_invocation_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "tighten" / "agents" / "openai.yaml"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("allow_implicit_invocation: false", "allow_implicit_invocation: true"), encoding="utf-8")

        self.assert_rejected(mutate, "tighten OpenAI invocation must remain explicit")

    def test_tighten_default_prompt_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "tighten" / "agents" / "openai.yaml"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("Use $tighten:", "Use Tighten to"), encoding="utf-8")

        self.assert_rejected(mutate, "tighten OpenAI default prompt must name $tighten")

    def test_forced_output_style_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "output-styles" / "nuko-nova-unslop.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("force-for-plugin: true", "force-for-plugin: false"), encoding="utf-8")

        self.assert_rejected(mutate, "Claude output style must stay forced")

    def test_hook_bundle_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            hooks = root / "hooks"
            hooks.mkdir()
            (hooks / "hooks.json").write_text('{"hooks": {}}\n', encoding="utf-8")

        self.assert_rejected(mutate, "lifecycle hook bundle must not be shipped")

    def test_missing_output_style_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "output-styles" / "nuko-nova-unslop.md").unlink()

        self.assert_rejected(mutate, "Claude output style is missing")

    def test_unapproved_writing_evaluation_restriction_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "nuko-nova-unslop" / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nDo not optimize for detector evasion.\n",
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "unapproved writing-evaluation restriction")

    def test_unrouted_reference_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "nuko-nova-unslop" / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("(references/tighten.md)", "(tighten.md)"), encoding="utf-8")

        self.assert_rejected(mutate, "canonical skill must route to references/tighten.md")

    def test_missing_artwork_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "assets" / "logo-dark.png").unlink()

        self.assert_rejected(mutate, "missing artwork")

    def test_artwork_dimension_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "assets" / "icon.png"
            data = bytearray(path.read_bytes())
            data[16:24] = (128).to_bytes(4, "big") + (256).to_bytes(4, "big")
            path.write_bytes(data)

        self.assert_rejected(mutate, "expected 256x256")

    def test_cadence_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "upstreams.lock.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["review_cadence"] = "monthly"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        self.assert_rejected(mutate, "cadence must be weekly")

    def test_changelog_version_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "CHANGELOG.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("# Changelog\n", "# Changelog\n\n## 99.0.0 - 2099-01-01\n\n- Future.\n", 1),
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "CHANGELOG.md: first release heading '99.0.0' does not match manifest version")

    def test_changelog_unreleased_heading_is_ignored(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "CHANGELOG.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("# Changelog\n", "# Changelog\n\n## Unreleased\n\n- Pending.\n", 1),
                encoding="utf-8",
            )

        self.assert_accepted(mutate)

    def test_manifest_version_bump_without_changelog_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            for client in (".codex-plugin", ".claude-plugin"):
                path = root / client / "plugin.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                data["version"] = "99.0.0"
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        self.assert_rejected(mutate, "does not match manifest version 99.0.0")

    def test_readme_marketplace_ref_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "README.md"
            text = path.read_text(encoding="utf-8")
            current = f"nuko-nova-unslop-marketplace-v{manifest_version(root)}"
            self.assertIn(current, text)
            path.write_text(text.replace(current, "nuko-nova-unslop-marketplace-v0.0.1"), encoding="utf-8")

        self.assert_rejected(mutate, "README.md: marketplace --ref nuko-nova-unslop-marketplace-v0.0.1 does not match manifest version")

    def test_upstream_count_is_not_fixed(self) -> None:
        def mutate(root: Path) -> None:
            removed: list[str] = []
            edit_lock(root, lambda data: removed.append(data["sources"].pop(0)["repository"]))
            drop_source_map_row(root, removed[0])

        self.assert_accepted(mutate)

    def test_locked_source_without_source_map_row_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            repository = json.loads((root / "upstreams.lock.json").read_text(encoding="utf-8"))["sources"][0]["repository"]
            drop_source_map_row(root, repository)

        self.assert_rejected(mutate, "docs/source-map.md: missing source row for")

    def test_source_map_row_without_lock_entry_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            edit_lock(root, lambda data: data["sources"].pop(0))

        self.assert_rejected(mutate, "has no entry in upstreams.lock.json")

    def test_duplicate_upstream_id_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            def change(data: dict) -> None:
                data["sources"][1]["id"] = data["sources"][0]["id"]

            edit_lock(root, change)

        self.assert_rejected(mutate, "upstream ids must be unique")

    def test_non_github_upstream_url_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            def change(data: dict) -> None:
                data["sources"][0]["url"] = "https://example.com/vale.git"

            edit_lock(root, change)

        self.assert_rejected(mutate, "expected GitHub HTTPS URL")


if __name__ == "__main__":
    unittest.main()
