#!/usr/bin/env python3
"""Render Nuko Nova marketplace entries from the synchronized manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from release_metadata import load_release_metadata  # noqa: E402

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def build_entries(sha: str, ref: str, root: Path = ROOT) -> dict[str, dict]:
    if not SHA_RE.fullmatch(sha):
        raise ValueError("sha must contain 40 lowercase hexadecimal characters")
    if not ref.strip():
        raise ValueError("ref must be non-empty")
    metadata = load_release_metadata(root)
    codex, claude = metadata.codex, metadata.claude
    source = {
        "source": "url",
        "url": metadata.repository + ".git",
        "ref": ref,
        "sha": sha,
    }
    codex_entry = {
        "name": metadata.name,
        "source": source,
        "version": metadata.version,
        "description": metadata.description,
        "author": {"name": metadata.author["name"], "email": metadata.author["email"]},
        "homepage": metadata.homepage,
        "repository": metadata.repository,
        "license": metadata.license,
        "keywords": codex["keywords"],
        "interface": codex["interface"],
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": codex["interface"]["category"],
    }
    claude_entry = {
        "name": metadata.name,
        "displayName": claude["displayName"],
        "version": metadata.version,
        "source": source,
        "description": metadata.description,
        "author": metadata.author,
        "homepage": metadata.homepage,
        "repository": metadata.repository,
        "license": metadata.license,
        "keywords": claude["keywords"],
        "category": "productivity",
        "tags": ["writing", "humanizer", "anti-slop", "no-cringe", "voice"],
    }
    return {"codex": codex_entry, "claude": claude_entry}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render immutable dual-client marketplace entries.")
    parser.add_argument("--sha", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--client", choices=("codex", "claude", "both"), default="both")
    args = parser.parse_args()
    try:
        entries = build_entries(args.sha, args.ref)
    except ValueError as exc:
        parser.error(str(exc))
    output = entries if args.client == "both" else entries[args.client]
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
