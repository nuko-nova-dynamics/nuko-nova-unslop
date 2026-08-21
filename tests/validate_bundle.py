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
SKILL = ROOT / "skills" / "nuko-nova-unslop"
ALIAS_SKILL = ROOT / "skills" / "unslop"
OUTPUT_STYLE = ROOT / "output-styles" / "nuko-nova-unslop.md"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
SHA = re.compile(r"^[0-9a-f]{40}$")
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
REQUIRED_REFERENCES = {
    "editorial-contract.md",
    "evolution.md",
    "interaction-calibration.md",
    "pattern-catalog.md",
    "profiles-and-genres.md",
    "source-map.md",
}
REQUIRED_SCRIPTS = {"preservation_guard.py", "unslop_lint.py"}
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


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")


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


def check_manifests() -> None:
    codex = load_json(ROOT / ".codex-plugin" / "plugin.json")
    claude = load_json(ROOT / ".claude-plugin" / "plugin.json")
    for field in ("name", "version", "description", "author", "homepage", "repository", "license"):
        if codex.get(field) != claude.get(field):
            fail(f"client manifests disagree on {field}")
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


def check_skill() -> None:
    frontmatter = parse_frontmatter(SKILL / "SKILL.md")
    if set(frontmatter) != {"name", "description"}:
        fail("skill frontmatter must contain only name and description")
    if frontmatter["name"] != "nuko-nova-unslop":
        fail("skill name mismatch")
    if len(frontmatter["description"]) < 180 or "Use " not in frontmatter["description"]:
        fail("skill description must explain capability and triggers")
    if not frontmatter["description"].startswith("Always-on human-writing standard for every human-facing"):
        fail("skill description must trigger for every human-facing response")
    references = {path.name for path in (SKILL / "references").iterdir() if path.is_file()}
    scripts = {path.name for path in (SKILL / "scripts").iterdir() if path.is_file() and path.suffix == ".py"}
    if references != REQUIRED_REFERENCES:
        fail(f"reference set mismatch: {sorted(references)}")
    if scripts != REQUIRED_SCRIPTS:
        fail(f"script set mismatch: {sorted(scripts)}")
    agent = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "Use Unslop" not in agent:
        fail("OpenAI default prompt must name Unslop")
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
    style_body = OUTPUT_STYLE.read_text(encoding="utf-8")
    if "every human-facing response" not in style_body or "Never invent detail" not in style_body:
        fail("Claude output style is missing the default writing contract")
    if "Human does not mean" not in style_body or "fake intimacy" not in style_body:
        fail("Claude output style is missing the human-writing and no-cringe contract")
    skill_body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if "Treat delegated prose as unreviewed source material" not in skill_body:
        fail("skill must require parent review of delegated prose")
    if "Carry explicit writing corrections forward" not in skill_body:
        fail("skill must carry explicit writing corrections forward")
    if "Apply the no-cringe standard as a context test" not in skill_body:
        fail("skill must define the no-cringe context test")

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
    if not re.search(r"^\s*allow_implicit_invocation:\s*false\s*$", alias_agent, re.MULTILINE):
        fail("alias OpenAI invocation must remain explicit")

    for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
        check_links(path)
    check_links(ALIAS_SKILL / "SKILL.md")
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


def check_upstreams() -> None:
    lock = load_json(ROOT / "upstreams.lock.json")
    if lock.get("review_cadence") != "every-two-days":
        fail("upstream cadence must be every-two-days")
    sources = lock.get("sources")
    if not isinstance(sources, list) or len(sources) != 17:
        fail("upstream lock must contain the seventeen researched repositories")
    ids = [source.get("id") for source in sources]
    if len(ids) != len(set(ids)):
        fail("upstream ids must be unique")
    for source in sources:
        if not SHA.fullmatch(source.get("reviewed_sha", "")):
            fail(f"{source.get('id')}: invalid reviewed SHA")
        if not source.get("monitored_paths"):
            fail(f"{source.get('id')}: monitored paths are required")
        if not source.get("url", "").startswith("https://github.com/"):
            fail(f"{source.get('id')}: expected GitHub HTTPS URL")


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
    workflow = (ROOT / ".github" / "workflows" / "upstream-review.yml").read_text(encoding="utf-8")
    if "86400 % 2" not in workflow or "schedule:" not in workflow:
        fail("upstream workflow must enforce its every-two-days cadence")


def main() -> int:
    check_manifests()
    check_skill()
    check_no_hooks()
    check_upstreams()
    check_content()
    print("PASS: dual manifests, forced Claude output style, hook-free packaging, one canonical skill, one short alias, six references, two helpers, seventeen source pins, links, metadata, and cadence verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
