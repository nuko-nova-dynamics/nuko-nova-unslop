from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "nuko-nova-unslop" / "scripts"


class PackagedHelperTests(unittest.TestCase):
    def test_copied_helpers_work_outside_the_repository(self) -> None:
        with tempfile.TemporaryDirectory(prefix="unslop-helpers-") as temporary:
            root = Path(temporary)
            installed = root / "installed" / "scripts"
            shutil.copytree(SCRIPTS, installed, ignore=shutil.ignore_patterns("__pycache__"))
            source = "- ```text\n  delve\n  ```\nOutside prose says leverage.\n"
            lint = subprocess.run(
                [sys.executable, "-E", "-B", str(installed / "unslop_lint.py"),
                 "--profile", "strict", "--format", "json"],
                input=source, cwd=root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(lint.returncode, 0, lint.stderr)
            findings = json.loads(lint.stdout)[0]["findings"]
            self.assertEqual([(item["rule_id"], item["line"]) for item in findings],
                             [("watched-vocabulary", 4)])

            before = root / "source.md"
            after = root / "rewrite.md"
            before.write_text(source, encoding="utf-8")
            after.write_text(source.replace("delve", "changed"), encoding="utf-8")
            guard = subprocess.run(
                [sys.executable, "-E", "-B", str(installed / "preservation_guard.py"),
                 str(before), str(after), "--format", "json"],
                cwd=root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(guard.returncode, 1, guard.stderr)
            self.assertEqual(set(json.loads(guard.stdout)["differences"]), {"fenced_code"})
            self.assertNotIn("delve", guard.stdout)
