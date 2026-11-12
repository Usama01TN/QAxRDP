# -*- coding: utf-8 -*-
"""
Qt Designer launcher for the QAxRDP plugins: finds a Qt Designer matching the Qt binding (pyside6-designer,
pyqt5-tools / pyqt6-tools designer, or a system "designer") and starts it with the plugin directory registered in
PYQTDESIGNERPATH (PyQt) and PYSIDE_DESIGNER_PLUGINS (PySide6).
This module does not import Qt, so it can prepare the environment before any binding is loaded.
"""
from os.path import dirname, abspath, join, isfile
from sys import executable, platform
from os import environ, pathsep
from subprocess import Popen

#: Bindings whose Qt Designer can load Python plugins, in order of preference.
DESIGNER_APIS = ('pyqt5', 'pyqt6', 'pyside6', 'pyqt4')  # type: tuple[str]
#: Commands tried for each binding: executable name followed by its arguments.
DESIGNER_COMMANDS = {
    'pyside6': (('pyside6-designer',),),
    'pyqt6': (('pyqt6-tools', 'designer'), ('designer-qt6',), ('designer',)),
    'pyqt5': (('pyqt5-tools', 'designer'), ('qt5-tools', 'designer'), ('designer-qt5',), ('designer',)),
    'pyqt4': (('designer-qt4',), ('designer',)),
}  # type: dict[str, tuple[tuple[str]]]
INSTALL_HINTS = {
    'pyside6': 'pip install PySide6 (it ships pyside6-designer with Python plugin support).',
    'pyqt6': 'pip install pyqt6-tools where available, or install Qt Designer with the PyQt6 Designer plugin.',
    'pyqt5': 'pip install pyqt5-tools where available for your Python, or install Qt Designer with the PyQt5 '
             'Designer plugin from your distribution.',
    'pyqt4': 'install Qt 4 Designer with the PyQt4 Designer plugin.',
}  # type: dict[str, str]
ENVIRONMENT_VARIABLES = ('PYQTDESIGNERPATH', 'PYSIDE_DESIGNER_PLUGINS')  # type: tuple[str]


def pluginDirectory():
    """
    :return: (str | unicode | QString) Directory holding qaxrdpplugin.py (PyQt) and registerqaxrdp.py (PySide6).
    """
    return dirname(abspath(__file__))


def packageRoot():
    """
    :return: (str | unicode | QString) Directory containing the QAxRDP package (added to PYTHONPATH for src checkouts).
    """
    return dirname(dirname(pluginDirectory()))


def which(name):
    """
    Finds an executable next to the running Python first (virtual environments), then on PATH.
    :param name: str | unicode | QString
    :return: str | None
    """
    suffixes = ('.exe', '.bat', '.cmd', '') if platform.startswith('win') else ('',)  # type: tuple[str]
    folders = [dirname(executable), join(dirname(executable), 'Scripts')] + environ.get(
        'PATH', '').split(pathsep)  # type: list[str]
    for folder in folders:
        for suffix in suffixes:
            candidate = join(folder, name + suffix)  # type: str
            if folder and isfile(candidate):
                return candidate
    return None


def selectApi(api=None):
    """
    :param api: (str | unicode | QString | None) pyqt5, pyqt6, pyside6 or pyqt4; None: QT_API,
        else the first installed binding whose Designer supports Python plugins.
    :return: (str | unicode | QString | None) Lower case API name.
    """
    api = (api or environ.get('QT_API') or '').lower()  # type: str
    if api:
        return api
    try:
        from ManyQt import availableapi
        installed = [name.lower() for name in availableapi()]  # type: list[str]
    except:
        installed = []  # type: list[str]
    for candidate in DESIGNER_APIS:
        if candidate in installed:
            return candidate
    return None


def findDesigner(api=None):
    """
    :param api: str | None
    :return: (list[str | unicode | QString] | QStringList | None) Command line starting Qt Designer for the binding.
    """
    for command in DESIGNER_COMMANDS.get(selectApi(api) or '', ()):
        path = which(command[0])  # type: str | None
        if path:
            return [path] + list(command[1:])
    return None


def designerEnvironment(api=None, base=None):
    """
    :param api: str | None
    :param base: (dict | None) Environment to extend, os.environ when None.
    :return: (dict[str | unicode | QString, str | unicode | QString]) Environment registering the plugins.
    """
    env = dict(environ if base is None else base)  # type: dict[str, str]
    for name in ENVIRONMENT_VARIABLES:
        env[name] = pathsep.join([pluginDirectory()] + [p for p in env.get(name, '').split(pathsep) if p])
    env['PYTHONPATH'] = pathsep.join([packageRoot()] + [p for p in env.get('PYTHONPATH', '').split(pathsep) if p])
    api = selectApi(api)  # type: str | None
    if api:
        env['QT_API'] = api
    return env


def environmentScript(api=None):
    """
    :param api: str | None
    :return: (str | unicode | QString) Shell commands registering the plugins (cmd on Windows, sh elsewhere).
    """
    env = designerEnvironment(api, {})  # type: dict[str, str]
    form = 'set {}={}' if platform.startswith('win') else 'export {}="{}"'  # type: str
    return '\n'.join(form.format(name, env[name]) for name in ENVIRONMENT_VARIABLES + ('PYTHONPATH', 'QT_API')
                     if name in env)


def launchDesigner(files=(), api=None):
    """
    Starts Qt Designer with the QAxRDP plugins.
    :param files: (list[str | unicode | QString] | QStringList) .ui files to open.
    :param api: str | None
    :return: subprocess.Popen
    :raise RuntimeError: When no suitable Qt Designer is found (the message says how to install one).
    """
    api = selectApi(api)  # type: str | None
    command = findDesigner(api)  # type: list[str] | None
    if command is None:
        raise RuntimeError('No Qt Designer found for {}: {}'.format(
            api or 'any installed Qt binding', INSTALL_HINTS.get(api, INSTALL_HINTS['pyside6'])))
    return Popen(command + list(files), env=designerEnvironment(api))
