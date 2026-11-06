"""Recognize Markdown source structure without applying editorial policy.

Call ``source_structure(text)`` once per document. It returns every recognized
structure grouped by kind, with offsets into the original text. One precedence
order decides which structure wins; a later kind never opens inside an earlier
one:

1. fenced code
2. indented code
3. inline code outside block code
4. HTML comments that open outside any code
5. raw HTML blocks outside code and comments
6. tables outside fenced code, comments, and raw HTML blocks

Callers choose which kinds to hide or compare, and ``mask_spans`` hides spans
without shifting offsets or changing line endings. The scanners cover the
supported block-quote and list containers; they are not a full Markdown parser.
Both command-line helpers use this module so syntax fixes reach both callers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, NamedTuple


FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})([^\r\n]*)$")
# One backtick pair on one line. The guard also uses the group as a token.
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
LIST_MARKER_RE = re.compile(
    r"^(?P<indent>[ \t]{0,3})(?P<marker>[-+*]|\d{1,9}[.)])"
    r"(?:(?P<spacing>[ \t]+)(?P<content>.*))?$"
)


def _fence_match(line: str, column: int = 0) -> re.Match[str] | None:
    """Return a fence match after the line's container prefix is removed.

    The opener may be indented at most three columns, measured with tab stops
    from ``column``, the line's position after its container prefix.
    """
    match = FENCE_RE.match(line)
    if match is None or _indent_width(line, column) > 3:
        return None
    return match


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
) -> tuple[str, ContainerPath, tuple[ContainerPath, ...], int]:
    """Peel ordered quote and list markers and return the content column."""
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

    return remainder, tuple(path), tuple(list_paths), column


Span = tuple[int, int]
LineView = tuple[str, ContainerPath, int]


class _ContainerWalker:
    """Track open list containers across lines and strip established prefixes."""

    def __init__(self) -> None:
        self._list_paths: list[ContainerPath] = []

    def view(self, physical: str) -> LineView:
        """Return a line's content, container path, and content start column."""
        for index in range(len(self._list_paths) - 1, -1, -1):
            stripped = _strip_container_path(physical, self._list_paths[index])
            if stripped is None:
                continue
            active_path = self._list_paths[index]
            self._list_paths = self._list_paths[: index + 1]
            content, path, new_list_paths, column = _peel_direct_containers(
                stripped[0], active_path, stripped[1]
            )
            self._list_paths.extend(new_list_paths)
            return content, path, column

        if self._list_paths and not physical.strip():
            return "", self._list_paths[-1], 0
        content, path, new_list_paths, column = _peel_direct_containers(physical)
        self._list_paths = list(new_list_paths)
        return content, path, column


def _indent_width(content: str, column: int) -> int:
    """Return the indentation width of container content in Markdown columns."""
    leading = content[: len(content) - len(content.lstrip(" \t"))]
    return _advance_columns(leading, column) - column


def _code_block_spans(text: str) -> tuple[list[Span], list[Span]]:
    """Return fenced and indented code spans from one container-aware line walk.

    Indented code cannot interrupt a paragraph, so it needs a blank line or the
    start of the document before it. Every other non-blank line, including a
    fence closer or heading, counts as paragraph text here; that keeps prose
    visible when the scanner is unsure. Indentation is measured in columns
    after the line's quote and list containers are stripped.
    """
    fenced: list[Span] = []
    indented: list[Span] = []
    walker = _ContainerWalker()
    offset = 0
    fence: tuple[str, int, int, ContainerPath] | None = None
    code: tuple[int, int, ContainerPath] | None = None
    in_paragraph = False

    for line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(line)
        physical = line.rstrip("\r\n")

        if fence is not None:
            marker_char, marker_length, start, container_path = fence
            stripped = _strip_container_path(physical, container_path)
            if stripped is None:
                fenced.append((start, line_start))
                fence = None
                in_paragraph = False
            else:
                match = _fence_match(*stripped)
                if match:
                    marker = match.group(1)
                    suffix = match.group(2)
                    if (
                        marker[0] == marker_char
                        and len(marker) >= marker_length
                        and not suffix.strip(" \t")
                    ):
                        fenced.append((start, offset))
                        fence = None
                        in_paragraph = True
                continue

        content, container_path, column = walker.view(physical)
        blank = not content.strip()

        if code is not None:
            code_start, code_end, code_path = code
            if container_path == code_path and (
                blank or _indent_width(content, column) >= 4
            ):
                if not blank:
                    code = (code_start, offset, code_path)
                continue
            indented.append((code_start, code_end))
            code = None

        if blank:
            in_paragraph = False
            continue

        match = _fence_match(content, column)
        if match:
            marker = match.group(1)
            suffix = match.group(2)
            if not (marker[0] == "`" and "`" in suffix):
                fence = (marker[0], len(marker), line_start, container_path)
                continue

        if not in_paragraph and _indent_width(content, column) >= 4:
            code = (line_start, offset, container_path)
            continue
        in_paragraph = True

    if fence is not None:
        fenced.append((fence[2], len(text)))
    if code is not None:
        indented.append((code[0], code[1]))
    return fenced, indented


