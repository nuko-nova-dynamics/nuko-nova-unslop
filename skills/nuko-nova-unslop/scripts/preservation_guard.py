#!/usr/bin/env python3
"""Compare protected surface tokens between a source and rewrite.

The result is a conservative review queue, not semantic proof. Exit status 1
means protected tokens differ; exit status 0 means no surface difference was
found.
"""

from __future__ import annotations

import argparse
import bisect
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from markdown_source import fenced_code_spans, markdown_table_spans, mask_spans


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


def compare_markdown_tables(source: str, rewrite: str) -> dict[str, dict[str, int]] | None:
    """Report Markdown table drift without printing protected table contents."""
    before = [table for _, _, table in markdown_table_spans(source)]
    after = [table for _, _, table in markdown_table_spans(rewrite)]
    if before == after:
        return None

    missing_count = sum((Counter(before) - Counter(after)).values())
    added_count = sum((Counter(after) - Counter(before)).values())
    return {
        "missing": {"original table": missing_count} if missing_count else {},
        "added": {"rewrite table": added_count} if added_count else {},
    }


def line_offsets(text: str) -> list[int]:
    """Return character offsets for the start of each line and the end of text."""
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def table_line_intervals(text: str) -> list[tuple[int, int]]:
    """Return zero-based line intervals for recognized Markdown tables."""
    offsets = line_offsets(text)
    intervals: list[tuple[int, int]] = []
    for start, end, _ in markdown_table_spans(text):
        start_line = max(0, bisect.bisect_right(offsets, start) - 1)
        end_line = bisect.bisect_left(offsets, end)
        intervals.append((start_line, end_line))
    return intervals


def mapped_table_spans(source: str, target: str) -> list[tuple[int, int]]:
    """Map recognized source-table lines onto their corresponding target regions."""
    source_lines = source.splitlines(keepends=True)
    target_lines = target.splitlines(keepends=True)
    source_intervals = table_line_intervals(source)
    target_offsets = line_offsets(target)
    spans: list[tuple[int, int]] = []

    matcher = difflib.SequenceMatcher(None, source_lines, target_lines, autojunk=False)
    for tag, source_start, source_end, target_start, target_end in matcher.get_opcodes():
        for table_start, table_end in source_intervals:
            overlap_start = max(source_start, table_start)
            overlap_end = min(source_end, table_end)
            if tag == "equal" and overlap_start < overlap_end:
                mapped_start = target_start + overlap_start - source_start
                mapped_end = target_start + overlap_end - source_start
                spans.append((target_offsets[mapped_start], target_offsets[mapped_end]))
            elif tag != "equal" and overlap_start < overlap_end:
                spans.append((target_offsets[target_start], target_offsets[target_end]))
            elif tag == "insert" and table_start <= source_start <= table_end:
                spans.append((target_offsets[target_start], target_offsets[target_end]))
    return spans


def mask_protected_blocks(
    text: str, additional_spans: list[tuple[int, int]] | None = None
) -> str:
    """Hide fenced code and Markdown tables while retaining line structure."""
    spans = fenced_code_spans(text)
    spans.extend((start, end) for start, end, _ in markdown_table_spans(text))
    spans.extend(additional_spans or [])
    return mask_spans(text, spans)


def compare_fenced_code(source: str, rewrite: str) -> dict[str, dict[str, int]] | None:
    """Report exact fenced-code drift without printing protected code."""
    before = [source[start:end] for start, end in fenced_code_spans(source)]
    after = [rewrite[start:end] for start, end in fenced_code_spans(rewrite)]
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
    markdown_table = compare_markdown_tables(source, rewrite)
    source_transition_spans = mapped_table_spans(rewrite, source) if markdown_table else []
    rewrite_transition_spans = mapped_table_spans(source, rewrite) if markdown_table else []
    before = extract(mask_protected_blocks(source, source_transition_spans))
    after = extract(mask_protected_blocks(rewrite, rewrite_transition_spans))
    result: dict[str, dict[str, dict[str, int]]] = {}
    fenced_code = compare_fenced_code(source, rewrite)
    if fenced_code:
        result["fenced_code"] = fenced_code
    if markdown_table:
        result["markdown_table"] = markdown_table
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
