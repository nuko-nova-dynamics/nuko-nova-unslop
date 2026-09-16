#!/usr/bin/env python3
"""Compare protected surface tokens between a source and rewrite.

The result is a conservative review queue, not semantic proof. Exit status 1
means protected tokens differ; exit status 0 means no surface difference was
found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


PATTERNS = {
    "url": re.compile(r"https?://[^\s)>\]]+"),
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "inline_code": re.compile(r"`([^`\n]+)`"),
    "flag": re.compile(r"(?<!\w)--[a-zA-Z0-9][a-zA-Z0-9-]*"),
    "version": re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?\b"),
    "date": re.compile(
        r"\b(?:\d{4}-\d{2}-\d{2}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:,\s*\d{4})?|\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)(?:\s+\d{4})?)\b",
        re.IGNORECASE,
    ),
    "number": re.compile(r"(?<![\w.-])(?:[$€£])?\d+(?:[,.]\d+)*(?:\s?(?:%|ms|s|sec(?:onds?)?|minutes?|hours?|days?|weeks?|months?|years?|KB|MB|GB|TB|px|qt|lb|kg|mi))?(?![\w-])", re.IGNORECASE),
    "range": re.compile(r"(?<![\w.-])\d+(?:\.\d+)*\s?[–—-]\s?\d+(?:\.\d+)*(?![\w-])"),
    "claim_scope": re.compile(
        r"\b(?:only|both|first|last|most|least|simultaneously)\b|\bat[ \t]+once\b",
        re.IGNORECASE,
    ),
    "quote": re.compile(r"(?:\"([^\"\n]{3,})\"|“([^”\n]{3,})”)"),
    "markdown_target": re.compile(r"\[[^\]]*\]\(([^)]+)\)"),
}

FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})([^\r\n]*)$")
LIST_MARKER_RE = re.compile(
    r"^(?P<indent>[ \t]{0,3})(?P<marker>[-+*]|\d{1,9}[.)])"
    r"(?:(?P<spacing>[ \t]+)(?P<content>.*))?$"
)


def fence_match(line: str) -> re.Match[str] | None:
    """Return a fence match after the line's container prefix is removed."""
    return FENCE_RE.match(line)


ContainerPath = tuple[tuple[str, int, int], ...]


def advance_columns(text: str, start: int = 0) -> int:
    """Advance a Markdown column counter with four-column tab stops."""
    column = start
    for character in text:
        if character == "\t":
            column += 4 - (column % 4)
        else:
            column += 1
    return column


def consume_indentation(text: str, target: int, start: int) -> tuple[str, int] | None:
    """Consume indentation to an absolute column, retaining tab overhang."""
    column = start
    index = 0
    while index < len(text) and text[index] in " \t" and column < target:
        if text[index] == " ":
            column += 1
        else:
            column += 4 - (column % 4)
        index += 1
    if column < target:
        return ("", target) if not text.strip() else None
    return (" " * (column - target)) + text[index:], target


def block_quote_prefix_options(
    text: str, start: int, max_indent: int | None = 3
) -> tuple[tuple[str, int], ...]:
    """Return valid block-quote prefix interpretations with tab overhang."""
    column = start
    index = 0
    while index < len(text) and text[index] in " \t":
        next_column = advance_columns(text[index], column)
        if max_indent is not None and next_column - start > max_indent:
            return ()
        column = next_column
        index += 1
    if index >= len(text) or text[index] != ">":
        return ()

    column += 1
    index += 1
    options: list[tuple[str, int]] = []
    if index < len(text) and text[index] == " ":
        options.append((text[index + 1 :], column + 1))
    elif index < len(text) and text[index] == "\t":
        tab_end = advance_columns("\t", column)
        consumed_column = column + 1
        overhang = tab_end - consumed_column
        options.append(((" " * overhang) + text[index + 1 :], consumed_column))
    options.append((text[index:], column))
    return tuple(dict.fromkeys(options))


def strip_container_path(line: str, path: ContainerPath) -> tuple[str, int] | None:
    """Strip one established sequence of Markdown container prefixes."""
    def strip_step(index: int, remainder: str, column: int) -> tuple[str, int] | None:
        if index == len(path):
            return remainder, column

        kind, relative_width, absolute_target = path[index]
        if kind == "quote":
            for consumed in block_quote_prefix_options(remainder, column, max_indent=None):
                stripped = strip_step(index + 1, *consumed)
                if stripped is not None:
                    return stripped
            return None

        targets = (column + relative_width, absolute_target)
        for target in dict.fromkeys(targets):
            consumed = consume_indentation(remainder, target, column)
            if consumed is None:
                continue
            stripped = strip_step(index + 1, *consumed)
            if stripped is not None:
                return stripped
        return None

    return strip_step(0, line, 0)


def peel_direct_containers(
    line: str, initial_path: ContainerPath = (), initial_column: int = 0
) -> tuple[str, ContainerPath, tuple[ContainerPath, ...]]:
    """Peel ordered quote and list markers before a possible fence."""
    remainder = line
    path = list(initial_path)
    list_paths: list[ContainerPath] = []
    column = initial_column

    while True:
        quote_options = block_quote_prefix_options(remainder, column)
        if quote_options:
            path.append(("quote", 0, 0))
            remainder, column = quote_options[0]
            continue

        list_match = LIST_MARKER_RE.match(remainder)
        if not list_match:
            break
        spacing = list_match.group("spacing")
        indent = list_match.group("indent")
        indent_end = advance_columns(indent, column)
        if indent_end - column > 3:
            break
        list_prefix = (
            indent
            + list_match.group("marker")
            + (spacing if spacing is not None else " ")
        )
        list_end = advance_columns(list_prefix, column)
        list_width = list_end - column
        column = list_end
        path.append(("indent", list_width, list_end))
        list_paths.append(tuple(path))
        remainder = list_match.group("content") or ""

    return remainder, tuple(path), tuple(list_paths)


