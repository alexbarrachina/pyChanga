"""A small FluidSynth C API adapter and a deterministic recording backend."""
from __future__ import annotations
import ctypes as C
from ctypes.util import find_library
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import time

from .instruments import PROGRAMS


class AudioError(RuntimeError):
    pass


class RecordingBackend:
    """No audio device. Records absolute deadlines for scheduler tests."""
    def __init__(self, clock=time.monotonic):
        self.now = clock
        self.events = []

    def note_on(self, identity, owner, instrument, pitch, volume, at):
        self.events.append(dict(type="on", id=identity, owner=owner, instrument=instrument,
                                pitch=pitch, volume=volume, at=at))

    def note_off(self, identity, owner, at):
        self.events.append(dict(type="off", id=identity, owner=owner, at=at))

    def remove_future(self, owner):
        now = self.now()
        self.events[:] = [e for e in self.events if e.get("owner") != owner or e["at"] < now]

    def finish_note(self, identity):
        pass

    def release_owner(self, owner, immediate=True):
        self.remove_future(owner)
        self.events.append(dict(type="release", owner=owner, at=self.now(), immediate=immediate))

    def close(self):
        pass


@dataclass
class Voice:
    owner: str
    channel: int
    pitch: int


class FluidSynthBackend:
    """Native audio and sample-driven sequencer; never calls Python on the audio thread."""
    def __init__(self, soundfont=None, library=None, audio_driver=None):
        self.settings = self.synth = self.seq = self.driver = None
        self.sources, self.channels, self.voices = {}, {}, {}
        self.busy = set()
        self.lib = self._load_library(library)
        self._bindings()
        try:
            self.settings = self.new_fluid_settings()
            self.fluid_settings_setnum(self.settings, b"synth.sample-rate", 48000.0)
            self.fluid_settings_setnum(self.settings, b"synth.gain", 0.5)
            self.fluid_settings_setint(self.settings, b"synth.midi-channels", 256)
            self.fluid_settings_setint(self.settings, b"synth.polyphony", 512)
            self.fluid_settings_setint(self.settings, b"audio.period-size", 128)
            self.fluid_settings_setint(self.settings, b"audio.periods", 3)
            self.fluid_settings_setint(self.settings, b"synth.reverb.active", 1)
            self.synth = self.new_fluid_synth(self.settings)
            if not self.synth:
                raise AudioError("FluidSynth could not create the synthesizer")
            font = Path(soundfont or os.environ.get("PYCHANGA_SOUNDFONT", Path(__file__).parent / "sounds" / "pyChanga.sf2"))
            if not font.is_file():
                raise AudioError(f"Soundfont not found: {font}")
            # Each note selects its preset explicitly; avoid a General MIDI reset
            # looking for a bank-128 kit that the custom soundfont does not contain.
            self.soundfont = self.fluid_synth_sfload(self.synth, os.fsencode(font), 0)
            if self.soundfont < 0:
                raise AudioError(f"Could not load soundfont: {font}")
            self.seq = self.new_fluid_sequencer2(0)
            if not self.seq:
                raise AudioError("Could not create the FluidSynth sequencer")
            self.destination = self.fluid_sequencer_register_fluidsynth(self.seq, self.synth)
            if self.destination < 0:
                raise AudioError("Could not connect the synthesizer to the sequencer")
            self.origin = time.monotonic()
            self.offline = audio_driver == "offline"
            if not self.offline:
                self._start_audio_driver(audio_driver)
        except BaseException:
            self.close()
            raise

    def _start_audio_driver(self, requested):
        if requested:
            drivers = [requested]
        elif sys.platform == "darwin":
            drivers = ["coreaudio", "portaudio"]
        elif sys.platform == "win32":
            drivers = ["wasapi"]
        else:
            drivers = [None]
        for driver in drivers:
            if driver and self.fluid_settings_setstr(self.settings, b"audio.driver", driver.encode()) < 0:
                continue
            self.driver = self.new_fluid_audio_driver(self.settings, self.synth)
            if not self.driver:
                continue
            # An open device can still have a stalled audio callback. Without samples,
            # the sequencer never advances and every part stays queued indefinitely.
            initial_tick = self.fluid_sequencer_get_tick(self.seq)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                time.sleep(.01)
                if self.fluid_sequencer_get_tick(self.seq) != initial_tick:
                    return
            self.delete_fluid_audio_driver(self.driver)
            self.driver = None
        raise AudioError("Could not start audio playback. Check your system audio output and restart playback.")

    @staticmethod
    def _load_library(explicit):
        names = [explicit, os.environ.get("PYCHANGA_FLUIDSYNTH")]
        native = os.environ.get("PYCHANGA_NATIVE_DIR")
        if native:
            if sys.platform == "win32":
                # Keep the directory handle alive for transitive DLL dependencies.
                FluidSynthBackend._dll_directory = os.add_dll_directory(native)
            names += [str(p) for p in Path(native).glob("*fluidsynth*." + ("dll" if sys.platform == "win32" else "dylib" if sys.platform == "darwin" else "so*"))]
        names += [find_library("fluidsynth"), find_library("libfluidsynth-3"),
                  "/opt/homebrew/lib/libfluidsynth.dylib", "/usr/local/lib/libfluidsynth.dylib"]
        errors = []
        for name in dict.fromkeys(n for n in names if n):
            try:
                return C.CDLL(name)
            except OSError as error:
                errors.append(str(error))
        raise AudioError("FluidSynth could not be loaded. Install its native library or set PYCHANGA_FLUIDSYNTH to its path.\n" + "\n".join(errors)[-1500:])

    def _bindings(self):
        ptr, integer, uint, short, text = C.c_void_p, C.c_int, C.c_uint, C.c_short, C.c_char_p
        definitions = {
            "new_fluid_settings": (ptr, []), "delete_fluid_settings": (None, [ptr]),
            "fluid_settings_setnum": (integer, [ptr, text, C.c_double]),
            "fluid_settings_setint": (integer, [ptr, text, integer]),
            "fluid_settings_setstr": (integer, [ptr, text, text]),
            "new_fluid_synth": (ptr, [ptr]), "delete_fluid_synth": (None, [ptr]),
            "fluid_synth_sfload": (integer, [ptr, text, integer]),
            "fluid_synth_program_select": (integer, [ptr, integer, integer, integer, integer]),
            "fluid_synth_set_channel_type": (integer, [ptr, integer, integer]),
            "fluid_synth_all_sounds_off": (integer, [ptr, integer]),
            "fluid_synth_all_notes_off": (integer, [ptr, integer]),
            "fluid_synth_write_float": (integer, [ptr, integer, ptr, integer, integer, ptr, integer, integer]),
            "new_fluid_audio_driver": (ptr, [ptr, ptr]), "delete_fluid_audio_driver": (None, [ptr]),
            "new_fluid_sequencer2": (ptr, [integer]), "delete_fluid_sequencer": (None, [ptr]),
            "fluid_sequencer_register_fluidsynth": (short, [ptr, ptr]),
            "fluid_sequencer_register_client": (short, [ptr, text, ptr, ptr]),
            "fluid_sequencer_unregister_client": (None, [ptr, short]),
            "fluid_sequencer_get_tick": (uint, [ptr]),
            "fluid_sequencer_send_at": (integer, [ptr, ptr, uint, integer]),
            "fluid_sequencer_remove_events": (None, [ptr, short, short, integer]),
            "new_fluid_event": (ptr, []), "delete_fluid_event": (None, [ptr]),
            "fluid_event_set_source": (None, [ptr, short]), "fluid_event_set_dest": (None, [ptr, short]),
            "fluid_event_noteon": (None, [ptr, integer, short, short]),
            "fluid_event_noteoff": (None, [ptr, integer, short]),
        }
        for name, (result, args) in definitions.items():
            function = getattr(self.lib, name)
            function.restype, function.argtypes = result, args
            setattr(self, name, function)

    def now(self):
        return self.origin + self.fluid_sequencer_get_tick(self.seq) / 1000

    def render(self, frames):
        """Render test audio without a sound device, advancing the same native sequencer."""
        if not self.offline:
            raise RuntimeError("Rendering is available only with audio_driver='offline'")
        left, right = (C.c_float * frames)(), (C.c_float * frames)()
        if self.fluid_synth_write_float(self.synth, frames, left, 0, 1, right, 0, 1) < 0:
            raise AudioError("Could not render audio")
        return list(left), list(right)

    def _source(self, owner):
        if owner not in self.sources:
            source = self.fluid_sequencer_register_client(self.seq, owner.encode(), None, None)
            if source < 0:
                raise AudioError("Could not allocate a musical part")
            self.sources[owner] = source
        return self.sources[owner]

    def _send(self, owner, at, kind, channel, pitch, velocity=None):
        event = self.new_fluid_event()
        try:
            self.fluid_event_set_source(event, self._source(owner))
            self.fluid_event_set_dest(event, self.destination)
            if kind == "on":
                self.fluid_event_noteon(event, channel, pitch, velocity)
            else:
                self.fluid_event_noteoff(event, channel, pitch)
            tick = max(self.fluid_sequencer_get_tick(self.seq), round((at - self.origin) * 1000))
            if self.fluid_sequencer_send_at(self.seq, event, tick, 1) < 0:
                raise AudioError("The audio event queue is full")
        finally:
            self.delete_fluid_event(event)

    def note_on(self, identity, owner, instrument, pitch, volume, at):
        existing = self.voices.get(identity)
        if existing:
            channel = existing.channel
        else:
            channel = next((i for i, o in self.channels.items() if o == owner and i not in self.busy), None)
            if channel is None:
                channel = next((i for i in range(256) if i not in self.channels), None)
            if channel is None:
                raise AudioError("Too many overlapping notes (256 voices). Stop a part or shorten note durations.")
            self.channels[channel] = owner
            self.busy.add(channel)
            self.voices[identity] = Voice(owner, channel, pitch)
        # The custom drum and chip kits are regular bank-0 presets too.
        self.fluid_synth_set_channel_type(self.synth, channel, 0)
        if self.fluid_synth_program_select(self.synth, channel, self.soundfont, 0, PROGRAMS[instrument]) < 0:
            raise AudioError(f"The soundfont does not contain {instrument}")
        self._send(owner, at, "on", channel, pitch, max(1, round(volume * 127)))

    def note_off(self, identity, owner, at):
        voice = self.voices.get(identity)
        if voice:
            self._send(owner, at, "off", voice.channel, voice.pitch)

    def finish_note(self, identity):
        voice = self.voices.pop(identity, None)
        if voice:
            self.busy.discard(voice.channel)

    def remove_future(self, owner):
        if owner in self.sources:
            self.fluid_sequencer_remove_events(self.seq, self.sources[owner], -1, -1)

    def release_owner(self, owner, immediate=True):
        self.remove_future(owner)
        for channel in [c for c, o in self.channels.items() if o == owner]:
            if immediate:
                self.fluid_synth_all_sounds_off(self.synth, channel)
            else:
                self.fluid_synth_all_notes_off(self.synth, channel)
            self.busy.discard(channel)
            del self.channels[channel]
        self.voices = {i: v for i, v in self.voices.items() if v.owner != owner}
        if owner in self.sources:
            self.fluid_sequencer_unregister_client(self.seq, self.sources.pop(owner))

    def close(self):
        for attribute, destructor in [("driver", "delete_fluid_audio_driver"), ("seq", "delete_fluid_sequencer"),
                                       ("synth", "delete_fluid_synth"), ("settings", "delete_fluid_settings")]:
            value = getattr(self, attribute, None)
            if value:
                getattr(self, destructor)(value)
                setattr(self, attribute, None)
