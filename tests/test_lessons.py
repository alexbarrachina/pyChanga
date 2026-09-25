import pathlib
import random
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pyChanga_package'))
from pyChanga import api
from pyChanga.sections import execution, parse_document


class EnoughMusic(Exception):
    pass


class BoundedRuntime:
    def __init__(self):
        self.steps = 0
    def advance(self):
        self.steps += 1
        if self.steps >= 24:
            raise EnoughMusic()
    def note(self, *args):
        self.advance()
    def wait(self, beats):
        self.advance()
    def tempo(self, bpm):
        pass
    def run(self, function, args, kwargs):
        function(*args, **kwargs)
        return function.__name__ + '1'


class LessonTests(unittest.TestCase):
    def test_examples_and_migrated_parts_execute_with_new_api(self):
        maintained_examples = [
            '01_simple_arpeggio.py',
            '02_sequence_blocking.py',
            '03_conditions_and_drums.py',
            '04_slicing_from_a_list.py',
            '05_zip_the_simsons.py',
        ]
        course_lessons = [
            '4 functions/4 functions and parts.py',
            '5 list operations/1 EXERCISE remix with slices.py',
            '5 list operations/4 slicing lists intervals.py',
            '5 list operations/5 nectar.py',
            '5 list operations/5b nectar2.py',
            '5 list operations/drumSeq & choice.py',
        ]
        # Name the maintained fixtures explicitly: missing lessons must fail, and
        # personal sketches in examples/ should not silently become test inputs.
        paths = [ROOT / 'examples' / name for name in maintained_examples]
        paths += [ROOT / 'curs' / name for name in course_lessons]
        for path in paths:
            source = path.read_text()
            document = parse_document(source)
            for part in document.parts:
                with self.subTest(file=path.name, part=part.name):
                    random.seed(123)
                    api._bind(BoundedRuntime())
                    namespace = {}
                    try:
                        _, _, body = execution(source, str(path), name=part.name)
                        exec(document.setup, namespace)
                        exec(body, namespace)
                    except EnoughMusic:
                        pass
                    finally:
                        api._bind(None)


if __name__ == '__main__':
    unittest.main()
