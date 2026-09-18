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


CanonicalTable = tuple[tuple[str, ...], ...]
ContainerView = tuple[str, ContainerPath]

ATX_HEADING_RE = re.compile(r"^#{1,6}(?:[ \t]+|$)")
THEMATIC_BREAK_RE = re.compile(
    r"^(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,})$"
)
RAW_HTML_BLOCK_RE = re.compile(
    r"^</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|"
    r"colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|"
    r"form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|"
    r"menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
    r"table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[ \t]+|/?>|$)",
    re.IGNORECASE,
)
RAW_HTML_CLOSED_RE = re.compile(
    r"^<(script|pre|style|textarea)(?:[ \t]+|>|$)", re.IGNORECASE
)


def strip_table_indentation(line: str) -> str | None:
    """Strip up to three Markdown columns and reject indented code."""
    column = 0
    index = 0
    while index < len(line) and line[index] in " \t":
        column = advance_columns(line[index], column)
        if column >= 4:
            return None
        index += 1
    return line[index:]


def split_table_cells(line: str) -> tuple[str, ...] | None:
    """Split a pipe row without treating escaped pipes as separators."""
    content = strip_table_indentation(line)
    if content is None:
        return None
    content = content.strip()
    if not content:
        return None

    separators: list[int] = []
    for index, character in enumerate(content):
        if character != "|":
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= 0 and content[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            separators.append(index)

    if not separators:
        return None

    parts: list[str] = []
    start = 0
    for separator in separators:
        parts.append(content[start:separator])
        start = separator + 1
    parts.append(content[start:])

    has_leading_pipe = separators[0] == 0
    has_trailing_pipe = separators[-1] == len(content) - 1
    if has_leading_pipe:
        parts = parts[1:]
    if has_trailing_pipe:
        parts = parts[:-1]
    if not parts or (len(parts) == 1 and not (has_leading_pipe and has_trailing_pipe)):
        return None
    return tuple(part.strip() for part in parts)


def split_table_row(line: str) -> tuple[str, ...] | None:
    """Split a possible top-level Markdown table row."""
    return split_table_cells(line)


def delimiter_alignment(cell: str) -> str | None:
    """Return a stable alignment label for one Markdown table delimiter cell."""
    if not re.fullmatch(r":?-+:?", cell):
        return None
    return (
        ("left" if cell.startswith(":") else "")
        + ("-right" if cell.endswith(":") else "")
        or "none"
    )


def html_comment_spans(text: str, excluded: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return Markdown HTML comment spans outside already protected blocks."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = text.find("<!--", cursor)
        if start < 0:
            break
        containing_end = next(
            (end for excluded_start, end in excluded if excluded_start <= start < end),
            None,
        )
        if containing_end is not None:
            cursor = containing_end
            continue
        closing = text.find("-->", start + 4)
        end = len(text) if closing < 0 else closing + 3
        spans.append((start, end))
        cursor = end
    return spans


def raw_html_block_spans(text: str, excluded: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return common raw HTML block spans, which end at the next blank line."""
    spans: list[tuple[int, int]] = []
    lines = text.splitlines(keepends=True)
    offset = 0
    opening: tuple[int, str | None] | None = None
    for line in lines:
        line_start = offset
        offset += len(line)
        physical = line.rstrip("\r\n")
        if opening is not None:
            start, closing_tag = opening
            if closing_tag is not None and re.search(
                rf"</{re.escape(closing_tag)}[ \t]*>", physical, re.IGNORECASE
            ):
                spans.append((start, offset))
                opening = None
            elif closing_tag is None and not physical.strip():
                spans.append((start, line_start))
                opening = None
            continue
        if any(start <= line_start < end for start, end in excluded):
            continue
        content, _, _ = peel_direct_containers(physical)
        content = strip_table_indentation(content)
        if content is None:
            continue
        closed_match = RAW_HTML_CLOSED_RE.match(content)
        if closed_match:
            closing_tag = closed_match.group(1).lower()
            if re.search(
                rf"</{re.escape(closing_tag)}[ \t]*>", content, re.IGNORECASE
            ):
                spans.append((line_start, offset))
            else:
                opening = (line_start, closing_tag)
        elif RAW_HTML_BLOCK_RE.match(content):
            opening = (line_start, None)
    if opening is not None:
        spans.append((opening[0], len(text)))
    return spans


def protected_source_spans(text: str) -> list[tuple[int, int]]:
    """Return source-only blocks that must not be parsed as Markdown tables."""
    fenced = fenced_code_spans(text)
    comments = html_comment_spans(text, fenced)
    html_blocks = raw_html_block_spans(text, [*fenced, *comments])
    return [*fenced, *comments, *html_blocks]


def markdown_container_views(text: str) -> list[ContainerView | None]:
    """Strip established quote and list containers from each unprotected line."""
    protected = protected_source_spans(text)
    active_list_paths: list[ContainerPath] = []
    views: list[ContainerView | None] = []
    offset = 0

    for line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(line)
        physical = line.rstrip("\r\n")
        if any(start <= line_start < end for start, end in protected):
            views.append(None)
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
                views.append(("", active_list_paths[-1]))
                continue
            active_list_paths = []
            content, container_path, new_list_paths = peel_direct_containers(physical)

        active_list_paths.extend(new_list_paths)
        views.append((content, container_path))

    return views


def starts_block_structure(content: str) -> bool:
    """Return whether a line starts a block that terminates a GFM table."""
    stripped = strip_table_indentation(content)
    if stripped is None:
        return True
    stripped = stripped.strip()
    return bool(
        not stripped
        or fence_match(stripped)
        or ATX_HEADING_RE.match(stripped)
        or THEMATIC_BREAK_RE.fullmatch(stripped)
    )


def markdown_table_spans(text: str) -> list[tuple[int, int, CanonicalTable]]:
    """Return recognized Markdown table spans and whitespace-normalized cell content."""
    lines = text.splitlines(keepends=True)
    starts: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)

    views = markdown_container_views(text)

    spans: list[tuple[int, int, CanonicalTable]] = []
    index = 0
    while index + 1 < len(lines):
        header_view = views[index]
        delimiter_view = views[index + 1]
        if header_view is None or delimiter_view is None:
            index += 1
            continue

        header_content, container_path = header_view
        delimiter_content, delimiter_path = delimiter_view
        if delimiter_path != container_path:
            index += 1
            continue

        header = split_table_cells(header_content)
        delimiter = split_table_cells(delimiter_content)
        alignments = tuple(
            delimiter_alignment(cell) for cell in delimiter
        ) if delimiter is not None else ()
        if (
            header is None
            or delimiter is None
            or len(header) != len(delimiter)
            or not alignments
            or any(alignment is None for alignment in alignments)
        ):
            index += 1
            continue

        canonical_rows: list[tuple[str, ...]] = [
            header,
            tuple(f"alignment:{alignment}" for alignment in alignments if alignment is not None),
        ]
        end_index = index + 2
        while end_index < len(lines):
            view = views[end_index]
            if view is None:
                break
            content, body_path = view
            if body_path != container_path or starts_block_structure(content):
                break
            row = split_table_cells(content)
            if row is None:
                plain = strip_table_indentation(content)
                if plain is None:
                    break
                row = (plain.strip(),)
            normalized = tuple((*row, *([""] * max(0, len(header) - len(row)))))
            canonical_rows.append(normalized)
            end_index += 1

        end = starts[end_index] if end_index < len(lines) else len(text)
        spans.append((starts[index], end, tuple(canonical_rows)))
        index = end_index

    return spans


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
    characters = list(text)
    spans = fenced_code_spans(text)
    spans.extend((start, end) for start, end, _ in markdown_table_spans(text))
    spans.extend(additional_spans or [])
    for start, end in spans:
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
