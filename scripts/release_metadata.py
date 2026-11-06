#!/usr/bin/env python3
"""Load the two client manifests and expose the release metadata they agree on."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_MANIFEST = Path(".codex-plugin") / "plugin.json"
CLAUDE_MANIFEST = Path(".claude-plugin") / "plugin.json"
STRING_FIELDS = ("name", "version", "description", "homepage", "repository", "license")
SHARED_FIELDS = ("name", "version", "description", "author", "homepage", "repository", "license")
CHANGELOG_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
README_REF = re.compile(r"--ref\s+(\S+)")


class ReleaseMetadataError(ValueError):
    """Raised when a manifest is unreadable or the client manifests disagree."""


@dataclass(frozen=True)
class ReleaseMetadata:
    name: str
    version: str
    description: str
    author: dict
    homepage: str
    repository: str
    license: str
    codex: dict
    claude: dict

    @property
    def marketplace_ref(self) -> str:
        return f"{self.name}-marketplace-v{self.version}"


def load_manifest(root: Path, relative: Path) -> dict:
    path = root / relative
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseMetadataError(f"{relative.as_posix()}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReleaseMetadataError(f"{relative.as_posix()}: expected a JSON object")
    return data


def load_manifests(root: Path = ROOT) -> tuple[dict, dict]:
    """Return the parsed (codex, claude) manifests without checking agreement."""
    return load_manifest(root, CODEX_MANIFEST), load_manifest(root, CLAUDE_MANIFEST)


def agreed_metadata(codex: dict, claude: dict) -> ReleaseMetadata:
    """Check each manifest's shared fields and that both clients agree on them."""
    for client, manifest in (("Codex", codex), ("Claude", claude)):
        for field in STRING_FIELDS:
            value = manifest.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ReleaseMetadataError(f"{client}: invalid manifest {field}; expected a nonempty string")
        author = manifest.get("author")
        if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
            raise ReleaseMetadataError(f"{client}: invalid manifest author; expected an object with a nonempty name")
    for field in SHARED_FIELDS:
        if codex.get(field) != claude.get(field):
            raise ReleaseMetadataError(f"client manifests disagree on {field}")
    return ReleaseMetadata(
        **{field: codex[field] for field in SHARED_FIELDS},
        codex=codex,
        claude=claude,
    )


def load_release_metadata(root: Path = ROOT) -> ReleaseMetadata:
    return agreed_metadata(*load_manifests(root))


def changelog_version(text: str) -> str | None:
    """Return the version of the first release heading, skipping "## Unreleased"."""
    for match in CHANGELOG_HEADING.finditer(text):
        title = match.group(1)
        if title.lower() == "unreleased":
            continue
        return title.split()[0]
    return None


def readme_refs(text: str) -> list[str]:
    """Return every marketplace ref passed with --ref in the README."""
    return README_REF.findall(text)
