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


if __name__ == "__main__":
    unittest.main()
