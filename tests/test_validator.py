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


class ValidatorMutationTests(unittest.TestCase):
    def assert_rejected(
        self,
        mutate: Callable[[Path], None],
        expected: str,
    ) -> None:
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
            result = run_validator(root)
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, combined)
            self.assertIn(expected, combined)

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

    def test_bad_source_pin_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "upstreams.lock.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["sources"][0]["reviewed_sha"] = "main"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        self.assert_rejected(mutate, "invalid reviewed SHA")

    def test_missing_reference_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "skills" / "nuko-nova-unslop" / "references" / "source-map.md").unlink()

        self.assert_rejected(mutate, "reference set mismatch")

    def test_implicit_invocation_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "nuko-nova-unslop" / "agents" / "openai.yaml"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("allow_implicit_invocation: true", "allow_implicit_invocation: false"), encoding="utf-8")

        self.assert_rejected(mutate, "OpenAI implicit invocation must remain enabled")

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

    def test_delegated_prose_guard_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "nuko-nova-unslop" / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("Treat delegated prose as unreviewed source material", "Delegated prose may be returned directly"),
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "parent review of delegated prose")

    def test_preference_continuity_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "nuko-nova-unslop" / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("Carry explicit writing corrections forward", "Ignore prior writing corrections"),
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "carry explicit writing corrections forward")

    def test_no_cringe_contract_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "skills" / "nuko-nova-unslop" / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("Apply the no-cringe standard as a context test", "Treat cringe as an undefined preference"),
                encoding="utf-8",
            )

        self.assert_rejected(mutate, "no-cringe context test")

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

        self.assert_rejected(mutate, "cadence must be every-two-days")


if __name__ == "__main__":
    unittest.main()
