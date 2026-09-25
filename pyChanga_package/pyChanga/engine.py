"""The conductor: process supervision, a beat timeline, and bounded scheduling."""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import multiprocessing as mp
import time
import uuid

from .audio import RecordingBackend
from .errors import error_info
from .execution import LaunchPlan, PartSource, prepare_run
from .transport import Transport
from .worker import run_worker

LOOKAHEAD = 0.100
GUARD = 0.030
LATE_TOLERANCE = 0.020
MAX_NOTES = 1024
MAX_PARTS = 32
MAX_REMEMBERED_PARTS = 128


@dataclass
class Note:
    """One note, with start/end positions in absolute beats."""

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
    """One execution of a part; replacements prepare before taking over."""

    identity: str
    part_id: str
    process: object
    connection: object
    quantum: float
    filename: str
    request_id: str | None
    source: str = ""
    reserved_names: frozenset[str] = frozenset()
    earliest_beat: float | None = None
    group: str | None = None
    ready: bool = False
    initial_tempo: float | None = None
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
    """A named part can have a playing revision and a prepared replacement."""

    identity: str
    name: str
    document_id: str
    filename: str
    line: int
    origin: str = "section"
    current: Revision | None = None
    pending: Revision | None = None
    state: str = "stopped"
    error: dict | None = None