def _inline_code_spans(text: str, block_code: list[Span]) -> list[Span]:
    """Return one-line inline code spans that open outside block code."""
    return [
        match.span()
        for match in INLINE_CODE_RE.finditer(text)
        if not any(start <= match.start() < end for start, end in block_code)
    ]


CanonicalTable = tuple[tuple[str, ...], ...]
ContainerView = tuple[str, ContainerPath]


class TableSpan(NamedTuple):
    """A recognized table: its source span and whitespace-normalized rows."""

    start: int
    end: int
    cells: CanonicalTable

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


def _html_comment_spans(text: str, excluded: list[Span]) -> list[Span]:
    """Return HTML comment spans whose opener lies outside excluded spans."""
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


def _raw_html_block_spans(text: str, excluded: list[Span]) -> list[Span]:
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
        content = _strip_table_indentation(_peel_direct_containers(physical)[0])
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


def _markdown_container_views(
    text: str, protected: list[Span]
) -> list[ContainerView | None]:
    """Strip established quote and list containers from each unprotected line."""
    walker = _ContainerWalker()
    views: list[ContainerView | None] = []
    offset = 0

    for line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(line)
        if any(start <= line_start < end for start, end in protected):
            views.append(None)
            continue
        content, container_path, _ = walker.view(line.rstrip("\r\n"))
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


def _markdown_table_spans(text: str, protected: list[Span]) -> list[TableSpan]:
    """Return Markdown tables outside protected lines, with normalized cells."""
    lines = text.splitlines(keepends=True)
    starts: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)

    views = _markdown_container_views(text, protected)

    spans: list[TableSpan] = []
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
        spans.append(TableSpan(starts[index], end, tuple(canonical_rows)))
        index = end_index

    return spans


@dataclass(frozen=True)
class SourceStructure:
    """Every recognized source structure in one text, grouped by kind.

    Spans are ``(start, end)`` offsets into the text that was scanned. Kinds
    can overlap only where the module precedence allows it: inline code may
    sit inside an HTML comment, and a comment that opens in prose ends at the
    first ``-->`` even when that closer lies inside later code.
    """

    fenced_code: tuple[Span, ...]
    indented_code: tuple[Span, ...]
    inline_code: tuple[Span, ...]
    html_comments: tuple[Span, ...]
    html_blocks: tuple[Span, ...]
    tables: tuple[TableSpan, ...]


def source_structure(text: str) -> SourceStructure:
    """Recognize every supported structure in ``text`` with one precedence order."""
    fenced, indented = _code_block_spans(text)
    block_code = [*fenced, *indented]
    inline = _inline_code_spans(text, block_code)
    comments = _html_comment_spans(text, [*block_code, *inline])
    html_blocks = _raw_html_block_spans(text, [*block_code, *comments])
    tables = _markdown_table_spans(text, [*fenced, *comments, *html_blocks])
    return SourceStructure(
        fenced_code=tuple(fenced),
        indented_code=tuple(indented),
        inline_code=tuple(inline),
        html_comments=tuple(comments),
        html_blocks=tuple(html_blocks),
        tables=tuple(tables),
    )


def mask_spans(text: str, spans: Iterable[Span]) -> str:
    """Hide selected spans without shifting offsets or changing line endings."""
    characters = list(text)
    for start, end in spans:
        for index in range(start, end):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)
