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
    launcher: Section | None = None

    @property
    def sections(self) -> tuple[Section, ...]:
        sections = self.parts + ((self.launcher,) if self.launcher else ())
        return tuple(sorted(sections, key=lambda section: section.marker_line))


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
    launcher = None
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
            if parts:
                raise ValueError("The setup section must come before musical parts")
            setup_lines.extend(["\n"] * (line - len(setup_lines)) + lines[line:end])
        elif name == "all":
            if any(text.strip() and not text.lstrip().startswith('#') for text in body.splitlines()):
                raise ValueError("Keep # %% all empty or comment-only. Put code in setup or named musical parts.")
            launcher = Section(name, line, line, end, body)
        else:
            parts.append(Section(name, line, line + 1, end, body))
    if not parts:
        raise ValueError("Add a musical part after setup, for example # %% melody")
    return Document("".join(setup_lines), tuple(parts), launcher)


def execution(
    source: str,
    filename: str,
    selection: dict | None = None,
    name: str | None = None,
) -> tuple[Document, Section, str]:
    """Select and compile a section, preserving original traceback line numbers."""
    document = parse_document(source)
    selection = selection or {"startLine": document.parts[0].start_line, "startColumn": 1,
                              "endLine": document.parts[0].start_line, "endColumn": 1}
    start, end = int(selection["startLine"]), int(selection["endLine"])
    start_column = int(selection.get("startColumn", 1))
    end_column = int(selection.get("endColumn", 1))
    lines = source.splitlines(keepends=True) or [""]
    if (
        min(start, end, start_column, end_column) < 1
        or start > len(lines) + 1
        or end > len(lines) + 1
        or (end, end_column) < (start, start_column)
    ):
        raise ValueError("Invalid source selection")
    selected = (start, start_column) != (end, end_column)
    effective_end = end - 1 if selected and end_column == 1 and end > start else end
    if name is not None:
        part = next((part for part in document.sections if part.name == name), None)
    else:
        part = next((part for part in document.sections
                     if part.marker_line <= start <= max(part.end_line, part.start_line)), None)
    if part is None:
        raise ValueError("Place the cursor in a musical part. Setup is replayed when you run a part.")
    if selected:
        if start < part.marker_line or effective_end > part.end_line:
            raise ValueError("Select code within one musical section")
        chunks = lines[start - 1:end]
        if start == end:
            body = chunks[0][start_column - 1:end_column - 1]
        else:
            chunks[0] = chunks[0][start_column - 1:]
            if end <= len(lines):
                chunks[-1] = chunks[-1][:end_column - 1]
            body = "".join(chunks)
        body = "\n" * (start - 1) + textwrap.dedent(body)
    else:
        body = "\n" * (part.start_line - 1) + part.source
    compile(document.setup, filename, "exec")
    compile(body, filename, "exec")
    return document, part, body
