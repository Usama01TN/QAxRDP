# -*- coding: utf-8 -*-
"""
Release helper used by .github/workflows/release.yml (standard library only, no Qt).
    python .github/scripts/release.py version              print the validated version of QAxRDP/version.py
    python .github/scripts/release.py notes <version>      print the CHANGELOG.md section of <version>
    python .github/scripts/release.py check-dist <version> <dist_dir>
                                                           check that dist_dir holds exactly the sdist and wheel
    python .github/scripts/release.py check-install <version>
                                                           check the installed distribution (metadata, commands,
                                                           package data) without importing Qt
Every command exits with status 1 and a GitHub "::error::" annotation when something is wrong.
"""
from os.path import abspath, dirname, join, isdir, isfile
from re import compile as regex, escape, search, M
from sys import argv, exit, stdout
from os import listdir
from io import open

ROOT = dirname(dirname(dirname(abspath(__file__))))  # type: str
#: Canonical public PEP 440 versions (what setuptools writes in file names): 2.1.0, 2.1.0rc1, 2.1.0.post1...
VERSION_PATTERN = regex(r'^(0|[1-9]\d*)(\.(0|[1-9]\d*))*((a|b|rc)(0|[1-9]\d*))?(\.post(0|[1-9]\d*))?(\.dev(0|[1-9]\d*))?$')
PRERELEASE_PATTERN = regex(r'(a|b|rc|\.dev)\d+')
DISTRIBUTION = 'qaxrdp'  # type: str  # Normalized project name used in distribution file names.
PACKAGE_DATA = ('images/logo.png', 'designer/images/remotedesktopwidget.png', 'designer/images/connectionbar.png',
                'designer/images/statusdot.png', 'designer/qaxrdpplugin.py', 'designer/registerqaxrdp.py')
COMMANDS = ('qaxrdp', 'qaxrdp-designer')  # type: tuple[str]


def fail(message):
    """
    :param message: str
    :return:
    """
    print('::error::{}'.format(message))
    exit(1)


def read(*parts):
    """
    :param parts: str
    :return: str
    """
    with open(join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


def version():
    """
    :return: (str) Version of QAxRDP/version.py, validated.
    """
    match = search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", read('QAxRDP', 'version.py'), M)
    if match is None:
        fail('__version__ not found in QAxRDP/version.py')
    value = match.group(1)  # type: str
    if not VERSION_PATTERN.match(value):
        fail('Version "{}" is not a canonical PEP 440 version (e.g. 2.1.0, 2.2.0rc1)'.format(value))
    return value


def isPrerelease(value):
    """
    :param value: str
    :return: bool
    """
    return PRERELEASE_PATTERN.search(value) is not None


def notes(value):
    """
    :param value: (str) Version.
    :return: (str) Body of the "## <version>" section of CHANGELOG.md (headings may end with ":").
    """
    lines = read('CHANGELOG.md').replace('\r\n', '\n').split('\n')  # type: list[str]
    header = regex(r'^##\s+\[?v?{}\]?(?=[\s:]|$)'.format(escape(value)))
    for start, line in enumerate(lines):
        if header.match(line):
            break
    else:
        fail('CHANGELOG.md has no "## {}" section: describe the release before publishing it'.format(value))
    body = []  # type: list[str]
    for line in lines[start + 1:]:
        if line.startswith('## '):
            break
        body.append(line)
    text = '\n'.join(body).strip()  # type: str
    if not text:
        fail('The "## {}" section of CHANGELOG.md is empty'.format(value))
    return text


def checkFiles():
    """
    In CI the checkout only holds committed files: a package data file missing here was never committed.
    :return:
    """
    missing = [name for name in PACKAGE_DATA if not isfile(join(ROOT, 'QAxRDP', *name.split('/')))]
    if missing:
        fail('Not in the repository: {}. Commit them (are they excluded by .gitignore?)'.format(
            ', '.join('QAxRDP/' + name for name in missing)))
    print('Package data files OK: {}'.format(len(PACKAGE_DATA)))


def checkDist(value, folder):
    """
    :param value: (str) Version.
    :param folder: (str) Directory holding the built distributions.
    :return:
    """
    if not isdir(folder):
        fail('No distribution directory: {}'.format(folder))
    expected = {'{}-{}.tar.gz'.format(DISTRIBUTION, value), '{}-{}-py3-none-any.whl'.format(DISTRIBUTION, value)}
    found = set(listdir(folder))  # type: set[str]
    if found != expected:
        fail('Expected exactly {} in {}, found {}'.format(sorted(expected), folder, sorted(found)))
    print('Distributions OK: {}'.format(', '.join(sorted(found))))


def checkInstall(value):
    """
    Checks the installed distribution without importing QAxRDP (which would need a Qt binding).
    :param value: (str) Version.
    :return:
    """
    from importlib.metadata import distribution, PackageNotFoundError
    from importlib.util import find_spec
    from shutil import which

    try:
        dist = distribution('QAxRDP')
    except PackageNotFoundError:
        fail('QAxRDP is not installed')
    if dist.version != value:
        fail('Installed version {} != {}'.format(dist.version, value))
    spec = find_spec('QAxRDP')
    if spec is None or not spec.submodule_search_locations:
        fail('The QAxRDP package cannot be found')
    package = list(spec.submodule_search_locations)[0]  # type: str
    if ROOT in abspath(package):
        fail('QAxRDP is imported from the source tree ({}), not from the installed wheel'.format(package))
    missing = [name for name in PACKAGE_DATA if not isfile(join(package, *name.split('/')))]
    if missing:
        fail('Files missing from the wheel: {}'.format(', '.join(missing)))
    absent = [name for name in COMMANDS if which(name) is None]
    if absent:
        fail('Commands not installed: {}'.format(', '.join(absent)))
    print('Installed QAxRDP {} OK: package data and commands {} present'.format(value, ', '.join(COMMANDS)))


def main(args):
    """
    :param args: (list[str]) Command line arguments without the program name.
    :return: int
    """
    if not args:
        fail('Usage: release.py version | notes <version> | check-dist <version> <dir> | check-install <version>')
    command, rest = args[0], args[1:]
    if command == 'version':
        stdout.write(version() + '\n')
    elif command == 'prerelease':
        stdout.write(('true' if isPrerelease(rest[0]) else 'false') + '\n')
    elif command == 'notes':
        stdout.write(notes(rest[0]) + '\n')
    elif command == 'check-files':
        checkFiles()
    elif command == 'check-dist':
        checkDist(rest[0], rest[1])
    elif command == 'check-install':
        checkInstall(rest[0])
    else:
        fail('Unknown command: {}'.format(command))
    return 0


if __name__ == '__main__':
    exit(main(argv[1:]))
