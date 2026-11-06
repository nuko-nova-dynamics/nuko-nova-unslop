from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
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
        entries = MODULE.build_entries(sha, "nuko-nova-unslop-marketplace-v0.6.1")
        self.assertEqual(entries["codex"]["source"], entries["claude"]["source"])
        self.assertEqual(entries["codex"]["version"], entries["claude"]["version"])
        self.assertEqual(entries["codex"]["source"]["sha"], sha)
        self.assertEqual(entries["codex"]["source"]["url"], entries["codex"]["repository"] + ".git")
        self.assertEqual(entries["codex"]["policy"]["installation"], "AVAILABLE")
        description = entries["codex"]["description"].lower()
        self.assertIn("human-writing standard", description)
        self.assertIn("no slop or cringe", description)
        self.assertEqual(entries["codex"]["interface"]["composerIcon"], "./assets/icon.png")
        self.assertEqual(entries["codex"]["interface"]["logo"], "./assets/logo.png")
        self.assertEqual(entries["codex"]["interface"]["logoDark"], "./assets/logo-dark.png")

    def test_invalid_sha_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.build_entries("abc", "release")

    def test_entries_use_the_agreed_manifest_version(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        entries = MODULE.build_entries("a" * 40, "release")
        self.assertEqual(entries["codex"]["version"], manifest["version"])
        self.assertEqual(entries["claude"]["version"], manifest["version"])

    def test_manifest_drift_is_rejected_by_shared_metadata(self) -> None:
        for field, value in (("version", "9.9.9"), ("repository", "https://github.com/example/fork")):
            with self.subTest(field=field), tempfile.TemporaryDirectory(prefix="nuko-nova-unslop-entries-") as temp:
                root = Path(temp)
                for client in (".codex-plugin", ".claude-plugin"):
                    shutil.copytree(ROOT / client, root / client)
                path = root / ".claude-plugin" / "plugin.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                data[field] = value
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, f"client manifests disagree on {field}"):
                    MODULE.build_entries("a" * 40, "release", root=root)


if __name__ == "__main__":
    unittest.main()
