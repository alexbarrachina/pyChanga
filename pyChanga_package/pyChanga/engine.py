"""The conductor: process supervision, a beat timeline, and bounded scheduling."""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import multiprocessing as mp
import time
import uuid

from .audio import RecordingBackend
from .sections import execution, parse_document
from .transport import Transport
from .worker import error_info, run_worker

LOOKAHEAD = 0.100
GUARD = 0.030
LATE_TOLERANCE = 0.020
MAX_NOTES = 1024
MAX_PARTS = 32


@dataclass
class Note:
    identity: str
    owner: str
    instrument: str
    pitch: int
    volume: float
    start: float
    end: float
    on_sent: bool = False
    off_sent: bool = False


@dataclass
class Revision:
    identity: str
    part_id: str
    process: object
    connection: object
    quantum: float
    filename: str
    request_id: str | None
    start: float | None = None
    stop: float | None = None
    next_cursor: float | None = None
    done: bool = False
    cursor: float = 0
    notes: dict[str, Note] = field(default_factory=dict)
    output_epoch: float = 0
    output_bytes: int = 0
    output_warned: bool = False
    late_warned: bool = False


@dataclass
class Part:
    identity: str
    name: str
    document_id: str
    filename: str
    line: int
    current: Revision | None = None
    pending: Revision | None = None
    state: str = "stopped"
    error: dict | None = None


