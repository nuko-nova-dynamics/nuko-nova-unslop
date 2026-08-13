from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_marketplace_entries.py"
SPEC = importlib.util.spec_from_file_location("render_marketplace_entries", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class MarketplaceEntryTests(unittest.TestCase):
    def test_dual_entries_share_immutable_source(self) -> None:
        sha = "a" * 40
        entries = MODULE.build_entries(sha, "nuko-nova-unslop-marketplace-v0.2.1")
        self.assertEqual(entries["codex"]["source"], entries["claude"]["source"])
        self.assertEqual(entries["codex"]["version"], entries["claude"]["version"])
        self.assertEqual(entries["codex"]["source"]["sha"], sha)
        self.assertEqual(entries["codex"]["source"]["url"], entries["codex"]["repository"] + ".git")
        self.assertEqual(entries["codex"]["policy"]["installation"], "AVAILABLE")
        self.assertIn("all human-facing writing", entries["codex"]["description"])

    def test_invalid_sha_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.build_entries("abc", "release")


if __name__ == "__main__":
    unittest.main()
