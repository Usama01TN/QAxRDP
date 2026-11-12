# coding=utf-8
"""
Shared QApplication for the tests (offscreen platform except on Windows, where ActiveX needs a real desktop).
"""
from os.path import dirname, abspath
from os import environ, name
from sys import path

ROOT = dirname(dirname(abspath(__file__)))  # type: str
if ROOT not in path:
    path.insert(0, ROOT)
if name != 'nt':
    environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
_APPLICATION = []  # type: list[QApplication]  # Keeps the application alive for the whole test run.


def application():
    """
    :return: QApplication
    """
    from ManyQt.QtWidgets import QApplication
    if not _APPLICATION:
        _APPLICATION.append(QApplication.instance() or QApplication(['qaxrdp-tests']))
    return _APPLICATION[0]


def processEvents(ms=0):
    """
    Runs the event loop for ms milliseconds.
    :param ms: int
    :return:
    """
    from ManyQt.QtCore import QEventLoop, QTimer
    loop = QEventLoop()  # type: QEventLoop
    QTimer.singleShot(ms, loop.quit)
    (getattr(loop, 'exec', None) or loop.exec_)()