def fenced_code_spans(text: str) -> list[tuple[int, int]]:
    """Return normalized-text spans for Markdown fenced code blocks.

    This scanner handles top-level fences plus common block-quote and list-item
    containers. It stays deliberately smaller than a full Markdown parser.
    """
    spans: list[tuple[int, int]] = []
    lines = text.splitlines(keepends=True)
    offset = 0
    active_list_paths: list[ContainerPath] = []
    opening: tuple[str, int, int, ContainerPath] | None = None

    for line in lines:
        line_start = offset
        offset += len(line)
        physical = line.rstrip("\r\n")

        if opening is not None:
            marker_char, marker_length, start, container_path = opening
            stripped = strip_container_path(physical, container_path)
            if stripped is None:
                spans.append((start, line_start))
                opening = None
            else:
                content, _ = stripped
                match = fence_match(content)
                if match:
                    marker = match.group(1)
                    suffix = match.group(2)
                    if (
                        marker[0] == marker_char
                        and len(marker) >= marker_length
                        and not suffix.strip(" \t")
                    ):
                        spans.append((start, offset))
                        opening = None
                continue

        active_match: tuple[int, ContainerPath, str, int] | None = None
        for index in range(len(active_list_paths) - 1, -1, -1):
            candidate = active_list_paths[index]
            stripped = strip_container_path(physical, candidate)
            if stripped is not None:
                candidate_content, candidate_column = stripped
                active_match = (index, candidate, candidate_content, candidate_column)
                break

        if active_match is not None:
            index, active_path, active_content, active_column = active_match
            active_list_paths = active_list_paths[: index + 1]
            content, container_path, new_list_paths = peel_direct_containers(
                active_content, active_path, active_column
            )
        else:
            if active_list_paths and not physical.strip():
                continue
            active_list_paths = []
            content, container_path, new_list_paths = peel_direct_containers(physical)

        active_list_paths.extend(new_list_paths)

        match = fence_match(content)
        if not match:
            continue
        marker = match.group(1)
        suffix = match.group(2)
        if marker[0] == "`" and "`" in suffix:
            continue
        opening = (marker[0], len(marker), line_start, container_path)

    if opening is not None:
        spans.append((opening[2], len(text)))

    return spans


def fenced_code_blocks(text: str) -> list[str]:
    """Return complete Markdown fence spans with normalized line endings."""
    normalized = text.replace("\r\n", "\n")
    return [normalized[start:end] for start, end in fenced_code_spans(normalized)]


def mask_fenced_code(text: str) -> str:
    """Hide fenced code from token extractors while retaining line structure."""
    characters = list(text)
    for start, end in fenced_code_spans(text):
        for index in range(start, end):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)


def compare_fenced_code(source: str, rewrite: str) -> dict[str, dict[str, int]] | None:
    """Report exact fenced-code drift without printing protected code."""
    before = fenced_code_blocks(source)
    after = fenced_code_blocks(rewrite)
    if before == after:
        return None

    missing: dict[str, int] = {}
    added: dict[str, int] = {}
    for index in range(max(len(before), len(after))):
        label = f"block #{index + 1}"
        if index >= len(after):
            missing[label] = 1
        elif index >= len(before):
            added[label] = 1
        elif before[index] != after[index]:
            missing[f"{label} original"] = 1
            added[f"{label} rewrite"] = 1

    return {"missing": missing, "added": added}


def normalize(kind: str, match: re.Match[str]) -> str:
    if kind in {"inline_code", "markdown_target"}:
        return match.group(1).strip()
    if kind == "quote":
        return next(group for group in match.groups() if group is not None).strip()
    if kind == "claim_scope":
        return match.group(0).lower()
    return match.group(0).rstrip(".,;:")


def extract(text: str) -> dict[str, Counter[str]]:
    return {
        kind: Counter(normalize(kind, match) for match in pattern.finditer(text))
        for kind, pattern in PATTERNS.items()
    }


def compare(source: str, rewrite: str) -> dict[str, dict[str, dict[str, int]]]:
    source = source.replace("\r\n", "\n")
    rewrite = rewrite.replace("\r\n", "\n")
    before = extract(mask_fenced_code(source))
    after = extract(mask_fenced_code(rewrite))
    result: dict[str, dict[str, dict[str, int]]] = {}
    fenced_code = compare_fenced_code(source, rewrite)
    if fenced_code:
        result["fenced_code"] = fenced_code
    for kind in PATTERNS:
        missing = before[kind] - after[kind]
        added = after[kind] - before[kind]
        if missing or added:
            result[kind] = {"missing": dict(missing), "added": dict(added)}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare protected surface tokens in two UTF-8 files.")
    parser.add_argument("source")
    parser.add_argument("rewrite")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    source_path = Path(args.source)
    rewrite_path = Path(args.rewrite)
    differences = compare(
        source_path.read_text(encoding="utf-8"),
        rewrite_path.read_text(encoding="utf-8"),
    )
    if args.format == "json":
        print(json.dumps({"source": str(source_path), "rewrite": str(rewrite_path), "differences": differences}, indent=2, ensure_ascii=False))
    elif not differences:
        print("PASS: no protected surface-token differences found")
    else:
        print("REVIEW: protected surface tokens differ")
        for kind, changes in differences.items():
            if changes["missing"]:
                print(f"  {kind} missing: {changes['missing']}")
            if changes["added"]:
                print(f"  {kind} added: {changes['added']}")
        print("This check cannot detect semantic drift; compare meaning manually.")
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
