#!/usr/bin/env python3
"""Dependency-free integrity checks for the Nuko Nova Unslop plugin."""

from __future__ import annotations

import ast
import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_metadata import (  # noqa: E402
    ReleaseMetadata,
    ReleaseMetadataError,
    agreed_metadata,
    changelog_version,
    load_manifests,
    readme_refs,
)

SKILL = ROOT / "skills" / "nuko-nova-unslop"
ALIAS_SKILL = ROOT / "skills" / "unslop"
TIGHTEN_SKILL = ROOT / "skills" / "tighten"
SUPER_TIGHTEN_SKILL = ROOT / "skills" / "super-tighten"
OUTPUT_STYLE = ROOT / "output-styles" / "nuko-nova-unslop.md"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
SHA = re.compile(r"^[0-9a-f]{40}$")
GITHUB_REPOSITORY = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?(?=[/)#\s]|$)")
SOURCE_MAP = ROOT / "docs" / "source-map.md"
SOURCE_MAP_HEADER = "| Source | License | Reviewed value |"
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
REQUIRED_REFERENCES = {
    "editorial-contract.md",
    "interaction-calibration.md",
    "pattern-catalog.md",
    "profiles-and-genres.md",
    "tighten.md",
}
REQUIRED_SCRIPTS = {"markdown_source.py", "preservation_guard.py", "unslop_lint.py"}
PROFILES = {"balanced", "strict", "nuko-nova"}
ARTWORK = {
    "composerIcon": ("./assets/icon.png", 256),
    "logo": ("./assets/logo.png", 1254),
    "logoDark": ("./assets/logo-dark.png", 1254),
}
IGNORED_CONTENT_PARTS = {
    ".git",
    ".wrangler",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
}
FORBIDDEN_WRITING_RESTRICTIONS = (
    re.compile(r"\bdetector[- ]evasion\b", re.IGNORECASE),
    re.compile(r"\b(?:score|classify)\s+authorship\b", re.IGNORECASE),
    re.compile(r"\bAI probability\b", re.IGNORECASE),
    re.compile(r"\bAI score\b", re.IGNORECASE),
    re.compile(r"\bauthorship signal\b", re.IGNORECASE),
    re.compile(r"\bprove (?:the )?prose is human\b", re.IGNORECASE),
)


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)}: expected a JSON object")
    return data


def check_links(path: Path) -> None:
    for raw in LINK.findall(path.read_text(encoding="utf-8")):
        target = raw.split("#", 1)[0].split(maxsplit=1)[0].strip("<>")
        if not target or target.startswith(("https://", "http://", "mailto:")):
            continue
        resolved = (path.parent / unquote(target)).resolve()
        if not resolved.exists():
            fail(f"{path.relative_to(ROOT)}: broken link {raw}")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("skill: missing frontmatter")
    try:
        raw = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise AssertionError("skill: malformed frontmatter") from exc
    result = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            fail(f"skill: malformed frontmatter line {line!r}")
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail(f"{path.relative_to(ROOT)}: invalid PNG header")
    return struct.unpack(">II", data[16:24])


def check_manifests() -> ReleaseMetadata:
    try:
        codex, claude = load_manifests(ROOT)
        for client, manifest in (("Codex", codex), ("Claude", claude)):
            if "hooks" in manifest:
                fail(f"{client}: lifecycle hooks must not be declared")
        metadata = agreed_metadata(codex, claude)
    except ReleaseMetadataError as exc:
        fail(str(exc))
    if codex.get("name") != "nuko-nova-unslop":
        fail("plugin name mismatch")
    if not isinstance(codex.get("version"), str) or not SEMVER.fullmatch(codex["version"]):
        fail("plugin version must use semver")
    if codex.get("skills") != "./skills/":
        fail("Codex manifest must expose ./skills/")
    description = codex.get("description", "").lower()
    if "human-writing standard" not in description or "no slop or cringe" not in description:
        fail("plugin description must declare the human-writing and no-cringe standard")
    if codex.get("license") != "Apache-2.0":
        fail("plugin license must be Apache-2.0")
    if claude.get("displayName") != codex.get("interface", {}).get("displayName"):
        fail("client display names differ")
    if {"mcpServers", "apps"} & (set(codex) | set(claude)):
        fail("plugin declares an unsupported integration component")
    prompts = codex.get("interface", {}).get("defaultPrompt")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        fail("Codex defaultPrompt must contain one to three prompts")
    if any(not isinstance(item, str) or len(item) > 128 for item in prompts):
        fail("Codex defaultPrompt entries must be strings of at most 128 characters")
    interface = codex.get("interface", {})
    for field, (relative_path, expected_size) in ARTWORK.items():
        if interface.get(field) != relative_path:
            fail(f"Codex interface {field} path mismatch")
        artwork_path = ROOT / relative_path.removeprefix("./")
        if not artwork_path.is_file():
            fail(f"missing artwork: {relative_path}")
        width, height = png_dimensions(artwork_path)
        if (width, height) != (expected_size, expected_size):
            fail(f"{relative_path}: expected {expected_size}x{expected_size}, found {width}x{height}")
    return metadata


