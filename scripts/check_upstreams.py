#!/usr/bin/env python3
"""Report changes against reviewed upstream pins and optionally accept them."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "upstreams.lock.json"
DEFAULT_REFERENCES = ROOT.parent / "_reference" / "nuko-nova-unslop-sources"


def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "command failed")
    return result.stdout.strip()


def remote_head(source: dict) -> str:
    output = run("git", "ls-remote", source["url"], source["branch"])
    if not output:
        raise RuntimeError(f"no remote ref returned for {source['id']}:{source['branch']}")
    return output.split()[0]


def local_head(source: dict, references: Path) -> str | None:
    checkout = references / source["checkout"]
    if not (checkout / ".git").exists():
        return None
    return run("git", "rev-parse", "HEAD", cwd=checkout)


def report(lock: dict, refresh: bool, references: Path) -> list[dict]:
    rows = []
    for source in lock["sources"]:
        try:
            observed = remote_head(source) if refresh else local_head(source, references)
            status = "unavailable" if observed is None else "current" if observed == source["reviewed_sha"] else "changed"
            error = None
        except RuntimeError as exc:
            observed = None
            status = "error"
            error = str(exc)
        rows.append(
            {
                "id": source["id"],
                "repository": source["repository"],
                "reviewed_sha": source["reviewed_sha"],
                "observed_sha": observed,
                "status": status,
                "monitored_paths": source["monitored_paths"],
                "error": error,
            }
        )
    return rows


def render_markdown(rows: list[dict], refreshed: bool) -> str:
    mode = "remote" if refreshed else "local reference"
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# Nuko Nova Unslop upstream review",
        "",
        f"Generated: {now}",
        f"Observation mode: {mode}",
        "",
        "| Source | Status | Reviewed | Observed |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        observed = row["observed_sha"][:12] if row["observed_sha"] else "-"
        lines.append(f"| `{row['id']}` | {row['status']} | `{row['reviewed_sha'][:12]}` | `{observed}` |")
    changed = [row for row in rows if row["status"] == "changed"]
    errors = [row for row in rows if row["status"] in {"error", "unavailable"}]
    if changed:
        lines.extend(["", "## Review required", ""])
        for row in changed:
            paths = ", ".join(f"`{path}`" for path in row["monitored_paths"])
            lines.append(f"- `{row['id']}` changed. Inspect: {paths}.")
    if errors:
        lines.extend(["", "## Incomplete checks", ""])
        for row in errors:
            detail = row["error"] or "local checkout unavailable"
            lines.append(f"- `{row['id']}`: {detail}")
    if not changed and not errors:
        lines.extend(["", "No upstream review is required."])
    lines.extend(
        [
            "",
            "A changed SHA is a review trigger, not evidence that the plugin should change. Do not accept a pin until relevant diffs and regressions pass.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check reviewed upstream commit pins.")
    parser.add_argument("--refresh", action="store_true", help="Read current remote refs with git ls-remote")
    parser.add_argument("--references-dir", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--accept", action="append", default=[], metavar="SOURCE_ID")
    args = parser.parse_args(argv)

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    rows = report(lock, args.refresh, args.references_dir)
    by_id = {row["id"]: row for row in rows}
    if args.accept:
        unknown = sorted(set(args.accept) - set(by_id))
        if unknown:
            raise SystemExit(f"unknown source id(s): {', '.join(unknown)}")
        for source in lock["sources"]:
            if source["id"] not in args.accept:
                continue
            row = by_id[source["id"]]
            if row["status"] not in {"current", "changed"} or not row["observed_sha"]:
                raise SystemExit(f"cannot accept unavailable source: {source['id']}")
            source["reviewed_sha"] = row["observed_sha"]
            source["reviewed_at"] = datetime.now(timezone.utc).date().isoformat()
        LOCK_PATH.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        rows = report(lock, False, args.references_dir)

    if args.format == "json":
        output = json.dumps(rows, indent=2) + "\n"
    else:
        output = render_markdown(rows, args.refresh)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 2 if any(row["status"] == "error" for row in rows) else 1 if any(row["status"] == "changed" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
