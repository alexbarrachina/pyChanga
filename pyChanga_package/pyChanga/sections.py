"""Canonical parser for the editor and command-line runner."""
from __future__ import annotations
from dataclasses import dataclass
import io
import re
import textwrap
import tokenize

MARKER = re.compile(r"^#\s*%%\s*(.*?)\s*$")


@dataclass(frozen=True)
class Section:
    name: str
    marker_line: int
    start_line: int
    end_line: int
    source: str


@dataclass(frozen=True)
class Document:
    setup: str
    parts: tuple[Section, ...]


def parse_document(source: str) -> Document:
    lines = source.splitlines(keepends=True)
    markers = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT and token.start[1] == 0:
                match = MARKER.match(token.string)
                if match:
                    markers.append((token.start[0], match.group(1)))
    except (tokenize.TokenError, IndentationError):
        pass  # compile() reports syntax errors without mistaking strings for sections.
    if not markers:
        return Document("", (Section("main", 1, 1, max(1, len(lines)), source),))
    names, parts = set(), []
    setup_lines = lines[:markers[0][0] - 1]
    for index, (line, name) in enumerate(markers):
        if not name:
            raise ValueError(f"Line {line}: name the section, for example # %% melody")
        if name in names:
            raise ValueError(f"Line {line}: duplicate section name '{name}'")
        names.add(name)
        end = markers[index + 1][0] - 1 if index + 1 < len(markers) else len(lines)
        body = "".join(lines[line:end])
        if name == "setup":
            if index != 0:
                raise ValueError("The setup section must come before musical parts")
            setup_lines.extend(["\n", *lines[line:end]])
        else:
            parts.append(Section(name, line, line + 1, end, body))
    if not parts:
        raise ValueError("Add a musical part after setup, for example # %% melody")
    return Document("".join(setup_lines), tuple(parts))


def execution(source: str, filename: str, selection: dict | None = None, name: str | None = None):
    document = parse_document(source)
    selection = selection or {"startLine": document.parts[0].start_line, "startColumn": 1,
                              "endLine": document.parts[0].start_line, "endColumn": 1}
    start, end = int(selection["startLine"]), int(selection["endLine"])
    sc, ec = int(selection.get("startColumn", 1)), int(selection.get("endColumn", 1))
    lines = source.splitlines(keepends=True) or [""]
    if min(start, end, sc, ec) < 1 or start > len(lines) + 1 or end > len(lines) + 1 or (end, ec) < (start, sc):
        raise ValueError("Invalid source selection")
    selected = (start, sc) != (end, ec)
    effective_end = end - 1 if selected and ec == 1 and end > start else end
    part = next((p for p in document.parts if p.name == name), None) if name is not None else next(
        (p for p in document.parts if p.marker_line <= start <= max(p.end_line, p.start_line)), None)
    if part is None:
        raise ValueError("Place the cursor in a musical part. Setup is replayed when you run a part.")
    if selected:
        if start < part.marker_line or effective_end > part.end_line:
            raise ValueError("Select code within one musical section")
        chunks = lines[start - 1:end]
        if start == end:
            body = chunks[0][sc - 1:ec - 1]
        else:
            chunks[0] = chunks[0][sc - 1:]
            if end <= len(lines):
                chunks[-1] = chunks[-1][:ec - 1]
            body = "".join(chunks)
        body = "\n" * (start - 1) + textwrap.dedent(body)
    else:
        body = "\n" * (part.start_line - 1) + part.source
    compile(document.setup, filename, "exec")
    compile(body, filename, "exec")
    return document, part, body
