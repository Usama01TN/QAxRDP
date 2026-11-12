#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script of QAxRDP.
    pip install .                 # QAxRDP + ManyQt (install a Qt binding yourself, or use an extra below)
    pip install .[pyqt5]          # + PyQt5 (its Windows wheels ship the QAxContainer module)
    pip install .[pyside6]        # + PySide6
    pip install .[designer]       # + PySide6, whose pyside6-designer loads the QAxRDP Designer plugins
"""
from setuptools import setup, find_packages
from os.path import abspath, dirname, join
from re import search, sub, M
from os import environ
from io import open

HERE = abspath(dirname(__file__))  # type: str


def read(*parts):
    """
    :param parts: str | unicode | QString
    :return: str | unicode | QString
    """
    with open(join(HERE, *parts), encoding='utf-8') as f:
        return f.read()


def meta(name):
    """
    Reads a dunder value of QAxRDP/version.py without importing the package (which would import Qt).
    :param name: (str | unicode | QString) e.g. 'version'.
    :return: str | unicode | QString
    """
    match = search(r"^__{}__\s*=\s*['\"]([^'\"]*)['\"]".format(name), read('QAxRDP', 'version.py'), M)
    if match is None:
        raise RuntimeError('__{}__ not found in QAxRDP/version.py'.format(name))
    return match.group(1)


def repository():
    """
    :return: (str | unicode | QString | None) "owner/name" of the GitHub repository when built by GitHub Actions.
    """
    return environ.get('GITHUB_REPOSITORY') or None


def longDescription():
    """
    README.md for PyPI. Inside GitHub Actions, relative links and images are made absolute (pinned to the built
    commit), because PyPI cannot resolve paths relative to the repository.
    :return: str | unicode | QString
    """
    text = read('README.md')  # type: str
    repo, sha = repository(), environ.get('GITHUB_SHA')
    if not (repo and sha):
        return text
    raw = 'https://raw.githubusercontent.com/{}/{}/'.format(repo, sha)  # type: str
    blob = 'https://github.com/{}/blob/{}/'.format(repo, sha)  # type: str

    def absolute(match):
        """
        :param match: re.Match
        :return: str | unicode | QString
        """
        prefix, target = match.group(1), match.group(2)
        if target.startswith(('http://', 'https://', '#', 'mailto:')):
            return match.group(0)
        isImage = prefix.startswith('src') or target.lower().endswith(('.png', '.svg', '.jpg', '.gif'))
        return prefix + (raw if isImage else blob) + target

    return sub(r'(src="|\]\()([^)"\s]+)', absolute, text)


def projectUrls():
    """
    :return: (dict[str, str]) Links shown on PyPI (only known when built by GitHub Actions).
    """
    repo = repository()  # type: str | None
    if not repo:
        return {}
    home = 'https://github.com/{}'.format(repo)  # type: str
    return {'Source': home, 'Issues': home + '/issues', 'Releases': home + '/releases',
            'Changelog': home + '/blob/{}/CHANGELOG.md'.format(environ.get('GITHUB_SHA', 'HEAD'))}


setup(
    name='QAxRDP',
    version=meta('version'),
    description='Microsoft Remote Desktop (RDP) client ActiveX control as a Qt widget, for PyQt/PySide through ManyQt.',
    long_description=longDescription(),
    long_description_content_type='text/markdown',
    url=projectUrls().get('Source'),
    project_urls=projectUrls(),
    author=meta('author'),
    author_email=meta('email'),
    license_expression='GPL-3.0-only',
    keywords=['rdp', 'remote desktop', 'mstsc', 'MsTscAx', 'activex', 'QAxWidget', 'QAxContainer', 'qt', 'pyqt',
              'pyside', 'ManyQt', 'terminal services', 'qt designer', 'designer plugin'],
    packages=find_packages(exclude=('tests', 'tests.*', 'tools', 'tools.*')),
    include_package_data=True,
    package_data={'QAxRDP.images': ['*.png'], 'QAxRDP.designer.images': ['*.png']},
    zip_safe=False,
    python_requires='>=2.7',
    install_requires=['ManyQt'],
    extras_require={
        'pyqt5': ['PyQt5>=5.9'],
        'pyqt6': ['PyQt6'],
        'pyside2': ['PySide2'],
        'pyside6': ['PySide6'],
        'designer': ['PySide6'],
    },
    entry_points={
        'gui_scripts': ['qaxrdp = QAxRDP.main:main'],
        'console_scripts': ['qaxrdp-designer = QAxRDP.designer.main:main'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Widget Sets',
        'Topic :: System :: Networking',
    ],
)
