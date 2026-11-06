from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_upstreams.py"
SPEC = importlib.util.spec_from_file_location("check_upstreams", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, env=GIT_ENV, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def commit(repo: Path, name: str) -> str:
    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", name)
    return git(repo, "rev-parse", "HEAD")


class CheckUpstreamsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory(prefix="nuko-nova-unslop-upstreams-")
        self.base = Path(self._temp.name)
        self.references = self.base / "references"
        self.references.mkdir()
        self.lock_path = self.base / "upstreams.lock.json"
        self.output = self.base / "report.json"
        self.repos: dict[str, Path] = {}
        self.first: dict[str, str] = {}
        sources = []
        for source_id in ("alpha", "beta"):
            repo = self.references / f"{source_id}-checkout"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            self.first[source_id] = commit(repo, "one.txt")
            self.repos[source_id] = repo
            sources.append(
                {
                    "id": source_id,
                    "repository": f"example/{source_id}",
                    "url": str(repo),
                    "branch": "refs/heads/main",
                    "checkout": repo.name,
                    "reviewed_sha": self.first[source_id],
                    "reviewed_at": "2026-01-01",
                    "license": "MIT",
                    "monitored_paths": ["one.txt"],
                }
            )
        self.lock = {"schema_version": 1, "review_cadence": "weekly", "sources": sources}
        self.write_lock()
        patcher = mock.patch.object(MODULE, "LOCK_PATH", self.lock_path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def write_lock(self) -> None:
        self.lock_path.write_text(json.dumps(self.lock, indent=2) + "\n", encoding="utf-8")

    def read_lock(self) -> dict:
        return json.loads(self.lock_path.read_text(encoding="utf-8"))

    def run_check(self, *args: str) -> tuple[int, dict[str, dict]]:
        code = MODULE.main(
            [
                "--references-dir",
                str(self.references),
                "--format",
                "json",
                "--output",
                str(self.output),
                *args,
            ]
        )
        rows = json.loads(self.output.read_text(encoding="utf-8"))
        return code, {row["id"]: row for row in rows}

    def test_local_status_reports_current_pins(self) -> None:
        code, rows = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual({row["status"] for row in rows.values()}, {"current"})
        self.assertEqual(rows["alpha"]["observed_sha"], self.first["alpha"])

    def test_local_status_reports_new_checkout_commit_as_changed(self) -> None:
        head = commit(self.repos["alpha"], "two.txt")
        code, rows = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(rows["alpha"]["status"], "changed")
        self.assertEqual(rows["alpha"]["observed_sha"], head)
        self.assertEqual(rows["beta"]["status"], "current")

    def test_missing_checkout_is_unavailable_without_failing(self) -> None:
        self.lock["sources"][1]["checkout"] = "missing"
        self.write_lock()
        code, rows = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(rows["beta"]["status"], "unavailable")
        self.assertIsNone(rows["beta"]["observed_sha"])

    def test_accept_advances_only_the_named_pin(self) -> None:
        alpha_head = commit(self.repos["alpha"], "two.txt")
        commit(self.repos["beta"], "two.txt")
        code, rows = self.run_check("--accept", "alpha")
        self.assertEqual(code, 1)
        self.assertEqual(rows["alpha"]["status"], "current")
        self.assertEqual(rows["beta"]["status"], "changed")
        lock = self.read_lock()
        alpha, beta = lock["sources"]
        self.assertEqual(alpha["reviewed_sha"], alpha_head)
        self.assertEqual(alpha["reviewed_at"], datetime.now(timezone.utc).date().isoformat())
        self.assertEqual(beta["reviewed_sha"], self.first["beta"])
        self.assertEqual(beta["reviewed_at"], "2026-01-01")
        self.assertEqual(self.lock_path.read_text(encoding="utf-8"), json.dumps(lock, indent=2) + "\n")

    def test_accept_rejects_unknown_id_without_writing(self) -> None:
        before = self.lock_path.read_text(encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "unknown source id"):
            self.run_check("--accept", "gamma")
        self.assertEqual(self.lock_path.read_text(encoding="utf-8"), before)

    def test_accept_rejects_unavailable_source_without_writing(self) -> None:
        commit(self.repos["alpha"], "two.txt")
        self.lock["sources"][1]["checkout"] = "missing"
        self.write_lock()
        before = self.lock_path.read_text(encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "cannot accept unavailable source: beta"):
            self.run_check("--accept", "alpha", "--accept", "beta")
        self.assertEqual(self.lock_path.read_text(encoding="utf-8"), before)

    def test_refresh_reads_the_remote_branch_and_accepts_it(self) -> None:
        remote_head = commit(self.repos["alpha"], "two.txt")
        # A stale local checkout must not affect refresh mode.
        self.lock["sources"][0]["checkout"] = "missing"
        self.write_lock()
        code, rows = self.run_check("--refresh")
        self.assertEqual(code, 1)
        self.assertEqual(rows["alpha"]["status"], "changed")
        self.assertEqual(rows["alpha"]["observed_sha"], remote_head)
        code, rows = self.run_check("--refresh", "--accept", "alpha")
        self.assertEqual(code, 0)
        self.assertEqual(self.read_lock()["sources"][0]["reviewed_sha"], remote_head)

    def test_refresh_error_fails_the_check(self) -> None:
        self.lock["sources"][0]["url"] = str(self.base / "no-such-remote")
        self.write_lock()
        code, rows = self.run_check("--refresh")
        self.assertEqual(code, 2)
        self.assertEqual(rows["alpha"]["status"], "error")
        self.assertTrue(rows["alpha"]["error"])
        with self.assertRaisesRegex(SystemExit, "cannot accept unavailable source: alpha"):
            self.run_check("--refresh", "--accept", "alpha")


if __name__ == "__main__":
    unittest.main()
