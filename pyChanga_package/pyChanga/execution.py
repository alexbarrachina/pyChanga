"""Prepare source for playback without starting workers or opening audio.

The CLI and editor share these document rules. The engine receives a complete
launch plan, so a syntax error cannot interrupt an already playing part.
"""
from __future__ import annotations

from dataclasses import dataclass

from .sections import execution, parse_document


@dataclass(frozen=True)
class PartSource:
    name: str
    line: int
    body: str


@dataclass(frozen=True)
class LaunchPlan:
    source: str
    filename: str
    document_id: str
    setup: str
    parts: tuple[PartSource, ...]
    reserved_names: frozenset[str]
    quantum: float
    grouped: bool
    request_id: str | None = None


def prepare_run(request: dict, *, all_parts: bool = False) -> LaunchPlan:
    """Validate and compile every selected part before changing playback."""
    source = request["source"]
    if not isinstance(source, str) or len(source.encode("utf-8")) > 1_000_000:
        raise ValueError("A document must contain at most 1 MB of Python source")
    filename = request.get("filename") or "untitled.py"

    if all_parts:
        document = parse_document(source)
    else:
        document, section, body = execution(
            source, filename, request.get("selection"), request.get("name")
        )
        all_parts = section.name == "all"

    if all_parts:
        compile(document.setup, filename, "exec")
        parts = []
        for section in document.parts:
            body = "\n" * (section.start_line - 1) + section.source
            compile(body, filename, "exec")
            parts.append(PartSource(section.name, section.start_line, body))
    else:
        parts = [PartSource(section.name, section.start_line, body)]

    # A bar currently contains four beats. This is a musical rule, not a UI rule.
    quantum = {"immediate": 0, "beat": 1, "bar": 4}.get(request.get("quantization", "beat"))
    if quantum is None:
        raise ValueError("Launch timing must be immediate, beat or bar")

    return LaunchPlan(
        source=source,
        filename=filename,
        document_id=str(request.get("documentId", filename)),
        setup=document.setup,
        parts=tuple(parts),
        reserved_names=frozenset(section.name for section in document.sections),
        quantum=quantum,
        grouped=all_parts,
        request_id=request.get("requestId"),
    )
