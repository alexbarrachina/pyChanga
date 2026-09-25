import pathlib
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pyChanga_package"))
from pyChanga.audio import RecordingBackend
from pyChanga.engine import Engine


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.backend = RecordingBackend()
        self.engine = Engine(self.backend, self.events.append)
    def tearDown(self):
        self.engine.close()
    def run_part(self, body, name='melody', setup='from pyChanga import *'):
        return self.engine.run({'source': f'# %% setup\n{setup}\n# %% {name}\n{body}\n',
                                'documentId': 'test', 'filename': str(pathlib.Path('/tmp/música test.py')),
                                'name': name, 'quantization': 'immediate'})
    def until(self, predicate, timeout=4):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.engine.tick()
            if predicate():
                return
            time.sleep(0.002)
        self.fail(f'Timed out: {self.engine.snapshot()}, errors: {[e for e in self.events if e["type"] == "error"]}')
    def test_final_nonblocking_note_drains(self):
        result = self.run_part('piano(60, 0.5, 0.4, block=False)')
        part = self.engine.parts[result['partId']]
        self.until(lambda: any(e['type'] == 'on' for e in self.backend.events))
        self.assertTrue(self.engine.active)
        self.until(lambda: part.state == 'finished')
        notes = [e for e in self.backend.events if e.get('owner') == result['revision']]
        on = next(e for e in notes if e['type'] == 'on')
        off = next(e for e in notes if e['type'] == 'off')
        self.assertAlmostEqual(off['at'] - on['at'], 0.4, places=5)
    def test_setup_and_syntax_errors_keep_old_part(self):
        original = self.run_part('while True:\n    piano(60, 0.5, 0.25)')
        part = self.engine.parts[original['partId']]
        self.until(lambda: part.current is not None)
        with self.assertRaises(SyntaxError):
            self.run_part('if')
        self.assertEqual(part.current.identity, original['revision'])
        self.run_part('piano(72, 0.5, 1)', setup='raise ValueError("bad setup")')
        self.until(lambda: part.error is not None)
        self.assertEqual(part.current.identity, original['revision'])
        self.assertIsNone(part.current.stop)
    def test_busy_loop_can_be_stopped_without_stopping_other_part(self):
        good = self.run_part('while True:\n    piano(60, 0.5, 0.25)', 'good')
        bad = self.run_part('while True:\n    pass', 'busy')
        self.until(lambda: all(p.current is not None for p in self.engine.parts.values()))
        start = time.monotonic()
        self.engine.stop(bad['partId'])
        self.assertLess(time.monotonic() - start, 0.25)
        self.assertIsNotNone(self.engine.parts[good['partId']].current)
        self.until(lambda: not self.engine.reaping)
    def test_replacement_releases_only_old_revision(self):
        old = self.run_part('while True:\n    piano(60, 0.5, 2)')
        other = self.run_part('while True:\n    piano(60, 0.5, 2)', 'other')
        part = self.engine.parts[old['partId']]
        self.until(lambda: part.current is not None)
        new = self.run_part('while True:\n    piano(72, 0.5, 0.25)')
        self.until(lambda: part.current is not None and part.current.identity == new['revision'])
        releases = [e['owner'] for e in self.backend.events if e['type'] == 'release']
        self.assertIn(old['revision'], releases)
        self.assertNotIn(other['revision'], releases)
    def test_runtime_error_is_local_and_has_source_line(self):
        good = self.run_part('while True:\n    wait(1)', 'good')
        bad = self.run_part('wait(0.5)\nraise ValueError("oops")', 'bad')
        self.until(lambda: self.engine.parts[bad['partId']].state == 'error')
        error = self.engine.parts[bad['partId']].error
        self.assertEqual(error['line'], 5)
        self.assertIsNotNone(self.engine.parts[good['partId']].current)
    def test_latest_pending_update_wins(self):
        self.run_part('while True:\n    wait(1)')
        first = self.run_part('while True:\n    piano(65, 0.5, 1)')
        last = self.run_part('while True:\n    piano(72, 0.5, 1)')
        part = self.engine.parts[last['partId']]
        self.until(lambda: part.current is not None)
        self.assertEqual(part.current.identity, last['revision'])
        self.assertFalse(any(e['type'] == 'on' and e['owner'] == first['revision'] for e in self.backend.events))

    def test_tempo_change_retimes_sustained_note_and_worker_wait(self):
        result = self.run_part('piano(60, 0.5, 2)')
        part = self.engine.parts[result['partId']]
        self.until(lambda: part.current is not None)
        ending = part.current.start + 2
        self.engine.set_tempo(120)
        expected = self.engine.transport.time_at(ending)
        self.until(lambda: part.state == 'finished')
        off = next(e for e in self.backend.events if e['type'] == 'off' and e['owner'] == result['revision'])
        self.assertAlmostEqual(off['at'], expected, places=5)

    def group_request(self, setup='', body='piano(60, .5, .25)', **extra):
        source = ('# %% setup\nfrom pyChanga import *\nfrom multiprocessing import current_process\n'
                  'import time\n' + setup + '\n# %% fast\n' + body + '\n# %% slow\n' + body + '\n# %% all\n')
        return {'source': source, 'filename': 'group.py', 'documentId': 'group',
                'name': 'all', 'quantization': 'immediate', **extra}

    def test_all_waits_for_setup_and_schedules_identical_onsets(self):
        request = self.group_request('if current_process().name.endswith("slow"):\n    time.sleep(.3)\ntempo(120)')
        request.pop('name')
        line = len(request['source'].splitlines())
        request['selection'] = {'startLine': line, 'endLine': line}
        result = self.engine.run(request)
        self.assertEqual([p['name'] for p in result['parts']], ['fast', 'slow'])
        fast, slow = [self.engine.parts[p['partId']] for p in result['parts']]
        self.until(lambda: fast.pending is not None and fast.pending.ready)
        self.assertIsNone(fast.pending.start)
        self.assertIsNone(slow.pending.start)
        self.assertEqual(self.engine.transport.bpm_at(self.backend.now()), 60)
        self.until(lambda: len([e for e in self.backend.events if e['type'] == 'on']) == 2)
        starts = [e['at'] for e in self.backend.events if e['type'] == 'on']
        self.assertEqual(starts[0], starts[1])
        self.assertEqual(len({e['beat'] for e in self.events if e['type'] == 'scheduled'}), 1)
        self.assertEqual(self.engine.transport.bpm_at(starts[0]), 120)
        self.assertNotIn('group::all', self.engine.parts)
        self.assertFalse(self.engine.launch_groups)
        self.until(lambda: not self.engine.active)

    def test_all_replaces_together_without_changing_another_document(self):
        other = self.run_part('while True:\n    piano(48, .5, .25)')
        request = self.group_request(body='while True:\n    piano(60, .5, .25)')
        original = self.engine.run(request)
        self.until(lambda: all(p.current for p in self.engine.parts.values()))
        updated = self.engine.run(request)
        self.until(lambda: all(self.engine.parts[p['partId']].current.identity == p['revision'] for p in updated['parts']))
        self.assertEqual(self.engine.parts[other['partId']].current.identity, other['revision'])
        starts = [self.engine.parts[p['partId']].current.start for p in updated['parts']]
        self.assertEqual(starts[0], starts[1])
        self.assertTrue(set(p['revision'] for p in original['parts']).isdisjoint(p['revision'] for p in updated['parts']))

    def test_group_setup_failure_preserves_existing_parts(self):
        original = self.engine.run(self.group_request(body='while True:\n    piano(60, .5, .25)'))
        self.until(lambda: all(p.current for p in self.engine.parts.values()))
        failed = self.engine.run(self.group_request('tempo(200)\nif current_process().name.endswith("slow"):\n    time.sleep(.2)\n    raise ValueError("bad group setup")'))
        self.until(lambda: any(p.error for p in self.engine.parts.values()))
        for p in original['parts']:
            part = self.engine.parts[p['partId']]
            self.assertEqual(part.current.identity, p['revision'])
            self.assertIsNone(part.current.stop)
            self.assertIsNone(part.pending)
        self.assertFalse(self.engine.launch_groups)
        failed_ids = {p['revision'] for p in failed['parts']}
        self.assertFalse(any(e['type'] == 'scheduled' and e['revision'] in failed_ids for e in self.events))
        self.assertEqual(self.engine.transport.bpm_at(self.backend.now() + 10), 60)

    def test_group_syntax_and_capacity_checks_happen_before_launch(self):
        request = self.group_request()
        request['source'] = request['source'].replace('# %% slow\npiano(60, .5, .25)', '# %% slow\nif')
        with self.assertRaises(SyntaxError):
            self.engine.run(request)
        self.assertFalse(self.engine.parts)
        with patch('pyChanga.engine.MAX_PARTS', 1), self.assertRaisesRegex(ValueError, 'At most 1'):
            self.engine.run(self.group_request())
        self.assertFalse(self.engine.parts)
        self.assertFalse(self.engine.launch_groups)

    def test_stopping_a_preparing_member_cancels_the_pending_group(self):
        self.engine.run(self.group_request('if current_process().name.endswith("slow"):\n    time.sleep(2)'))
        self.until(lambda: self.engine.parts['group::fast'].pending.ready)
        self.engine.stop('group::slow')
        self.assertFalse(self.engine.active)
        self.assertFalse(self.engine.launch_groups)
        self.assertFalse(any(e['type'] == 'scheduled' for e in self.events))
        self.until(lambda: not self.engine.reaping)

    def test_setup_exit_does_not_leave_a_group_waiting_forever(self):
        self.engine.run(self.group_request('if current_process().name.endswith("slow"):\n    raise SystemExit(0)'))
        self.until(lambda: not self.engine.active)
        self.assertFalse(self.engine.launch_groups)
        self.assertIn('before completing setup', self.engine.parts['group::slow'].error['message'])

    def test_run_all_without_marker(self):
        request = self.group_request()
        request['source'] = request['source'].replace('# %% all\n', '')
        self.engine.run_all(request)
        self.until(lambda: len([e for e in self.events if e['type'] == 'scheduled']) == 2)
        self.assertEqual(len({e['beat'] for e in self.events if e['type'] == 'scheduled'}), 1)

    def controller_request(self, body, setup=''):
        return {'source': ('# %% setup\nfrom pyChanga import *\n' + setup +
                           '\n# %% conductor\n' + body + '\n'),
                'filename': 'conductor.py', 'documentId': 'song', 'name': 'conductor', 'quantization': 'immediate'}

    def test_run_creates_independent_numbered_instances_and_caller_continues(self):
        setup = 'def notes(pitch):\n    while True:\n        piano(pitch, .5, .25)'
        result = self.engine.run(self.controller_request('run(notes, 60)\nrun(notes, 64)\npiano(72, .5, .25)', setup))
        first, second = 'song::function::notes1', 'song::function::notes2'
        self.until(lambda: all(self.engine.parts.get(key) and self.engine.parts[key].current for key in [first, second]))
        self.until(lambda: self.engine.parts[result['partId']].state == 'finished')
        self.assertTrue(self.engine.parts[first].current)
        self.assertTrue(self.engine.parts[second].current)
        self.assertEqual([self.engine.parts[key].origin for key in [first, second]], ['function', 'function'])
        self.until(lambda: {60, 64, 72} <= {e['pitch'] for e in self.backend.events if e['type'] == 'on'})
        self.engine.stop(first)
        self.assertTrue(self.engine.parts[second].current)
        self.assertFalse(any(e['type'] == 'error' for e in self.events))

    def test_run_supports_closures_and_wait_between_launches(self):
        setup = ('def make_seq(pitch):\n'
                 '    def sequence():\n'
                 '        while True:\n'
                 '            piano(pitch, .5, .25)\n'
                 '    return sequence\n'
                 'seq = make_seq(67)')
        self.engine.run(self.controller_request('run(seq)\nwait(.6)\nrun(seq)', setup))
        first, second = 'song::function::sequence1', 'song::function::sequence2'
        self.until(lambda: self.engine.parts.get(second) and self.engine.parts[second].current)
        launches = [e for e in self.events if e['type'] == 'scheduled' and e['partId'] in (first, second)]
        self.assertEqual(len(launches), 2)
        self.assertGreater(launches[1]['beat'], launches[0]['beat'] + .4)
        self.until(lambda: any(e['type'] == 'on' and e['pitch'] == 67 for e in self.backend.events))

    def test_function_names_respect_source_sections_in_nested_launches(self):
        request = self.controller_request(
            'run(parent)',
            setup='def notes():\n    piano(60, .5, .1)\ndef parent():\n    run(notes)',
        )
        request['source'] += '# %% notes1\npass\n'
        self.engine.run(request)
        self.until(lambda: 'song::function::notes2' in self.engine.parts)
        self.assertNotIn('song::function::notes1', self.engine.parts)
        self.until(lambda: not self.engine.active)
        self.assertTrue(any(event['type'] == 'on' for event in self.backend.events))

    def test_run_instances_have_independent_default_random_streams(self):
        for setup in [
            ('from random import randint\n'
             'def roll():\n    print(randint(0, 2**128 - 1))\n    wait(8)'),
            ('def make_roll():\n'
             '    from random import randint\n'
             '    def roll():\n        print(randint(0, 2**128 - 1))\n        wait(8)\n'
             '    return roll\nroll = make_roll()'),
        ]:
            with self.subTest(setup=setup):
                self.events.clear()
                self.engine.run(self.controller_request('run(roll)\nrun(roll)', setup))
                ids = ('song::function::roll1', 'song::function::roll2')
                def values():
                    output = [e for e in self.events if e['type'] == 'output' and e.get('partId') in ids
                              and e['text'].strip().isdigit()]
                    return {part_id: next((int(e['text']) for e in output if e['partId'] == part_id), None)
                            for part_id in ids}
                self.until(lambda: all(value is not None for value in values().values()))
                first, second = values().values()
                self.assertNotEqual(first, second)
                self.engine.stop_all()

    def test_run_keeps_explicitly_seeded_random_objects_deterministic(self):
        setup = ('from random import Random\n'
                 'generator = Random(42)\n'
                 'def roll():\n    print(generator.randint(0, 2**128 - 1))\n    wait(8)')
        self.engine.run(self.controller_request('run(roll)\nrun(roll)', setup))
        ids = ('song::function::roll1', 'song::function::roll2')
        def values():
            output = [e for e in self.events if e['type'] == 'output' and e.get('partId') in ids
                      and e['text'].strip().isdigit()]
            return {part_id: next((int(e['text']) for e in output if e['partId'] == part_id), None)
                    for part_id in ids}
        self.until(lambda: all(value is not None for value in values().values()))
        first, second = values().values()
        self.assertEqual(first, second)

    def test_run_rejects_setup_and_skips_when_at_capacity(self):
        request = self.controller_request('pass', setup='def notes():\n    wait(1)\nrun(notes)')
        self.engine.run(request)
        self.until(lambda: self.engine.parts['song::conductor'].error is not None)
        self.assertIn('not setup', self.engine.parts['song::conductor'].error['message'])
        self.assertEqual(set(self.engine.parts), {'song::conductor'})
        self.events.clear()
        request = self.controller_request('name = run(notes)\nprint("skipped", name)\npiano(72, .5, .1)',
                                          setup='def notes():\n    wait(1)')
        with patch('pyChanga.engine.MAX_PARTS', 1):
            self.engine.run(request)
            self.until(lambda: self.engine.parts['song::conductor'].state == 'finished')
        self.assertEqual(set(self.engine.parts), {'song::conductor'})
        warnings = [event for event in self.events if event['type'] == 'warning']
        self.assertEqual(len(warnings), 1)
        self.assertIn('At most 1 musical parts', warnings[0]['message'])
        self.assertIn('skipped run(notes)', warnings[0]['message'])
        self.assertEqual(''.join(event['text'] for event in self.events if event['type'] == 'output'), 'skipped None\n')
        self.assertTrue(any(e['type'] == 'on' and e['pitch'] == 72 for e in self.backend.events))
        self.assertFalse(any(event['type'] == 'error' for event in self.events))

    def test_renamed_marker_starts_new_part_without_stopping_old(self):
        old = self.run_part('while True:\n    piano(60, .5, .25)', 'old')
        self.until(lambda: self.engine.parts[old['partId']].current is not None)
        new = self.run_part('while True:\n    piano(72, .5, .25)', 'new')
        self.until(lambda: self.engine.parts[new['partId']].current is not None)
        self.assertEqual(self.engine.parts[old['partId']].current.identity, old['revision'])
        self.assertEqual(self.engine.parts[new['partId']].current.identity, new['revision'])


if __name__ == '__main__':
    unittest.main()
