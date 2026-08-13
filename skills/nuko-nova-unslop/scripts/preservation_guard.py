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
    "quote": re.compile(r"(?:\"([^\"\n]{3,})\"|“([^”\n]{3,})”)"),
    "markdown_target": re.compile(r"\[[^\]]*\]\(([^)]+)\)"),
}


def normalize(kind: str, match: re.Match[str]) -> str:
    if kind in {"inline_code", "markdown_target"}:
        return match.group(1).strip()
    if kind == "quote":
        return next(group for group in match.groups() if group is not None).strip()
    return match.group(0).rstrip(".,;:")


def extract(text: str) -> dict[str, Counter[str]]:
    return {
        kind: Counter(normalize(kind, match) for match in pattern.finditer(text))
        for kind, pattern in PATTERNS.items()
    }


def compare(source: str, rewrite: str) -> dict[str, dict[str, dict[str, int]]]:
    before = extract(source)
    after = extract(rewrite)
    result: dict[str, dict[str, dict[str, int]]] = {}
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
