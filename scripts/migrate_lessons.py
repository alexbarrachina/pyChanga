"""Generate teaching copies of fork-based lessons. Originals stay untouched.

Only selected, syntactically complete concurrency examples are transformed.
General lesson modernization is deliberately not a blind AST rewrite.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = [
    '4 functions/4 forking functions.py',
    '5 list operations/1 EXERCISE remix with slices.py',
    '5 list operations/4 slicing lists intervals.py',
    '5 list operations/5 nectar.py',
    '5 list operations/5b nectar2.py',
    '5 list operations/drumSeq & choice.py',
]


def migrate(relative):
    original = ROOT / 'curs' / relative
    tree = ast.parse(original.read_text())
    setup, parts, main = [], [], []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign, ast.AnnAssign)):
            # The built-in drumSeq replaces the local E-mu-specific implementation.
            if isinstance(node, ast.FunctionDef) and node.name == 'drumSeq':
                continue
            setup.append(ast.unparse(node))
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            call = node.value
            name = call.func.id
            if name == 'fork':
                if len(call.args) != 1 or call.keywords:
                    raise ValueError(f'Needs a manual migration: {relative}')
                label = ast.unparse(call.args[0])
                parts.append((label, label + '()'))
            elif name in ('wait_for_children_to_finish', 'wait_forever'):
                continue
            elif name.startswith('set_') or name == 'tempo':
                setup.append(ast.unparse(node))
            else:
                main.append(ast.unparse(node))
        else:
            main.append(ast.unparse(node))
    if main:
        parts.append(('main_voice', '\n\n'.join(main)))
    target = ROOT / 'curs' / 'live' / relative.replace('forking functions', 'functions and parts')
    target.parent.mkdir(parents=True, exist_ok=True)
    header = f'# Adapted from curs/{relative}\n# Run the named sections independently; re-run a section to replace its part.\n'
    target.write_text(header + '# %% setup\n' + '\n\n'.join(setup) + '\n\n' +
                      '\n\n'.join(f'# %% {name}\n{body}' for name, body in parts) + '\n')


if __name__ == '__main__':
    for lesson in LESSONS:
        migrate(lesson)
    print(f'Created {len(LESSONS)} migrated lessons under curs/live')