def check_release_references(metadata: ReleaseMetadata) -> None:
    heading = changelog_version((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    if heading != metadata.version:
        fail(f"CHANGELOG.md: first release heading {heading!r} does not match manifest version {metadata.version}")
    refs = readme_refs((ROOT / "README.md").read_text(encoding="utf-8"))
    if not refs:
        fail(f"README.md: missing marketplace --ref {metadata.marketplace_ref}")
    for ref in refs:
        if ref != metadata.marketplace_ref:
            fail(f"README.md: marketplace --ref {ref} does not match manifest version; expected {metadata.marketplace_ref}")


def check_skill() -> None:
    frontmatter = parse_frontmatter(SKILL / "SKILL.md")
    if set(frontmatter) != {"name", "description"}:
        fail("skill frontmatter must contain only name and description")
    if frontmatter["name"] != "nuko-nova-unslop":
        fail("skill name mismatch")
    if len(frontmatter["description"]) < 180 or "Use " not in frontmatter["description"]:
        fail("skill description must explain capability and triggers")
    references = {path.name for path in (SKILL / "references").iterdir() if path.is_file()}
    scripts = {path.name for path in (SKILL / "scripts").iterdir() if path.is_file() and path.suffix == ".py"}
    if references != REQUIRED_REFERENCES:
        fail(f"reference set mismatch: {sorted(references)}")
    if scripts != REQUIRED_SCRIPTS:
        fail(f"script set mismatch: {sorted(scripts)}")
    agent = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "Use $nuko-nova-unslop" not in agent:
        fail("OpenAI default prompt must name $nuko-nova-unslop")
    if not re.search(r"^\s*allow_implicit_invocation:\s*true\s*$", agent, re.MULTILINE):
        fail("OpenAI implicit invocation must remain enabled")
    match = re.search(r'^\s*short_description:\s*"([^"]+)"', agent, re.MULTILINE)
    if not match or not 25 <= len(match.group(1)) <= 64:
        fail("OpenAI short description must be 25 to 64 characters")
    if not OUTPUT_STYLE.is_file():
        fail("Claude output style is missing")
    style = parse_frontmatter(OUTPUT_STYLE)
    expected_style = {
        "name": "Nuko Nova Unslop",
        "description": "Always-on human writing with no slop or cringe",
        "keep-coding-instructions": "true",
        "force-for-plugin": "true",
    }
    if style != expected_style:
        fail("Claude output style must stay forced and retain coding instructions")
    skill_body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for reference in sorted(REQUIRED_REFERENCES):
        if f"(references/{reference})" not in skill_body:
            fail(f"canonical skill must route to references/{reference}")

    alias_entrypoint = ALIAS_SKILL / "SKILL.md"
    if not alias_entrypoint.is_file():
        fail("alias skill is missing")
    alias_frontmatter = parse_frontmatter(alias_entrypoint)
    if set(alias_frontmatter) != {"name", "description"}:
        fail("alias skill frontmatter must contain only name and description")
    if alias_frontmatter["name"] != "unslop":
        fail("alias skill name must be unslop")
    if not alias_frontmatter["description"].startswith("Short explicit alias for Nuko Nova Unslop"):
        fail("alias skill description must declare its narrow purpose")
    alias_body = alias_entrypoint.read_text(encoding="utf-8")
    if "../nuko-nova-unslop/SKILL.md" not in alias_body:
        fail("alias skill must route to the canonical skill")
    if len(alias_body) > 1_000 or "## Non-negotiable contract" in alias_body:
        fail("alias skill must not duplicate canonical behavior")
    alias_agent = (ALIAS_SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if not re.search(r"^\s*display_name:\s*\"Unslop\"\s*$", alias_agent, re.MULTILINE):
        fail("alias OpenAI metadata must display Unslop")
    if "Use $unslop" not in alias_agent:
        fail("alias OpenAI default prompt must name $unslop")
    if not re.search(r"^\s*allow_implicit_invocation:\s*false\s*$", alias_agent, re.MULTILINE):
        fail("alias OpenAI invocation must remain explicit")

    tighten_entrypoint = TIGHTEN_SKILL / "SKILL.md"
    if not tighten_entrypoint.is_file():
        fail("tighten command skill is missing")
    tighten_frontmatter = parse_frontmatter(tighten_entrypoint)
    if set(tighten_frontmatter) != {"name", "description"}:
        fail("tighten skill frontmatter must contain only name and description")
    if tighten_frontmatter["name"] != "tighten":
        fail("tighten skill name mismatch")
    if not tighten_frontmatter["description"].startswith("Focused command for tightening supplied prose"):
        fail("tighten skill description must declare its focused purpose")
    tighten_body = tighten_entrypoint.read_text(encoding="utf-8")
    if "../nuko-nova-unslop/SKILL.md" not in tighten_body:
        fail("tighten command must route to the canonical skill")
    if "references/tighten.md" not in tighten_body:
        fail("tighten command must route to its second-stage reference")
    if len(tighten_body) > 1_200 or "## Non-negotiable contract" in tighten_body:
        fail("tighten command must not duplicate canonical behavior")
    tighten_agent_path = TIGHTEN_SKILL / "agents" / "openai.yaml"
    if not tighten_agent_path.is_file():
        fail("tighten OpenAI metadata is missing")
    tighten_agent = tighten_agent_path.read_text(encoding="utf-8")
    if not re.search(r'^\s*display_name:\s*"Tighten"\s*$', tighten_agent, re.MULTILINE):
        fail("tighten OpenAI metadata must display Tighten")
    if "Use $tighten" not in tighten_agent:
        fail("tighten OpenAI default prompt must name $tighten")
    if not re.search(r"^\s*allow_implicit_invocation:\s*false\s*$", tighten_agent, re.MULTILINE):
        fail("tighten OpenAI invocation must remain explicit")

    for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
        check_links(path)
    check_links(ALIAS_SKILL / "SKILL.md")
    check_links(TIGHTEN_SKILL / "SKILL.md")
    for path in (SKILL / "scripts").glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            fail(f"{path.relative_to(ROOT)}: invalid Python: {exc}")

    for path in (ROOT / "scripts").glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            fail(f"{path.relative_to(ROOT)}: invalid Python: {exc}")


def check_no_hooks() -> None:
    if (ROOT / "hooks").exists():
        fail("lifecycle hook bundle must not be shipped")


def check_super_tighten() -> None:
    entrypoint = SUPER_TIGHTEN_SKILL / "SKILL.md"
    if not entrypoint.is_file():
        fail("standalone super-tighten skill is missing")
    frontmatter = parse_frontmatter(entrypoint)
    if set(frontmatter) != {"name", "description"} or frontmatter["name"] != "super-tighten":
        fail("super-tighten frontmatter must declare its standalone name and description")
    if "ASD-STE100" not in frontmatter["description"]:
        fail("super-tighten discovery must identify its controlled-language purpose")
    for raw in LINK.findall(entrypoint.read_text(encoding="utf-8")):
        if not raw.startswith(("https://", "http://", "mailto:", "#")):
            fail("super-tighten instructions must not depend on another local resource")
    agent_path = SUPER_TIGHTEN_SKILL / "agents" / "openai.yaml"
    if not agent_path.is_file():
        fail("super-tighten OpenAI metadata is missing")
    agent = agent_path.read_text(encoding="utf-8")
    if not re.search(r'^\s*display_name:\s*"Super Tighten"\s*$', agent, re.MULTILINE):
        fail("super-tighten OpenAI display name mismatch")
    if "Use $super-tighten" not in agent:
        fail("super-tighten default prompt must name its own invocation")
    check_links(entrypoint)
    check_links(ROOT / "research" / "super-tighten.md")


def source_map_repositories() -> dict[str, str]:
    """Map each lowercase owner/repo linked in the source-map table to its row's Source cell."""
    lines = SOURCE_MAP.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(SOURCE_MAP_HEADER)
    except ValueError:
        fail(f"docs/source-map.md: missing source table header {SOURCE_MAP_HEADER!r}")
    rows: dict[str, str] = {}
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cell = line.split("|")[1].strip()
        match = GITHUB_REPOSITORY.search(cell)
        if not match:
            fail(f"docs/source-map.md: source row {cell!r} must link its GitHub repository")
        repository = match.group(1).lower()
        if repository in rows:
            fail(f"docs/source-map.md: duplicate source row for {repository}")
        rows[repository] = cell
    return rows


def check_upstreams() -> int:
    lock = load_json(ROOT / "upstreams.lock.json")
    if lock.get("review_cadence") != "weekly":
        fail("upstream cadence must be weekly")
    sources = lock.get("sources")
    if not isinstance(sources, list) or not sources or not all(isinstance(source, dict) for source in sources):
        fail("upstream lock must contain a nonempty list of source objects")
    ids = [source.get("id") for source in sources]
    if any(not isinstance(source_id, str) or not source_id for source_id in ids):
        fail("upstream ids must be nonempty strings")
    if len(ids) != len(set(ids)):
        fail("upstream ids must be unique")
    repositories: dict[str, str] = {}
    for source in sources:
        source_id = source["id"]
        if not SHA.fullmatch(source.get("reviewed_sha", "")):
            fail(f"{source_id}: invalid reviewed SHA")
        paths = source.get("monitored_paths")
        if not isinstance(paths, list) or not paths or not all(isinstance(path, str) and path for path in paths):
            fail(f"{source_id}: monitored paths are required")
        repository = source.get("repository")
        if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            fail(f"{source_id}: repository must be owner/name")
        if source.get("url") not in {f"https://github.com/{repository}", f"https://github.com/{repository}.git"}:
            fail(f"{source_id}: expected GitHub HTTPS URL for {repository}")
        if repository.lower() in repositories:
            fail(f"{source_id}: repository {repository} is already tracked by {repositories[repository.lower()]}")
        repositories[repository.lower()] = source_id
    rows = source_map_repositories()
    for repository, source_id in repositories.items():
        if repository not in rows:
            fail(f"docs/source-map.md: missing source row for {source_id} ({repository})")
    for repository, cell in rows.items():
        if repository not in repositories:
            fail(f"docs/source-map.md: source row {cell!r} has no entry in upstreams.lock.json")
    return len(sources)


def check_content() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or IGNORED_CONTENT_PARTS.intersection(path.parts):
            continue
        if path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"} and path.name not in {"LICENSE", "NOTICE"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "[" + "TODO:" in text or "<" + "placeholder>" in text:
            fail(f"{path.relative_to(ROOT)}: editorial placeholder remains")
        if path.suffix in {".md", ".yaml", ".yml", ".py"} and "\t" in text:
            fail(f"{path.relative_to(ROOT)}: tab character found")
        if "tests" not in path.parts:
            for pattern in FORBIDDEN_WRITING_RESTRICTIONS:
                if pattern.search(text):
                    fail(f"{path.relative_to(ROOT)}: unapproved writing-evaluation restriction remains")
    workflow = (ROOT / ".github" / "workflows" / "upstream-review.yml").read_text(encoding="utf-8")
    if not re.search(r'cron: "\d+ \d+ \* \* [0-6]"', workflow):
        fail("upstream workflow must run on a weekly schedule")


def main() -> int:
    metadata = check_manifests()
    check_release_references(metadata)
    check_skill()
    check_super_tighten()
    check_no_hooks()
    source_count = check_upstreams()
    check_content()
    print(
        "PASS: dual manifests, release version references, forced Claude output style, hook-free packaging, "
        "canonical skill, short alias, focused command, standalone Super Tighten, "
        f"{len(REQUIRED_REFERENCES)} references, {len(REQUIRED_SCRIPTS)} helpers with shared Markdown recognition, "
        f"{source_count} source pins with source-map rows, links, metadata, and cadence verified"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
