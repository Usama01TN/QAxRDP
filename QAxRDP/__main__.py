# coding=utf-8
"""
Test runner used by the release workflow:
    python -m tests [-v | -q]
Runs the whole suite, then ends the process right away with the result (0 = success, 1 = failure). The test
process creates and releases many ActiveX controls without the usual application life cycle, and tearing that state
down at interpreter exit crashed on Windows although every test had passed. Widget deletion is tested by the tests
themselves (deleteNow()), and the shutdown of a real application by .github/scripts/shutdowncheck.py.
"""
from unittest import TestLoader, TextTestRunner
from sys import argv, stdout, stderr, path
from os.path import dirname, abspath
from os import _exit

HERE = dirname(abspath(__file__))  # type: str
ROOT = dirname(HERE)  # type: str
if ROOT not in path:
    path.insert(0, ROOT)


def main(args):
    """
    :param args: (list[str]) Command line arguments.
    :return: (int) 0 if every test passed, 1 otherwise.
    """
    verbosity = 2 if '-v' in args else 0 if '-q' in args else 1  # type: int
    suite = TestLoader().discover(start_dir=HERE, pattern='test*.py', top_level_dir=ROOT)
    result = TextTestRunner(verbosity=verbosity).run(suite)  # type: TextTestRunner
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    code = main(argv[1:])  # type: int
    stdout.flush()
    stderr.flush()
    _exit(code)
