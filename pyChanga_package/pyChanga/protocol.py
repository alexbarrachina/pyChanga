"""Translate client messages into engine calls.

Only this adapter and service.py know the external protocol version. Playback
code emits ordinary events; the service adds the wire envelope when sending them.
"""
from __future__ import annotations

from .errors import error_info
from .sections import parse_document

PROTOCOL_VERSION = 1


def handle_command(engine, request: dict) -> dict:
    """Return one response; runtime events use the engine's existing callback."""
    response = {"type": "response", "requestId": request.get("requestId")}
    try:
        if request.get("version") != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version; expected version {PROTOCOL_VERSION}")
        result = _dispatch(engine, request)
        return {**response, "ok": True, "result": result}
    except Exception as error:
        return {
            **response,
            "ok": False,
            "error": error_info(error, request.get("filename", "untitled.py")),
        }


def _dispatch(engine, request: dict) -> dict:
    kind = request.get("type")
    if kind == "run":
        return engine.run(request)
    if kind == "run_callable":
        return engine.run_callable(request)
    if kind == "note":
        return engine.direct_note(request)
    if kind == "wait":
        return engine.direct_wait(request["beats"])
    if kind == "launch_mode":
        return engine.set_launch_mode(request["mode"])
    if kind == "stop":
        engine.stop(request["partId"])
        return {}
    if kind == "stop_all":
        engine.stop_all()
        return {}
    if kind == "tempo":
        return engine.set_tempo(request["bpm"])
    if kind == "direct_tempo":
        return engine.set_tempo(request["bpm"], engine.live_cursor)
    if kind == "parse":
        document = parse_document(request["source"])
        return {
            "parts": [
                {
                    "name": section.name,
                    "line": section.start_line,
                    "markerLine": section.marker_line,
                    "endLine": section.end_line,
                    "kind": "all" if section.name == "all" else "part",
                }
                for section in document.sections
            ]
        }
    if kind == "status":
        return engine.snapshot()
    if kind == "shutdown":
        engine.close()
        return {}
    raise ValueError(f"Unknown command: {kind}")
