"""Recognize Markdown source structure without applying editorial policy.

Spans use offsets into the original text. Scanners cover the supported fenced
code, container, comment, and table forms; they are not a full Markdown parser.
Both command-line helpers use this module so syntax fixes reach both callers.
"""

from __future__ import annotations

import re
from typing import Iterable


FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})([^\r\n]*)$")
LIST_MARKER_RE = re.compile(
    r"^(?P<indent>[ \t]{0,3})(?P<marker>[-+*]|\d{1,9}[.)])"
    r"(?:(?P<spacing>[ \t]+)(?P<content>.*))?$"
)


def _fence_match(line: str) -> re.Match[str] | None:
    """Return a fence match after the line's container prefix is removed."""
    return FENCE_RE.match(line)


ContainerPath = tuple[tuple[str, int, int], ...]


def _advance_columns(text: str, start: int = 0) -> int:
    """Advance a Markdown column counter with four-column tab stops."""
    column = start
    for character in text:
        if character == "\t":
            column += 4 - (column % 4)
        else:
            column += 1
    return column


def _consume_indentation(text: str, target: int, start: int) -> tuple[str, int] | None:
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


def _block_quote_prefix_options(
    text: str, start: int, max_indent: int | None = 3
) -> tuple[tuple[str, int], ...]:
    """Return valid block-quote prefix interpretations with tab overhang."""
    column = start
    index = 0
    while index < len(text) and text[index] in " \t":
        next_column = _advance_columns(text[index], column)
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
        tab_end = _advance_columns("\t", column)
        consumed_column = column + 1
        overhang = tab_end - consumed_column
        options.append(((" " * overhang) + text[index + 1 :], consumed_column))
    options.append((text[index:], column))
    return tuple(dict.fromkeys(options))


def _strip_container_path(line: str, path: ContainerPath) -> tuple[str, int] | None:
    """Strip one established sequence of Markdown container prefixes."""
    def strip_step(index: int, remainder: str, column: int) -> tuple[str, int] | None:
        if index == len(path):
            return remainder, column

        kind, relative_width, absolute_target = path[index]
        if kind == "quote":
            for consumed in _block_quote_prefix_options(remainder, column, max_indent=None):
                stripped = strip_step(index + 1, *consumed)
                if stripped is not None:
                    return stripped
            return None

        targets = (column + relative_width, absolute_target)
        for target in dict.fromkeys(targets):
            consumed = _consume_indentation(remainder, target, column)
            if consumed is None:
                continue
            stripped = strip_step(index + 1, *consumed)
            if stripped is not None:
                return stripped
        return None

    return strip_step(0, line, 0)


def _peel_direct_containers(
    line: str, initial_path: ContainerPath = (), initial_column: int = 0
) -> tuple[str, ContainerPath, tuple[ContainerPath, ...]]:
    """Peel ordered quote and list markers before a possible fence."""
    remainder = line
    path = list(initial_path)
    list_paths: list[ContainerPath] = []
    column = initial_column

    while True:
        quote_options = _block_quote_prefix_options(remainder, column)
        if quote_options:
            path.append(("quote", 0, 0))
            remainder, column = quote_options[0]
            continue

        list_match = LIST_MARKER_RE.match(remainder)
        if not list_match:
            break
        spacing = list_match.group("spacing")
        indent = list_match.group("indent")
        indent_end = _advance_columns(indent, column)
        if indent_end - column > 3:
            break
        list_prefix = (
            indent
            + list_match.group("marker")
            + (spacing if spacing is not None else " ")
        )
        list_end = _advance_columns(list_prefix, column)
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
            stripped = _strip_container_path(physical, container_path)
            if stripped is None:
                spans.append((start, line_start))
                opening = None
            else:
                content, _ = stripped
                match = _fence_match(content)
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
            stripped = _strip_container_path(physical, candidate)
            if stripped is not None:
                candidate_content, candidate_column = stripped
                active_match = (index, candidate, candidate_content, candidate_column)
                break

        if active_match is not None:
            index, active_path, active_content, active_column = active_match
            active_list_paths = active_list_paths[: index + 1]
            content, container_path, new_list_paths = _peel_direct_containers(
                active_content, active_path, active_column
            )
        else:
            if active_list_paths and not physical.strip():
                continue
            active_list_paths = []
            content, container_path, new_list_paths = _peel_direct_containers(physical)

        active_list_paths.extend(new_list_paths)

        match = _fence_match(content)
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


def _strip_table_indentation(line: str) -> str | None:
    """Strip up to three Markdown columns and reject indented code."""
    column = 0
    index = 0
    while index < len(line) and line[index] in " \t":
        column = _advance_columns(line[index], column)
        if column >= 4:
            return None
        index += 1
    return line[index:]


def _split_table_cells(line: str) -> tuple[str, ...] | None:
    """Split a pipe row without treating escaped pipes as separators."""
    content = _strip_table_indentation(line)
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


def _delimiter_alignment(cell: str) -> str | None:
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


def _raw_html_block_spans(text: str, excluded: list[tuple[int, int]]) -> list[tuple[int, int]]:
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
        content, _, _ = _peel_direct_containers(physical)
        content = _strip_table_indentation(content)
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


def _protected_source_spans(text: str) -> list[tuple[int, int]]:
    """Return source-only blocks that must not be parsed as Markdown tables."""
    fenced = fenced_code_spans(text)
    comments = html_comment_spans(text, fenced)
    html_blocks = _raw_html_block_spans(text, [*fenced, *comments])
    return [*fenced, *comments, *html_blocks]


def _markdown_container_views(text: str) -> list[ContainerView | None]:
    """Strip established quote and list containers from each unprotected line."""
    protected = _protected_source_spans(text)
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
            stripped = _strip_container_path(physical, candidate)
            if stripped is not None:
                candidate_content, candidate_column = stripped
                active_match = (index, candidate, candidate_content, candidate_column)
                break

        if active_match is not None:
            index, active_path, active_content, active_column = active_match
            active_list_paths = active_list_paths[: index + 1]
            content, container_path, new_list_paths = _peel_direct_containers(
                active_content, active_path, active_column
            )
        else:
            if active_list_paths and not physical.strip():
                views.append(("", active_list_paths[-1]))
                continue
            active_list_paths = []
            content, container_path, new_list_paths = _peel_direct_containers(physical)

        active_list_paths.extend(new_list_paths)
        views.append((content, container_path))

    return views


def _starts_block_structure(content: str) -> bool:
    """Return whether a line starts a block that terminates a GFM table."""
    stripped = _strip_table_indentation(content)
    if stripped is None:
        return True
    stripped = stripped.strip()
    return bool(
        not stripped
        or _fence_match(stripped)
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

    views = _markdown_container_views(text)

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

        header = _split_table_cells(header_content)
        delimiter = _split_table_cells(delimiter_content)
        alignments = tuple(
            _delimiter_alignment(cell) for cell in delimiter
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
            if body_path != container_path or _starts_block_structure(content):
                break
            row = _split_table_cells(content)
            if row is None:
                plain = _strip_table_indentation(content)
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


def mask_spans(text: str, spans: Iterable[tuple[int, int]]) -> str:
    """Hide selected spans without shifting offsets or changing line endings."""
    characters = list(text)
    for start, end in spans:
        for index in range(start, end):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)