class Engine:
    """Own the workers, shared clock and note queue on one controlling thread.

    Call tick() regularly from a runner. No editor, event loop or audio device is
    created implicitly; callers supply the backend and event callback.
    """

    def __init__(self, backend=None, emit=None):
        self.backend = backend or RecordingBackend()
        self.transport = Transport(self.backend.now())
        self.emit = emit or (lambda event: None)
        self.parts: dict[str, Part] = {}
        self.launch_groups: dict[str, list[Revision]] = {}
        self.context = mp.get_context("spawn")
        self.reaping = []
        self.last_status = -math.inf
        self.closed = False

    def event(self, kind, **fields):
        self.emit({"type": kind, **fields})

    def run(self, request):
        """Prepare and launch one source selection, or its # %% all launcher."""
        return self.start(prepare_run(request))

    def run_all(self, request):
        """Prepare and launch every musical section at a common boundary."""
        return self.start(prepare_run(request, all_parts=True))

    def start(self, plan: LaunchPlan):
        """Launch validated source. Parsing and compilation have already finished."""
        active = {part.identity for part in self.parts.values() if part.current or part.pending}
        requested = {f"{plan.document_id}::{part.name}" for part in plan.parts}
        if len(active | requested) > MAX_PARTS:
            raise ValueError(f"At most {MAX_PARTS} musical parts can run at once")

        group = uuid.uuid4().hex if plan.grouped else None
        if group:
            self.launch_groups[group] = []
        results = []
        try:
            for part_source in plan.parts:
                results.append(self._prepare(plan, part_source, group))
        except BaseException:
            if group:
                self._cancel_group(group)
            raise
        self.status(force=True)
        return {"parts": results} if plan.grouped else results[0]

    def _remember_part(self, part: Part) -> None:
        """Bound the status history without discarding any active parts."""
        if len(self.parts) >= MAX_REMEMBERED_PARTS:
            for identity, previous in self.parts.items():
                if previous.current is None and previous.pending is None:
                    del self.parts[identity]
                    break
        self.parts[part.identity] = part

    def _spawn_revision(self, part, payload, quantum, request_id, *,
                        reserved_names, group=None, earliest_beat=None):
        """Create one worker and always close the parent's copy of its pipe."""
        parent, child = self.context.Pipe()
        process = self.context.Process(
            target=run_worker,
            args=(child, payload),
            name=f"pyChanga: {part.name}",
            daemon=True,
        )
        revision = Revision(
            identity=uuid.uuid4().hex,
            part_id=part.identity,
            process=process,
            connection=parent,
            quantum=quantum,
            filename=payload["filename"],
            request_id=request_id,
            source=payload["source"],
            reserved_names=reserved_names,
            group=group,
            earliest_beat=earliest_beat,
        )
        try:
            process.start()
        except BaseException:
            parent.close()
            raise
        finally:
            child.close()
        return revision

    def _prepare(self, plan: LaunchPlan, source: PartSource, group):
        identity = f"{plan.document_id}::{source.name}"
        part = self.parts.get(identity)
        if part is None:
            part = Part(identity, source.name, plan.document_id, plan.filename, source.line)
            self._remember_part(part)
        self._cancel_pending(part)
        part.filename = plan.filename
        part.line = source.line
        part.error = None
        payload = {
            "source": plan.source,
            "filename": plan.filename,
            "setup": plan.setup,
            "body": source.body,
        }
        revision = self._spawn_revision(
            part, payload, plan.quantum, plan.request_id,
            reserved_names=plan.reserved_names, group=group,
        )
        part.pending = revision
        if group:
            self.launch_groups[group].append(revision)
        part.state = "playing" if part.current else "preparing"
        return {"partId": identity, "revision": revision.identity, "name": part.name}

    def set_tempo(self, bpm, earliest_beat=None):
        if isinstance(bpm, bool) or not isinstance(bpm, (int, float)) or not math.isfinite(bpm) or not 20 <= bpm <= 400:
            raise ValueError("Tempo must be between 20 and 400 BPM")
        beat = self.transport.boundary(self.backend.now() + LOOKAHEAD + GUARD, 1)
        if earliest_beat is not None:
            beat = max(beat, earliest_beat)
        self.transport.set_tempo(bpm, beat)
        self.event("tempo", bpm=bpm, effectiveBeat=beat)
        return {"bpm": bpm, "effectiveBeat": beat}

    def _reply(self, revision):
        try:
            revision.connection.send({"type": "continue"})
        except (BrokenPipeError, EOFError, OSError):
            pass

    def _message(self, part, revision, message):
        kind = message["type"]
        now = self.backend.now()
        if kind == "ready":
            revision.ready = True
            revision.initial_tempo = message.get("tempo")
            if revision.group:
                members = self.launch_groups[revision.group]
                if all(member.ready for member in members):
                    self.launch_groups.pop(revision.group)
                    self._launch(members)
            else:
                self._launch([revision])
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
        elif kind == "run":
            self._run_from_part(part, revision, message)
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
            if revision.start is None:
                self._fail(part, revision, {"message": "The part exited before completing setup", "filename": revision.filename, "line": part.line})
                return
            revision.done = True
            revision.cursor = message["cursor"]
        elif kind == "error":
            self._fail(part, revision, message)
        else:
            raise ValueError(f"Invalid worker message: {kind}")

    def _launch(self, revisions):
        earliest = self.backend.now() + LOOKAHEAD + GUARD
        for revision in revisions:
            if revision.earliest_beat is not None:
                earliest = max(earliest, self.transport.time_at(revision.earliest_beat))
        start = self.transport.boundary(earliest, revisions[0].quantum)
        for revision in revisions:
            revision.group, revision.start = None, start
            if revision.initial_tempo is not None:
                self.transport.set_tempo(revision.initial_tempo, start)
                self.event("tempo", bpm=revision.initial_tempo, effectiveBeat=start)
            part = self.parts[revision.part_id]
            if part.current:
                part.current.stop = start
            self._reply(revision)
            self.event("scheduled", partId=part.identity, revision=revision.identity, beat=start)

    def _run_from_part(self, part, revision, message):
        try:
            if revision.start is None:
                raise ValueError("Put run() in a musical part, not setup")
            active = sum(bool(p.current or p.pending) for p in self.parts.values())
            if active >= MAX_PARTS:
                self.event("warning", partId=part.identity, revision=revision.identity,
                           documentId=part.document_id,
                           message=f"At most {MAX_PARTS} musical parts can run at once; skipped run({message['name']}).")
                revision.connection.send({"type": "continue", "name": None})
                return
            base = message["name"]
            if not isinstance(base, str) or not base.isidentifier():
                raise ValueError("run() needs a named function")
            blob = message["function"]
            if not isinstance(blob, bytes) or len(blob) > 1_000_000:
                raise ValueError("A launched function and its arguments must fit within 1 MB")
            index = 1
            while True:
                name = f"{base}{index}"
                identity = f"{part.document_id}::function::{name}"
                existing = self.parts.get(identity)
                if name not in revision.reserved_names and not (existing and (existing.current or existing.pending)):
                    break
                index += 1
            if existing is None:
                existing = Part(identity, name, part.document_id, revision.filename, message["line"], origin="function")
                self._remember_part(existing)
            existing.filename = revision.filename
            existing.line = message["line"]
            existing.error = None
            payload = {"source": revision.source, "filename": revision.filename, "function": blob}
            launched = self._spawn_revision(
                existing, payload, revision.quantum, revision.request_id,
                reserved_names=revision.reserved_names,
                earliest_beat=revision.start + message["cursor"],
            )
            existing.pending = launched
            existing.state = "preparing"
            revision.connection.send({"type": "continue", "name": name})
            self.status(force=True)
        except Exception as error:
            # Raise at the user's call site, allowing normal Python try/except.
            revision.connection.send({"type": "error", "message": str(error)})

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
            if part.pending.group:
                self._cancel_group(part.pending.group)
                return
            self._terminate(part.pending)
            part.pending = None
            if part.current:
                self._restore(part.current)

    def _cancel_group(self, group):
        for revision in self.launch_groups.pop(group, []):
            revision.group = None
            part = self.parts[revision.part_id]
            self._cancel_pending(part)
            part.state = "playing" if part.current else "error" if part.error else "stopped"

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
        self._cancel_pending(part)
        if part.current:
            self._terminate(part.current)
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
        """Advance playback without waiting for any individual worker."""
        if self.closed:
            return
        for part in list(self.parts.values()):
            self._activate_pending(part)
            for revision in (part.current, part.pending):
                if revision is None:
                    continue
                try:
                    self._tick_revision(part, revision)
                except (EOFError, BrokenPipeError, OSError):
                    if not revision.done:
                        self._fail(part, revision, {
                            "message": "The Python part exited unexpectedly",
                            "filename": revision.filename,
                            "line": part.line,
                        })
                except Exception as error:
                    self._fail(part, revision, error_info(error, revision.filename))
        self._reap()
        self.status()

    def _activate_pending(self, part):
        """Replace the old revision only when the scheduled boundary arrives."""
        pending = part.pending
        if pending is None or pending.start is None:
            return
        if self.transport.time_at(pending.start) > self.backend.now():
            return
        if part.current:
            self._terminate(part.current)
        part.current = pending
        part.pending = None
        part.state = "playing"

    def _tick_revision(self, part, revision):
        if revision.next_cursor is not None and not revision.process.is_alive():
            raise BrokenPipeError("The Python part exited while waiting")

        # Limit work per part so a talkative worker cannot starve the others.
        for _ in range(16):
            if revision.done or revision.next_cursor is not None or not revision.connection.poll():
                break
            self._message(part, revision, revision.connection.recv())
            if revision is not part.current and revision is not part.pending:
                return  # A worker error may have cancelled this revision or its group.

        now = self.backend.now()
        self._schedule(part, revision, now)
        if revision.next_cursor is not None:
            resume_at = self.transport.time_at(revision.next_cursor)
            if resume_at <= now + LOOKAHEAD:
                revision.next_cursor = None
                self._reply(revision)

        # Returning from Python does not end a final nonblocking note early.
        if revision.done and revision.start is not None and not revision.notes:
            finish_at = self.transport.time_at(revision.start + revision.cursor)
            if finish_at <= now:
                self._finish_revision(part, revision)

    def _finish_revision(self, part, revision):
        self._terminate(revision, immediate=False)
        if part.current is revision:
            part.current = None
        if part.pending is revision:
            part.pending = None
            if part.current:
                self._restore(part.current)
        if part.current:
            part.state = "playing"
        elif part.pending:
            part.state = "preparing"
        else:
            part.state = "finished"

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
                "parts": [{"id": p.identity, "name": p.name, "origin": p.origin, "documentId": p.document_id, "filename": p.filename,
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