class Engine:
    def __init__(self, backend=None, emit=None):
        self.backend = backend or RecordingBackend()
        self.transport = Transport(self.backend.now())
        self.emit = emit or (lambda event: None)
        self.parts: dict[str, Part] = {}
        self.context = mp.get_context("spawn")
        self.reaping = []
        self.last_status = -math.inf
        self.closed = False

    def event(self, kind, **fields):
        self.emit({"version": 1, "type": kind, **fields})

    def run(self, request):
        source = request["source"]
        if not isinstance(source, str) or len(source.encode("utf-8")) > 1_000_000:
            raise ValueError("A document must contain at most 1 MB of Python source")
        filename = request.get("filename") or "untitled.py"
        document, section, body = execution(source, filename, request.get("selection"), request.get("name"))
        document_id = str(request.get("documentId", filename))
        identity = f"{document_id}::{section.name}"
        quantum = {"immediate": 0, "beat": 1, "bar": 4}.get(request.get("quantization", "beat"))
        if quantum is None:
            raise ValueError("Launch timing must be immediate, beat or bar")
        active = sum(bool(p.current or p.pending) for p in self.parts.values())
        part = self.parts.get(identity)
        if active >= MAX_PARTS and (part is None or not (part.current or part.pending)):
            raise ValueError(f"At most {MAX_PARTS} musical parts can run at once")
        if part is None:
            if len(self.parts) >= 128:
                oldest = next((key for key, p in self.parts.items() if not (p.current or p.pending)), None)
                if oldest:
                    del self.parts[oldest]
            part = Part(identity, section.name, document_id, filename, section.start_line)
            self.parts[identity] = part
        self._cancel_pending(part)
        part.filename, part.line, part.error = filename, section.start_line, None
        parent, child = self.context.Pipe()
        revision_id = uuid.uuid4().hex
        payload = {"source": source, "filename": filename, "setup": document.setup, "body": body}
        process = self.context.Process(target=run_worker, args=(child, payload), name=f"pyChanga: {section.name}", daemon=True)
        revision = Revision(revision_id, identity, process, parent, quantum, filename, request.get("requestId"))
        try:
            process.start()
        except BaseException:
            parent.close()
            child.close()
            raise
        child.close()
        part.pending = revision
        part.state = "playing" if part.current else "preparing"
        self.status(force=True)
        return {"partId": identity, "revision": revision_id, "name": section.name}

    def set_tempo(self, bpm, earliest_beat=None):
        if isinstance(bpm, bool) or not isinstance(bpm, (int, float)) or not math.isfinite(bpm) or not 20 <= bpm <= 400:
            raise ValueError("Tempo must be between 20 and 400 BPM")
        beat = self.transport.boundary(self.backend.now() + LOOKAHEAD + GUARD, 1)
        if earliest_beat is not None:
            beat = max(beat, earliest_beat)
        self.transport.set_tempo(bpm, beat)
        self.event("tempo", bpm=bpm, effectiveBeat=beat)
        return {"bpm": bpm, "effectiveBeat": beat}

    def command(self, request):
        request_id = request.get("requestId")
        try:
            if request.get("version") != 1:
                raise ValueError("Unsupported protocol version; expected version 1")
            kind = request.get("type")
            if kind == "run":
                result = self.run(request)
            elif kind == "stop":
                self.stop(request["partId"])
                result = {}
            elif kind == "stop_all":
                self.stop_all()
                result = {}
            elif kind == "tempo":
                result = self.set_tempo(request["bpm"])
            elif kind == "parse":
                document = parse_document(request["source"])
                result = {"parts": [{"name": p.name, "line": p.start_line, "markerLine": p.marker_line,
                                      "endLine": p.end_line} for p in document.parts]}
            elif kind == "status":
                result = self.snapshot()
            elif kind == "shutdown":
                self.close()
                result = {}
            else:
                raise ValueError(f"Unknown command: {kind}")
            self.event("response", requestId=request_id, ok=True, result=result)
        except Exception as error:
            self.event("response", requestId=request_id, ok=False,
                       error=error_info(error, request.get("filename", "untitled.py")))

    def _reply(self, revision):
        try:
            revision.connection.send({"type": "continue"})
        except (BrokenPipeError, EOFError, OSError):
            pass

    def _message(self, part, revision, message):
        kind = message["type"]
        now = self.backend.now()
        if kind == "ready":
            revision.start = self.transport.boundary(now + LOOKAHEAD + GUARD, revision.quantum)
            if message.get("tempo") is not None:
                # Setup completed successfully; apply its requested tempo at the launch beat.
                self.transport.set_tempo(message["tempo"], revision.start)
                self.event("tempo", bpm=message["tempo"], effectiveBeat=revision.start)
            if part.current:
                part.current.stop = revision.start
            self._reply(revision)
            self.event("scheduled", partId=part.identity, revision=revision.identity, beat=revision.start)
        elif kind in ("note", "wait"):
            if revision.start is None:
                raise ValueError("The part has not completed setup")
            cursor = float(message["next"])
            if not math.isfinite(cursor) or not 0 <= cursor <= 1e9 or cursor < revision.cursor:
                raise ValueError("The part's beat cursor is invalid")
            revision.cursor = cursor
            if kind == "note":
                if len(revision.notes) + len(message["pitches"]) > MAX_NOTES:
                    raise ValueError("Too many pending notes. Add wait(...) or use blocking notes to advance musical time.")
                onset = revision.start + message["cursor"]
                end = onset + message["duration"]
                if message["volume"] > 0:
                    for pitch in message["pitches"]:
                        identity = uuid.uuid4().hex
                        revision.notes[identity] = Note(identity, revision.identity, message["instrument"], pitch,
                                                        message["volume"], onset, end)
            revision.next_cursor = revision.start + cursor
        elif kind == "tempo":
            self.set_tempo(message["bpm"], revision.start + message["cursor"])
            self._reply(revision)
        elif kind == "output":
            if now - revision.output_epoch >= 1:
                revision.output_epoch, revision.output_bytes, revision.output_warned = now, 0, False
            text = str(message["text"])[:4096]
            revision.output_bytes += len(text)
            if revision.output_bytes <= 16384:
                self.event("output", partId=part.identity, revision=revision.identity, stream=message["stream"], text=text)
            elif not revision.output_warned:
                self.event("output", partId=part.identity, revision=revision.identity, stream="stderr", text="\nOutput limited to keep playback responsive.\n")
                revision.output_warned = True
            self._reply(revision)
        elif kind == "done":
            revision.done = True
            revision.cursor = message["cursor"]
        elif kind == "error":
            self._fail(part, revision, message)
        else:
            raise ValueError(f"Invalid worker message: {kind}")

    def _fail(self, part, revision, error):
        part.error = {key: error[key] for key in ("message", "filename", "line", "column", "traceback", "phase") if key in error}
        self.event("error", partId=part.identity, revision=revision.identity, requestId=revision.request_id,
                   documentId=part.document_id, **part.error)
        if part.pending is revision:
            self._cancel_pending(part)
        elif part.current is revision:
            self._terminate(revision)
            part.current = None
        part.state = "playing" if part.current else "preparing" if part.pending else "error"

    def _restore(self, revision):
        revision.stop = None
        now = self.backend.now()
        self.backend.remove_future(revision.identity)
        for note in revision.notes.values():
            if self.transport.time_at(note.start) >= now:
                note.on_sent = False
            if self.transport.time_at(note.end) >= now:
                note.off_sent = False

    def _cancel_pending(self, part):
        if part.pending:
            self._terminate(part.pending)
            part.pending = None
            if part.current:
                self._restore(part.current)

    def _terminate(self, revision, immediate=True):
        self.backend.release_owner(revision.identity, immediate=immediate)
        revision.notes.clear()
        revision.connection.close()
        if revision.process.is_alive():
            revision.process.terminate()
        self.reaping.append((revision.process, time.monotonic()))

    def stop(self, identity):
        part = self.parts.get(identity)
        if not part:
            return
        for revision in (part.pending, part.current):
            if revision:
                self._terminate(revision)
        part.pending = part.current = None
        part.state, part.error = "stopped", None
        self.status(force=True)

    def stop_all(self):
        for identity in list(self.parts):
            self.stop(identity)

    def _schedule(self, part, revision, now):
        horizon = now + LOOKAHEAD
        for identity, note in list(revision.notes.items()):
            if revision.stop is not None and note.start >= revision.stop:
                # Retain unsent events until replacement commits, so an aborted edit can restore them.
                continue
            ending = min(note.end, revision.stop) if revision.stop is not None else note.end
            start_time, end_time = self.transport.time_at(note.start), self.transport.time_at(ending)
            if not note.on_sent and start_time <= horizon:
                if start_time < now - LATE_TOLERANCE:
                    del revision.notes[identity]
                    if not revision.late_warned:
                        self.event("warning", partId=part.identity, message="This part missed a note deadline. Long calculations or time.sleep() can make notes late; use wait() for musical timing.")
                        revision.late_warned = True
                    continue
                self.backend.note_on(identity, revision.identity, note.instrument, note.pitch, note.volume, start_time)
                note.on_sent = True
            if note.on_sent and not note.off_sent and end_time <= horizon:
                self.backend.note_off(identity, revision.identity, end_time)
                note.off_sent = True
            if note.off_sent and end_time <= now:
                self.backend.finish_note(identity)
                del revision.notes[identity]

    def tick(self):
        if self.closed:
            return
        for part in list(self.parts.values()):
            now = self.backend.now()
            if part.pending and part.pending.start is not None and self.transport.time_at(part.pending.start) <= now:
                if part.current:
                    self._terminate(part.current)
                part.current, part.pending = part.pending, None
                part.state = "playing"
            for revision in (part.current, part.pending):
                if revision is None:
                    continue
                try:
                    if revision.next_cursor is not None and not revision.process.is_alive():
                        raise BrokenPipeError("The Python part exited while waiting")
                    for _ in range(16):
                        if revision.done or revision.next_cursor is not None or not revision.connection.poll():
                            break
                        self._message(part, revision, revision.connection.recv())
                        if revision is not part.current and revision is not part.pending:
                            break
                    if revision is not part.current and revision is not part.pending:
                        continue
                    now = self.backend.now()
                    self._schedule(part, revision, now)
                    if revision.next_cursor is not None and self.transport.time_at(revision.next_cursor) <= now + LOOKAHEAD:
                        revision.next_cursor = None
                        self._reply(revision)
                    if revision.done and revision.start is not None and not revision.notes and self.transport.time_at(revision.start + revision.cursor) <= now:
                        self._terminate(revision, immediate=False)
                        if part.current is revision:
                            part.current = None
                        if part.pending is revision:
                            part.pending = None
                            if part.current:
                                self._restore(part.current)
                        part.state = "playing" if part.current else "preparing" if part.pending else "finished"
                except (EOFError, BrokenPipeError, OSError) as error:
                    if not revision.done:
                        self._fail(part, revision, {"message": "The Python part exited unexpectedly", "filename": revision.filename, "line": part.line})
                except Exception as error:
                    self._fail(part, revision, error_info(error, revision.filename))
        self._reap()
        self.status()

    def _reap(self):
        remaining = []
        for process, started in self.reaping:
            if process.is_alive() and time.monotonic() - started > 0.1:
                process.kill()
            if process.is_alive():
                remaining.append((process, started))
            else:
                process.join(timeout=0)
                process.close()
        self.reaping = remaining

    def snapshot(self):
        now = self.backend.now()
        future = next((s for s in self.transport.segments if s.seconds > now), None)
        return {"beat": self.transport.beat_at(now), "bpm": self.transport.bpm_at(now),
                "pendingTempo": {"bpm": future.bpm, "beat": future.beat} if future else None,
                "parts": [{"id": p.identity, "name": p.name, "documentId": p.document_id, "filename": p.filename,
                           "line": p.line, "state": p.state, "revision": p.current.identity if p.current else None,
                           "pending": {"revision": p.pending.identity, "beat": p.pending.start} if p.pending else None,
                           "error": p.error} for p in self.parts.values()]}

    def status(self, force=False):
        now = time.monotonic()
        if force or now - self.last_status >= 0.1:
            self.last_status = now
            self.event("status", **self.snapshot())

    @property
    def active(self):
        return any(p.current or p.pending for p in self.parts.values())

    def close(self):
        if self.closed:
            return
        self.stop_all()
        deadline = time.monotonic() + 1
        while self.reaping and time.monotonic() < deadline:
            self._reap()
            time.sleep(0.005)
        self.backend.close()
        self.closed = True
