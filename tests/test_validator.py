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
            shutil.copytree(SOURCE, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
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

    def test_cadence_drift_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            path = root / "upstreams.lock.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["review_cadence"] = "monthly"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        self.assert_rejected(mutate, "cadence must be every-other-day")


if __name__ == "__main__":
    unittest.main()
