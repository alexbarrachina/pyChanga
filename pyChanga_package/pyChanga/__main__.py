"""Command-line runner and optional service entry point for pyChanga."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description="pyChanga — ordinary Python, one shared musical clock")
    parser.add_argument("file", nargs="?", type=Path)
    parser.add_argument("--service", action="store_true", help="Serve playback commands over standard input/output")
    parser.add_argument("--silent", action="store_true", help="Use the recording backend without opening audio")
    parser.add_argument("--part", help="Run this named section, or all for every part together")
    parser.add_argument("--quantization", choices=["immediate", "beat", "bar"], default="beat")
    args = parser.parse_args()
    if args.service:
        from .service import serve
        return serve(args.silent)
    if not args.file:
        parser.error("Supply a Python file, for example: python -m pyChanga lesson.py")
    from .audio import FluidSynthBackend, RecordingBackend
    from .engine import Engine
    from .sections import parse_document
    failed = False

    def emit(event):
        nonlocal failed
        if event["type"] == "output":
            print(event["text"], end="", file=sys.stderr if event["stream"] == "stderr" else sys.stdout, flush=True)
        elif event["type"] in ("error", "warning"):
            print(event.get("traceback", event["message"]), file=sys.stderr)
            failed |= event["type"] == "error"

    engine = None
    try:
        filename = args.file.resolve()
        source = filename.read_text(encoding="utf-8")
        document = parse_document(source)
        if args.part and args.part != "all" and args.part not in [p.name for p in document.parts]:
            raise ValueError(f"No section named {args.part!r}")
        engine = Engine(RecordingBackend() if args.silent else FluidSynthBackend(), emit)
        engine.set_launch_mode(args.quantization)
        request = {"source": source, "filename": str(filename)}
        if args.part is None or args.part == "all":
            engine.run_all(request)
        else:
            engine.run({**request, "name": args.part})
        while engine.active:
            engine.tick()
            time.sleep(0.002)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"pyChanga: {error}", file=sys.stderr)
        failed = True
    finally:
        if engine:
            engine.close()
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
