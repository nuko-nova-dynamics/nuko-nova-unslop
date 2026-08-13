#!/usr/bin/env python3
"""Render Nuko Nova marketplace entries from the synchronized manifests."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_entries(sha: str, ref: str) -> dict[str, dict]:
    if not SHA_RE.fullmatch(sha):
        raise ValueError("sha must contain 40 lowercase hexadecimal characters")
    if not ref.strip():
        raise ValueError("ref must be non-empty")
    codex = load(ROOT / ".codex-plugin" / "plugin.json")
    claude = load(ROOT / ".claude-plugin" / "plugin.json")
    if codex["repository"] != claude["repository"]:
        raise ValueError("client manifests disagree on repository")
    source = {
        "source": "url",
        "url": codex["repository"] + ".git",
        "ref": ref,
        "sha": sha,
    }
    codex_entry = {
        "name": codex["name"],
        "source": source,
        "version": codex["version"],
        "description": codex["description"],
        "author": {"name": codex["author"]["name"], "email": codex["author"]["email"]},
        "homepage": codex["homepage"],
        "repository": codex["repository"],
        "license": codex["license"],
        "keywords": codex["keywords"],
        "interface": codex["interface"],
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": codex["interface"]["category"],
    }
    claude_entry = {
        "name": claude["name"],
        "displayName": claude["displayName"],
        "version": claude["version"],
        "source": source,
        "description": claude["description"],
        "author": claude["author"],
        "homepage": claude["homepage"],
        "repository": claude["repository"],
        "license": claude["license"],
        "keywords": claude["keywords"],
        "category": "productivity",
        "tags": ["writing", "editing", "humanizer", "anti-slop", "voice"],
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
